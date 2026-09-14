from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError

from ironman.ledger.domain import validate_event
from ironman.ledger.models import EventType, LegDirection, LegType, PortfolioStateVersion
from ironman.ledger.reconstruction import LedgerInvariantError
from ironman.ledger.service import validate_tax_lot_allocations


def leg(kind, direction, **kwargs):
    return {"leg_type": kind, "direction": direction, **kwargs}


def test_event_shapes_are_required():
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.BUY, [leg(LegType.SECURITY, LegDirection.IN, instrument_id=uuid4(), quantity=Decimal("1"))])
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.SELL, [leg(LegType.CASH, LegDirection.IN, currency="INR", amount=Decimal("1"))])
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.CASH_DEPOSIT, [leg(LegType.CASH, LegDirection.OUT, currency="INR", amount=Decimal("1"))])
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.CASH_WITHDRAWAL, [leg(LegType.CASH, LegDirection.IN, currency="INR", amount=Decimal("1"))])
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.DIVIDEND, [leg(LegType.SECURITY, LegDirection.IN, instrument_id=uuid4(), quantity=Decimal("1"))])
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.FEE, [leg(LegType.CASH, LegDirection.OUT, currency="INR", amount=Decimal("1"))])


def test_balanced_cash_and_security_transfers_require_correlation():
    a, b, instrument = uuid4(), uuid4(), uuid4()
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.TRANSFER, [leg(LegType.CASH, LegDirection.OUT, account_id=a, currency="INR", amount=Decimal("10")), leg(LegType.CASH, LegDirection.IN, account_id=b, currency="INR", amount=Decimal("10"))])
    correlation = uuid4()
    validate_event(EventType.TRANSFER, [leg(LegType.CASH, LegDirection.OUT, account_id=a, currency="INR", amount=Decimal("10")), leg(LegType.CASH, LegDirection.IN, account_id=b, currency="INR", amount=Decimal("10"))], correlation_id=correlation)
    validate_event(EventType.TRANSFER, [leg(LegType.SECURITY, LegDirection.OUT, account_id=a, instrument_id=instrument, quantity=Decimal("2")), leg(LegType.SECURITY, LegDirection.IN, account_id=b, instrument_id=instrument, quantity=Decimal("2"))], correlation_id=correlation)
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.TRANSFER, [leg(LegType.CASH, LegDirection.OUT, account_id=a, currency="INR", amount=Decimal("10")), leg(LegType.CASH, LegDirection.IN, account_id=b, currency="USD", amount=Decimal("10"))], correlation_id=correlation)


def test_correction_requires_reference_and_financial_legs():
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.CORRECTION, [leg(LegType.CASH, LegDirection.IN, currency="INR", amount=Decimal("1"))])
    validate_event(EventType.CORRECTION, [leg(LegType.CASH, LegDirection.IN, currency="INR", amount=Decimal("1"))], correction_of_id=uuid4())


def test_snapshot_bulk_update_delete_are_rejected(sqlite_session):
    snapshot = PortfolioStateVersion(ledger_boundary=datetime.now(timezone.utc), boundary_sequence=1, calculation_version="test", holdings=[], cash_balances=[], tax_lots=[], content_hash=uuid4().hex, created_at=datetime.now(timezone.utc))
    sqlite_session.add(snapshot)
    sqlite_session.commit()
    with pytest.raises(IntegrityError):
        sqlite_session.execute(update(PortfolioStateVersion).where(PortfolioStateVersion.id == snapshot.id).values(calculation_version="changed"))
        sqlite_session.commit()
    sqlite_session.rollback()
    with pytest.raises(IntegrityError):
        sqlite_session.execute(delete(PortfolioStateVersion).where(PortfolioStateVersion.id == snapshot.id))
        sqlite_session.commit()
