from datetime import datetime, timezone
from decimal import Decimal

from ironman.ledger.models import EventType, LegDirection, LegType
from ironman.ledger.reconstruction import LedgerInvariantError


SUPPORTED_EVENT_TYPES = frozenset(EventType)


def validate_event(event_type: str, legs: list[dict], effective_at: datetime | None = None, *, correlation_id=None, correction_of_id=None) -> None:
    if event_type not in SUPPORTED_EVENT_TYPES:
        raise LedgerInvariantError(f"unsupported event type: {event_type}")
    if not legs:
        raise LedgerInvariantError("a ledger event requires at least one leg")
    if effective_at is not None and (effective_at.tzinfo is None or effective_at.utcoffset() != timezone.utc.utcoffset(effective_at)):
        raise LedgerInvariantError("effective_at must be an explicit UTC instant")
    for leg in legs:
        quantity = leg.get("quantity")
        amount = leg.get("amount")
        if quantity is not None and Decimal(quantity) < 0:
            raise LedgerInvariantError("posted quantities must be nonnegative")
        if amount is not None and Decimal(amount) < 0:
            raise LedgerInvariantError("posted amounts must be nonnegative")
        if leg["leg_type"] == LegType.SECURITY and not leg.get("instrument_id"):
            raise LedgerInvariantError("security legs require an instrument")
        if leg["leg_type"] in (LegType.CASH, LegType.FEE, LegType.TAX) and not leg.get("currency"):
            raise LedgerInvariantError("cash and charge legs require a currency")
        if event_type == EventType.TRANSFER and leg.get("direction") not in (LegDirection.IN, LegDirection.OUT):
            raise LedgerInvariantError("transfer legs require IN or OUT direction")
    security = [leg for leg in legs if leg["leg_type"] == LegType.SECURITY]
    cash = [leg for leg in legs if leg["leg_type"] == LegType.CASH]
    charges = [leg for leg in legs if leg["leg_type"] in (LegType.FEE, LegType.TAX)]
    if event_type == EventType.BUY and not (any(x.get("direction") == LegDirection.IN for x in security) and any(x.get("direction") == LegDirection.OUT for x in cash)):
        raise LedgerInvariantError("BUY requires security IN and cash OUT legs")
    if event_type == EventType.SELL and not (any(x.get("direction") == LegDirection.OUT for x in security) and any(x.get("direction") == LegDirection.IN for x in cash)):
        raise LedgerInvariantError("SELL requires security OUT and cash IN legs")
    if event_type in (EventType.CASH_DEPOSIT, EventType.DIVIDEND) and not (len(cash) == 1 and cash[0].get("direction") == LegDirection.IN):
        raise LedgerInvariantError(f"{event_type} requires one cash IN leg")
    if event_type == EventType.CASH_WITHDRAWAL and not (len(cash) == 1 and cash[0].get("direction") == LegDirection.OUT):
        raise LedgerInvariantError("CASH_WITHDRAWAL requires one cash OUT leg")
    if event_type in (EventType.FEE, EventType.TAX) and not (len(charges) == 1 and charges[0].get("direction") == LegDirection.OUT):
        raise LedgerInvariantError(f"{event_type} requires one charge OUT leg")
    if event_type in (EventType.SPLIT, EventType.BONUS) and not security:
        raise LedgerInvariantError(f"{event_type} requires security legs")
    if event_type == EventType.CORRECTION:
        if correction_of_id is None:
            raise LedgerInvariantError("CORRECTION requires correction_of_id")
        if not (security or cash or charges):
            raise LedgerInvariantError("CORRECTION requires financial legs")
    if event_type == EventType.TRANSFER:
        if correlation_id is None:
            raise LedgerInvariantError("TRANSFER requires correlation_id")
        if not security and not cash:
            raise LedgerInvariantError("TRANSFER requires cash or security legs")
        groups = {}
        for leg in security + cash:
            key = (leg["leg_type"], leg.get("instrument_id"), leg.get("currency"))
            groups.setdefault(key, {LegDirection.IN: Decimal("0"), LegDirection.OUT: Decimal("0")})
            value = leg.get("quantity") if leg["leg_type"] == LegType.SECURITY else leg.get("amount")
            groups[key][leg["direction"]] += Decimal(value or 0)
        if any(values[LegDirection.IN] <= 0 or values[LegDirection.IN] != values[LegDirection.OUT] for values in groups.values()):
            raise LedgerInvariantError("TRANSFER legs must balance by currency or instrument")
