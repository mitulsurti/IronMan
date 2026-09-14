from decimal import Decimal
from uuid import uuid4

import pytest

from ironman.ledger.domain import validate_event
from ironman.ledger.models import EventType, LegType
from ironman.ledger.reconstruction import LedgerInvariantError


def test_security_and_cash_legs_require_identity_fields() -> None:
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.BUY, [{"leg_type": LegType.SECURITY, "quantity": Decimal("1")}])
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.CASH_DEPOSIT, [{"leg_type": LegType.CASH, "amount": Decimal("1")}])


def test_transfer_requires_explicit_balanced_leg_direction() -> None:
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.TRANSFER, [{"leg_type": LegType.CASH, "currency": "INR", "amount": Decimal("1")}])


def test_negative_posted_values_are_rejected() -> None:
    with pytest.raises(LedgerInvariantError):
        validate_event(EventType.CASH_DEPOSIT, [{"leg_type": LegType.CASH, "currency": "INR", "amount": Decimal("-1")}])
