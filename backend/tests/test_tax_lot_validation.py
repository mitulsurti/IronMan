from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from ironman.ledger.models import Account, AccountType, EventType, Instrument, InstrumentType, LedgerEvent, LedgerLeg, LegDirection, LegType
from ironman.ledger.reconstruction import LedgerInvariantError
from ironman.ledger.service import validate_tax_lot_allocations


def test_tax_lot_validation_requires_sell_and_matching_acquisition(sqlite_session):
    account = Account(name="a", account_type=AccountType.BANK, created_at=datetime.now(timezone.utc))
    instrument = Instrument(name="i", instrument_type=InstrumentType.EQUITY, native_currency="INR", created_at=datetime.now(timezone.utc))
    sqlite_session.add_all([account, instrument])
    sqlite_session.flush()
    acquisition = LedgerEvent(id=uuid4(), event_type=EventType.BUY, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=1, source="t", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    acquisition.legs = [LedgerLeg(leg_type=LegType.SECURITY, direction=LegDirection.IN, account_id=account.id, instrument_id=instrument.id, quantity=Decimal("2"), cost_basis=Decimal("100"))]
    disposal = LedgerEvent(id=uuid4(), event_type=EventType.SELL, effective_at=datetime.now(timezone.utc), financial_date=date.today(), timezone="UTC", sequence=2, source="t", actor_id="owner", actor_type="human", created_at=datetime.now(timezone.utc))
    disposal.legs = [LedgerLeg(leg_type=LegType.SECURITY, direction=LegDirection.OUT, account_id=account.id, instrument_id=instrument.id, quantity=Decimal("1"))]
    sqlite_session.add_all([acquisition, disposal])
    sqlite_session.flush()
    validate_tax_lot_allocations(sqlite_session, disposal, [{"acquisition_event_id": acquisition.id, "instrument_id": instrument.id, "account_id": account.id, "quantity": "1", "cost_basis": "50"}])
    with pytest.raises(LedgerInvariantError):
        validate_tax_lot_allocations(sqlite_session, disposal, [{"acquisition_event_id": acquisition.id, "instrument_id": instrument.id, "account_id": account.id, "quantity": "2", "cost_basis": "50"}])
