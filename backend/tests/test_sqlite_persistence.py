from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from ironman.ledger.models import Account, AccountType, EventType, Instrument, InstrumentType, LedgerEvent, LedgerLeg, LegDirection, LegType, PortfolioStateVersion, TaxLotAllocation
from ironman.ledger.service import DuplicateLedgerEvent, append_event, create_state_version, reconstruct_from_rows


def make_account(session):
    account = Account(name="Test", account_type=AccountType.BANK, created_at=datetime.now(timezone.utc))
    session.add(account)
    session.flush()
    return account


def test_sqlite_persists_ledger_reconstruction_and_state_version(sqlite_session):
    account = make_account(sqlite_session)
    instrument = Instrument(name="Test Equity", instrument_type=InstrumentType.EQUITY, native_currency="INR", created_at=datetime.now(timezone.utc))
    sqlite_session.add(instrument)
    sqlite_session.flush()
    deposit = LedgerEvent(id=uuid4(), event_type=EventType.CASH_DEPOSIT, effective_at=datetime(2026, 1, 1, tzinfo=timezone.utc), financial_date=date(2026, 1, 1), timezone="UTC", sequence=1, source="test", source_event_id="deposit-1", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    append_event(sqlite_session, deposit, [LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("1000"))])
    buy = LedgerEvent(id=uuid4(), event_type=EventType.BUY, effective_at=datetime(2026, 1, 2, tzinfo=timezone.utc), financial_date=date(2026, 1, 2), timezone="UTC", sequence=1, source="test", source_event_id="buy-1", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    append_event(sqlite_session, buy, [LedgerLeg(leg_type=LegType.SECURITY, direction=LegDirection.IN, account_id=account.id, instrument_id=instrument.id, quantity=Decimal("2"), cost_basis=Decimal("200")), LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.OUT, account_id=account.id, currency="INR", amount=Decimal("200"))])
    sqlite_session.commit()
    events = list(sqlite_session.scalars(select(LedgerEvent).order_by(LedgerEvent.effective_at)))
    state = reconstruct_from_rows(events)
    assert state.cash[(account.id, "INR")] == Decimal("800")
    assert state.positions[(account.id, instrument.id)].quantity == Decimal("2")
    version = create_state_version(sqlite_session, events, calculation_version="test-v1")
    sqlite_session.commit()
    assert sqlite_session.get(PortfolioStateVersion, version.id).content_hash == version.content_hash
    assert version.boundary_event_id == buy.id
    assert version.boundary_sequence == buy.sequence


def test_sqlite_enforces_foreign_keys_and_idempotency(sqlite_session):
    invalid_event = LedgerEvent(id=uuid4(), event_type=EventType.CASH_DEPOSIT, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=1, source="test", source_event_id="invalid", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    with pytest.raises(IntegrityError):
        append_event(sqlite_session, invalid_event, [LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=uuid4(), currency="INR", amount=Decimal("1"))])
    sqlite_session.rollback()
    account = make_account(sqlite_session)
    event_row = LedgerEvent(id=uuid4(), event_type=EventType.CASH_DEPOSIT, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=1, source="test", source_event_id="same", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    event_row.legs = [LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("1"))]
    append_event(sqlite_session, event_row, event_row.legs)
    with pytest.raises(DuplicateLedgerEvent):
        append_event(sqlite_session, LedgerEvent(id=uuid4(), event_type=EventType.CASH_DEPOSIT, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=2, source="test", source_event_id="same", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc)), [LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("1"))])


def test_sqlite_application_protects_posted_event_update_delete(sqlite_session):
    account = make_account(sqlite_session)
    row = LedgerEvent(id=uuid4(), event_type=EventType.CASH_DEPOSIT, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=1, source="test", source_event_id="immutable", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    append_event(sqlite_session, row, [LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("1"))])
    sqlite_session.commit()
    row.source = "changed"
    with pytest.raises(ValueError):
        sqlite_session.commit()


def test_sqlite_bulk_operations_cannot_mutate_posted_rows(sqlite_session):
    account = make_account(sqlite_session)
    row = LedgerEvent(id=uuid4(), event_type=EventType.CASH_DEPOSIT, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=1, source="test", source_event_id="bulk-immutable", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    append_event(sqlite_session, row, [LedgerLeg(leg_type=LegType.CASH, direction=LegDirection.IN, account_id=account.id, currency="INR", amount=Decimal("1"))])
    sqlite_session.commit()
    with pytest.raises(IntegrityError):
        sqlite_session.execute(update(LedgerEvent).where(LedgerEvent.id == row.id).values(source="bypass"))
        sqlite_session.commit()
    sqlite_session.rollback()
    with pytest.raises(IntegrityError):
        sqlite_session.execute(delete(LedgerEvent).where(LedgerEvent.id == row.id))
        sqlite_session.commit()
    sqlite_session.rollback()
    with pytest.raises(ValueError):
        sqlite_session.delete(row)
        sqlite_session.commit()
