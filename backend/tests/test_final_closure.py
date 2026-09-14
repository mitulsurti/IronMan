from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError

from ironman.ledger.models import Account, AccountType, EventType, Instrument, InstrumentType, LedgerEvent, LedgerLeg, LegDirection, LegType, TaxLotAllocation
from ironman.ledger.reconstruction import LedgerInvariantError
from ironman.ledger.service import append_event


def test_tax_lot_allocation_persistence_rejects_historical_quantity_and_cost_overconsumption(sqlite_session):
    account = Account(name="a", account_type=AccountType.BANK, created_at=datetime.now(timezone.utc))
    instrument = Instrument(name="i", instrument_type=InstrumentType.EQUITY, native_currency="INR", created_at=datetime.now(timezone.utc))
    sqlite_session.add_all([account, instrument])
    sqlite_session.flush()
    acquisition = LedgerEvent(id=uuid4(), event_type=EventType.BUY, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=1, source="final", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    append_event(sqlite_session, acquisition, [LedgerLeg(leg_type=LegType.SECURITY, direction=LegDirection.IN, account_id=account.id, instrument_id=instrument.id, quantity=Decimal("2"), cost_basis=Decimal("100")), LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.OUT, account_id=account.id, currency="INR", amount=Decimal("100"))])
    sqlite_session.commit()

    first = LedgerEvent(id=uuid4(), event_type=EventType.SELL, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=2, source="final", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    first_legs = [LedgerLeg(leg_type=LegType.SECURITY, direction=LegDirection.OUT, account_id=account.id, instrument_id=instrument.id, quantity=Decimal("1")), LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("60"))]
    allocation = {"acquisition_event_id": acquisition.id, "instrument_id": instrument.id, "account_id": account.id, "quantity": Decimal("1"), "cost_basis": Decimal("60")}
    append_event(sqlite_session, first, first_legs, allocations=[allocation])
    sqlite_session.commit()
    assert sqlite_session.scalar(__import__("sqlalchemy").select(__import__("sqlalchemy").func.count(TaxLotAllocation.id))) == 1

    second = LedgerEvent(id=uuid4(), event_type=EventType.SELL, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=3, source="final", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    second_legs = [LedgerLeg(leg_type=LegType.SECURITY, direction=LegDirection.OUT, account_id=account.id, instrument_id=instrument.id, quantity=Decimal("2")), LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("60"))]
    with pytest.raises(LedgerInvariantError):
        append_event(sqlite_session, second, second_legs, allocations=[{**allocation, "quantity": Decimal("2"), "cost_basis": Decimal("40")}])
    sqlite_session.rollback()
    assert sqlite_session.scalar(__import__("sqlalchemy").select(__import__("sqlalchemy").func.count(TaxLotAllocation.id))) == 1
    cost_only = LedgerEvent(id=uuid4(), event_type=EventType.SELL, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=4, source="final", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    cost_only_legs = [LedgerLeg(leg_type=LegType.SECURITY, direction=LegDirection.OUT, account_id=account.id, instrument_id=instrument.id, quantity=Decimal("1")), LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("60"))]
    with pytest.raises(LedgerInvariantError):
        append_event(sqlite_session, cost_only, cost_only_legs, allocations=[{**allocation, "quantity": Decimal("1"), "cost_basis": Decimal("41")}])


def test_posted_ledger_leg_direct_and_bulk_update_delete_are_rejected(sqlite_session):
    account = Account(name="a", account_type=AccountType.BANK, created_at=datetime.now(timezone.utc))
    sqlite_session.add(account)
    sqlite_session.flush()
    event_row = LedgerEvent(id=uuid4(), event_type=EventType.CASH_DEPOSIT, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=1, source="final", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    leg = LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("1"))
    append_event(sqlite_session, event_row, [leg])
    sqlite_session.commit()
    for operation in (
        lambda: setattr(leg, "amount", Decimal("2")),
        lambda: sqlite_session.execute(update(LedgerLeg).where(LedgerLeg.id == leg.id).values(amount=Decimal("2"))),
        lambda: sqlite_session.delete(leg),
        lambda: sqlite_session.execute(delete(LedgerLeg).where(LedgerLeg.id == leg.id)),
    ):
        sqlite_session.rollback()
        with pytest.raises((ValueError, IntegrityError)):
            operation()
            sqlite_session.commit()
