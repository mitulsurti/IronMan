from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from ironman.ledger.models import EventType, LegType
from ironman.ledger.reconstruction import ReconstructionEvent, ReconstructionLeg, apply_events


def test_same_timestamp_boundary_is_exact():
    account = uuid4()
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first = ReconstructionEvent(uuid4(), EventType.CASH_DEPOSIT, timestamp, 1, (ReconstructionLeg(LegType.CASH, account, currency="INR", amount=Decimal("10")),))
    second = ReconstructionEvent(uuid4(), EventType.CASH_DEPOSIT, timestamp, 2, (ReconstructionLeg(LegType.CASH, account, currency="INR", amount=Decimal("20")),))
    state = apply_events([second, first], boundary=timestamp, boundary_sequence=1, boundary_event_id=first.id)
    assert state.cash[(account, "INR")] == Decimal("10")
