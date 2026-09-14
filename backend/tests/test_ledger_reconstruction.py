from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from ironman.ledger.models import EventType, LegDirection, LegType
from ironman.ledger.reconstruction import (
    LedgerInvariantError,
    ReconstructionEvent,
    ReconstructionLeg,
    apply_events,
)


def event(event_type: str, *legs: ReconstructionLeg, sequence: int = 0) -> ReconstructionEvent:
    return ReconstructionEvent(uuid4(), event_type, datetime(2026, 1, 1, tzinfo=timezone.utc), sequence, tuple(legs))


def cash(account, amount, event_type=EventType.CASH_DEPOSIT, currency="INR", sequence=0):
    return ReconstructionLeg(LegType.CASH, account, currency=currency, amount=Decimal(amount), direction=None)


def test_buy_sell_and_cash_reconstruct_deterministically() -> None:
    account, instrument = uuid4(), uuid4()
    events = [
        event(EventType.CASH_DEPOSIT, cash(account, "1000"), sequence=1),
        event(
            EventType.BUY,
            ReconstructionLeg(LegType.SECURITY, account, instrument_id=instrument, quantity=Decimal("2")),
            ReconstructionLeg(LegType.CASH, account, currency="INR", amount=Decimal("200")), sequence=2,
        ),
        event(
            EventType.SELL,
            ReconstructionLeg(LegType.SECURITY, account, instrument_id=instrument, quantity=Decimal("1")),
            ReconstructionLeg(LegType.CASH, account, currency="INR", amount=Decimal("120")), sequence=3,
        ),
    ]
    state = apply_events(events)
    assert state.positions[(account, instrument)].quantity == Decimal("1")
    assert state.cash[(account, "INR")] == Decimal("920")


def test_transfer_requires_explicit_direction_and_preserves_quantity() -> None:
    source, destination, instrument = uuid4(), uuid4(), uuid4()
    state = apply_events([
        event(
            EventType.CASH_DEPOSIT,
            cash(source, "1000"),
            sequence=0,
        ),
        event(
            EventType.BUY,
            ReconstructionLeg(LegType.SECURITY, source, instrument_id=instrument, quantity=Decimal("3")),
            ReconstructionLeg(LegType.CASH, source, currency="INR", amount=Decimal("300")),
            sequence=1,
        ),
        event(
            EventType.TRANSFER,
            ReconstructionLeg(LegType.SECURITY, source, instrument_id=instrument, quantity=Decimal("3"), direction=LegDirection.OUT),
            ReconstructionLeg(LegType.SECURITY, destination, instrument_id=instrument, quantity=Decimal("3"), direction=LegDirection.IN),
            sequence=2,
        )
    ])
    assert state.positions[(source, instrument)].quantity == Decimal("0")
    assert state.positions[(destination, instrument)].quantity == Decimal("3")


def test_negative_cash_is_rejected() -> None:
    with pytest.raises(LedgerInvariantError):
        apply_events([event(EventType.CASH_WITHDRAWAL, cash(uuid4(), "1", EventType.CASH_WITHDRAWAL))])


def test_ordering_uses_timestamp_sequence_and_identity() -> None:
    account = uuid4()
    first = event(EventType.CASH_DEPOSIT, cash(account, "10"), sequence=1)
    second = event(EventType.CASH_WITHDRAWAL, cash(account, "3", EventType.CASH_WITHDRAWAL), sequence=2)
    state = apply_events([second, first])
    assert state.cash[(account, "INR")] == Decimal("7")
