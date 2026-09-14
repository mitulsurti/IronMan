from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ironman.ledger.models import LedgerEvent, LedgerLeg, PortfolioStateVersion, TaxLotAllocation
from ironman.ledger.reconstruction import ReconstructionEvent, ReconstructionLeg, apply_events


class DuplicateLedgerEvent(ValueError):
    """The source event has already been recorded."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def append_event(
    session: Session,
    event: LedgerEvent,
    legs: Iterable[LedgerLeg],
    allocations: list[dict] | None = None,
) -> LedgerEvent:
    from ironman.ledger.domain import validate_event
    event.legs = list(legs)
    validate_event(
        event.event_type,
        [
            {
                "leg_type": leg.leg_type,
                "direction": leg.direction,
                "account_id": leg.account_id,
                "instrument_id": leg.instrument_id,
                "currency": leg.currency,
                "quantity": leg.quantity,
                "amount": leg.amount,
            }
            for leg in event.legs
        ],
        event.effective_at,
        correlation_id=event.correlation_id,
        correction_of_id=event.correction_of_id,
    )
    if event.source_event_id:
        existing = session.scalar(
            select(LedgerEvent).where(
                LedgerEvent.source == event.source,
                LedgerEvent.source_event_id == event.source_event_id,
            )
        )
        if existing:
            raise DuplicateLedgerEvent(str(existing.id))
    event.created_at = event.created_at or utc_now()
    event.posted = True
    if allocations:
        validate_tax_lot_allocations(session, event, allocations)
    session.add(event)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        message = str(exc.orig).lower()
        if constraint_name == "uq_ledger_source_event" or "ledger_events.source, ledger_events.source_event_id" in message:
            raise DuplicateLedgerEvent("duplicate ledger source event") from exc
        raise
    if allocations:
        for allocation in allocations:
            session.add(
                TaxLotAllocation(
                    consumption_event_id=event.id,
                    created_at=event.created_at,
                    **allocation,
                )
            )
        session.flush()
    return event


def validate_tax_lot_allocations(session: Session, consumption_event: LedgerEvent, allocations: list[dict]) -> None:
    if not allocations:
        return
    from ironman.ledger.reconstruction import LedgerInvariantError
    if consumption_event.event_type != "SELL":
        raise LedgerInvariantError("tax-lot allocations require a SELL event")
    disposal = next((leg for leg in consumption_event.legs if leg.leg_type == "SECURITY" and leg.direction == "OUT"), None)
    if disposal is None:
        raise LedgerInvariantError("tax-lot allocations require a security disposal leg")
    allocated_quantity = Decimal("0")
    seen_acquisitions = set()
    for item in allocations:
        quantity = Decimal(item["quantity"])
        cost_basis = Decimal(item["cost_basis"])
        acquisition_id = item["acquisition_event_id"]
        if acquisition_id in seen_acquisitions:
            raise LedgerInvariantError("duplicate allocation relationship")
        seen_acquisitions.add(acquisition_id)
        acquisition = session.get(LedgerEvent, acquisition_id)
        if acquisition is None or acquisition.event_type not in ("BUY", "BONUS", "SPLIT"):
            raise LedgerInvariantError("allocation acquisition must be a valid acquisition event")
        acquisition_leg = next((leg for leg in acquisition.legs if leg.leg_type == "SECURITY" and leg.direction == "IN"), None)
        if (
            acquisition_leg is None
            or item.get("account_id") != disposal.account_id
            or item.get("instrument_id") != disposal.instrument_id
            or acquisition_leg.account_id != disposal.account_id
            or acquisition_leg.instrument_id != disposal.instrument_id
        ):
            raise LedgerInvariantError("allocation account and instrument must match disposal")
        if quantity <= 0 or quantity > (disposal.quantity or 0):
            raise LedgerInvariantError("allocation quantity is invalid")
        prior_quantity = session.scalar(
            select(func.coalesce(func.sum(TaxLotAllocation.quantity), 0)).where(
                TaxLotAllocation.acquisition_event_id == acquisition_id
            )
        ) or Decimal("0")
        prior_cost_basis = session.scalar(
            select(func.coalesce(func.sum(TaxLotAllocation.cost_basis), 0)).where(
                TaxLotAllocation.acquisition_event_id == acquisition_id
            )
        ) or Decimal("0")
        remaining_quantity = Decimal(acquisition_leg.quantity or 0) - Decimal(prior_quantity)
        remaining_cost_basis = Decimal(acquisition_leg.cost_basis or 0) - Decimal(prior_cost_basis)
        if quantity > remaining_quantity:
            raise LedgerInvariantError("allocation exceeds remaining acquisition quantity")
        if cost_basis < 0 or cost_basis > remaining_cost_basis:
            raise LedgerInvariantError("allocation cost basis is invalid")
        allocated_quantity += quantity
    if allocated_quantity > (disposal.quantity or 0):
        raise LedgerInvariantError("allocations exceed disposal quantity")


def reconstruct_from_rows(events: Iterable[LedgerEvent]):
    events = list(events)
    ordered = []
    for event in events:
        ordered.append(
            ReconstructionEvent(
                id=event.id,
                event_type=event.event_type,
                effective_at=event.effective_at,
                sequence=event.sequence,
                legs=tuple(
                    ReconstructionLeg(
                        leg_type=leg.leg_type,
                        direction=leg.direction,
                        account_id=leg.account_id,
                        instrument_id=leg.instrument_id,
                        currency=leg.currency,
                        quantity=leg.quantity,
                        amount=leg.amount,
                        cost_basis=leg.cost_basis,
                    )
                    for leg in event.legs
                ),
                lot_allocations=tuple(
                    (allocation.acquisition_event_id, allocation.quantity, allocation.cost_basis)
                    for allocation in event.lot_allocations
                ),
            )
        )
    return apply_events(ordered)


def create_state_version(
    session: Session,
    events: Iterable[LedgerEvent],
    *,
    calculation_version: str,
    policy_version: str | None = None,
    data_context: dict | None = None,
) -> PortfolioStateVersion:
    events = list(events)
    state = reconstruct_from_rows(events)
    holdings = [
        {
            "account_id": str(account_id),
            "instrument_id": str(instrument_id),
            "quantity": str(position.quantity),
            "cost_basis": str(position.cost_basis),
        }
        for (account_id, instrument_id), position in sorted(
            state.positions.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))
        )
    ]
    cash = [
        {"account_id": str(account_id), "currency": currency, "amount": str(amount)}
        for (account_id, currency), amount in sorted(state.cash.items(), key=lambda item: (str(item[0][0]), item[0][1]))
    ]
    tax_lots = [
        {"acquisition_event_id": str(lot_id), "remaining_quantity": str(quantity), "remaining_cost_basis": str(state.lot_cost_basis.get(lot_id, Decimal("0")))}
        for lot_id, quantity in sorted(state.remaining_lots.items(), key=lambda item: str(item[0]))
        if quantity > 0
    ]
    ordered = sorted(events, key=lambda event: (event.effective_at, event.sequence, event.id.hex))
    final_event = ordered[-1] if ordered else None
    boundary = final_event.effective_at if final_event else utc_now()
    payload = {
        "ledger_boundary": boundary.isoformat(),
        "boundary_sequence": final_event.sequence if final_event else 0,
        "boundary_event_id": str(final_event.id) if final_event else None,
        "holdings": holdings,
        "cash": cash,
        "tax_lots": tax_lots,
        "calculation_version": calculation_version,
        "policy_version": policy_version,
        "data_context": data_context or {},
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    version = PortfolioStateVersion(
        id=uuid4(),
        ledger_boundary=boundary,
        boundary_sequence=final_event.sequence if final_event else 0,
        boundary_event_id=final_event.id if final_event else None,
        calculation_version=calculation_version,
        policy_version=policy_version,
        data_context=data_context or {},
        holdings=holdings,
        cash_balances=cash,
        tax_lots=tax_lots,
        content_hash=digest,
        created_at=utc_now(),
    )
    session.add(version)
    return version
