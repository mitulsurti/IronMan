from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from ironman.ledger.models import Account, AccountType, EventType, LedgerEvent, LedgerLeg, LegDirection, LegType
from ironman.ledger.reconstruction import LedgerInvariantError
from ironman.ledger.service import append_event


def make_event(event_type, legs, **kwargs):
    return LedgerEvent(
        id=uuid4(), event_type=event_type, effective_at=datetime.now(timezone.utc),
        financial_date=date.today(), timezone="UTC", sequence=1, source="service-test",
        actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc), **kwargs,
        legs=legs,
    )


def test_append_event_enforces_shape_and_transfer_rules(sqlite_session):
    account = Account(name="a", account_type=AccountType.BANK, created_at=datetime.now(timezone.utc))
    sqlite_session.add(account)
    sqlite_session.flush()
    invalid = make_event(EventType.BUY, [LedgerLeg(leg_type=LegType.SECURITY, direction=LegDirection.IN, account_id=account.id, instrument_id=uuid4(), quantity=Decimal("1"))])
    with pytest.raises(LedgerInvariantError):
        append_event(sqlite_session, invalid, invalid.legs)
    transfer = make_event(EventType.TRANSFER, [LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.OUT, account_id=account.id, currency="INR", amount=Decimal("1"))])
    with pytest.raises(LedgerInvariantError):
        append_event(sqlite_session, transfer, transfer.legs)
    correction = make_event(EventType.CORRECTION, [LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("1"))])
    with pytest.raises(LedgerInvariantError):
        append_event(sqlite_session, correction, correction.legs)
