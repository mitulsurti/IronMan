from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ironman.ledger.models import EventType, LegDirection, LegType


class LedgerInvariantError(ValueError):
    pass


@dataclass
class Position:
    quantity: Decimal = Decimal("0")
    cost_basis: Decimal = Decimal("0")


@dataclass
class PortfolioState:
    cash: dict[tuple[UUID, str], Decimal] = field(default_factory=dict)
    positions: dict[tuple[UUID, UUID], Position] = field(default_factory=dict)
    remaining_lots: dict[UUID, Decimal] = field(default_factory=dict)
    lot_cost_basis: dict[UUID, Decimal] = field(default_factory=dict)


@dataclass(frozen=True)
class ReconstructionLeg:
    leg_type: str
    account_id: UUID
    instrument_id: UUID | None = None
    currency: str | None = None
    quantity: Decimal | None = None
    amount: Decimal | None = None
    cost_basis: Decimal | None = None
    direction: str | None = None


@dataclass(frozen=True)
class ReconstructionEvent:
    id: UUID
    event_type: str
    effective_at: datetime
    sequence: int
    legs: tuple[ReconstructionLeg, ...]
    lot_allocations: tuple[tuple[UUID, Decimal, Decimal], ...] = ()


def ordered_events(events: list[ReconstructionEvent]) -> list[ReconstructionEvent]:
    return sorted(events, key=lambda event: (event.effective_at, event.sequence, event.id.hex))


def apply_events(
    events: list[ReconstructionEvent],
    boundary: datetime | None = None,
    boundary_sequence: int | None = None,
    boundary_event_id: UUID | None = None,
) -> PortfolioState:
    state = PortfolioState()
    for event in ordered_events(events):
        if boundary is not None:
            event_key = (event.effective_at, event.sequence, event.id.hex)
            boundary_key = (boundary, boundary_sequence or 0, boundary_event_id.hex if boundary_event_id else "z" * 32)
            if event_key > boundary_key:
                continue
        for leg in event.legs:
            amount = leg.amount or Decimal("0")
            quantity = leg.quantity or Decimal("0")
            if leg.leg_type == LegType.CASH:
                if not leg.currency:
                    raise LedgerInvariantError("cash leg requires currency")
                key = (leg.account_id, leg.currency)
                sign = _signed_direction(event.event_type, leg.direction, LegType.CASH)
                state.cash[key] = state.cash.get(key, Decimal("0")) + sign * amount
                if state.cash[key] < 0:
                    raise LedgerInvariantError("cash balance cannot become negative")
            elif leg.leg_type == LegType.SECURITY:
                if leg.instrument_id is None:
                    raise LedgerInvariantError("security leg requires instrument")
                key = (leg.account_id, leg.instrument_id)
                position = state.positions.setdefault(key, Position())
                sign = _signed_direction(event.event_type, leg.direction, LegType.SECURITY)
                position.quantity += sign * quantity
                position.cost_basis += sign * (leg.cost_basis or Decimal("0"))
                if event.event_type in (EventType.BUY, EventType.BONUS, EventType.SPLIT) and quantity > 0:
                    state.remaining_lots[event.id] = state.remaining_lots.get(event.id, Decimal("0")) + quantity
                    state.lot_cost_basis[event.id] = state.lot_cost_basis.get(event.id, Decimal("0")) + (leg.cost_basis or Decimal("0"))
                if position.quantity < 0:
                    raise LedgerInvariantError("security quantity cannot become negative")
            elif leg.leg_type in (LegType.FEE, LegType.TAX):
                if not leg.currency:
                    raise LedgerInvariantError("charge leg requires currency")
                key = (leg.account_id, leg.currency)
                state.cash[key] = state.cash.get(key, Decimal("0")) - abs(amount)
                if state.cash[key] < 0:
                    raise LedgerInvariantError("cash balance cannot become negative")
        for acquisition_id, quantity, cost_basis in event.lot_allocations:
            if quantity <= 0 or cost_basis < 0:
                raise LedgerInvariantError("tax-lot allocation values must be positive")
            remaining = state.remaining_lots.get(acquisition_id, Decimal("0"))
            if quantity > remaining:
                raise LedgerInvariantError("tax-lot allocation exceeds remaining quantity")
            state.remaining_lots[acquisition_id] = remaining - quantity
            state.lot_cost_basis[acquisition_id] = state.lot_cost_basis.get(acquisition_id, Decimal("0")) - cost_basis
    return state


def _signed_direction(event_type: str, direction: str | None, leg_type: str) -> Decimal:
    if event_type == EventType.BUY:
        return Decimal("1") if leg_type == LegType.SECURITY else Decimal("-1")
    if event_type == EventType.SELL:
        return Decimal("-1") if leg_type == LegType.SECURITY else Decimal("1")
    if event_type in (EventType.CASH_DEPOSIT, EventType.DIVIDEND, EventType.BONUS, EventType.SPLIT):
        return Decimal("1")
    if event_type == EventType.CASH_WITHDRAWAL:
        return Decimal("-1")
    if event_type == EventType.TRANSFER:
        if direction == LegDirection.IN:
            return Decimal("1")
        if direction == LegDirection.OUT:
            return Decimal("-1")
        raise LedgerInvariantError("transfer leg requires direction")
    if event_type in (EventType.FEE, EventType.TAX):
        return Decimal("-1")
    if event_type == EventType.CORRECTION:
        if direction == LegDirection.IN:
            return Decimal("1")
        if direction == LegDirection.OUT:
            return Decimal("-1")
    raise LedgerInvariantError(f"unsupported event/leg semantics: {event_type}/{leg_type}")
