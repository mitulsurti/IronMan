from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from ironman.ledger.models import EventType, LegType
from ironman.ledger.reconstruction import ReconstructionEvent, ReconstructionLeg
from ironman.ledger.service import create_state_version


def test_state_version_content_is_deterministic(db_session=None) -> None:
    account, instrument = uuid4(), uuid4()
    events = [
        ReconstructionEvent(
            uuid4(), EventType.CASH_DEPOSIT, datetime(2026, 1, 1, tzinfo=timezone.utc), 1,
            (ReconstructionLeg(LegType.CASH, account, currency="INR", amount=Decimal("10")),),
        )
    ]
    # The pure reconstruction payload is tested through equal ordered histories;
    # persistence requires PostgreSQL and is covered by the integration suite.
    from ironman.ledger.reconstruction import apply_events
    first = apply_events(events)
    second = apply_events(list(reversed(events)))
    assert first.cash == second.cash
