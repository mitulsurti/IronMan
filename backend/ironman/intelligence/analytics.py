from decimal import Decimal

from ironman.ledger.models import PortfolioStateVersion
from ironman.ledger.reconstruction import LedgerInvariantError


class IntelligenceGateError(ValueError):
    pass


VALUATION_CALCULATION_VERSION = "valuation-v1"


def valuation_facts(inputs: dict) -> dict:
    """Compute only transparent, same-currency valuation facts from supplied inputs."""
    price = _decimal_or_none(inputs.get("price"))
    eps = _decimal_or_none(inputs.get("eps"))
    book_value_per_share = _decimal_or_none(inputs.get("book_value_per_share"))
    enterprise_value = _decimal_or_none(inputs.get("enterprise_value"))
    ebitda = _decimal_or_none(inputs.get("ebitda"))
    free_cash_flow = _decimal_or_none(inputs.get("free_cash_flow"))
    market_cap = _decimal_or_none(inputs.get("market_cap"))
    facts = {"calculation_version": VALUATION_CALCULATION_VERSION, "currency": inputs.get("currency"), "methods": {}, "assumptions": inputs.get("assumptions", {})}
    if price is not None and eps is not None and eps > 0:
        facts["methods"]["pe"] = str(price / eps)
    if price is not None and book_value_per_share is not None and book_value_per_share > 0:
        facts["methods"]["pb"] = str(price / book_value_per_share)
    if enterprise_value is not None and ebitda is not None and ebitda > 0:
        facts["methods"]["ev_ebitda"] = str(enterprise_value / ebitda)
    if free_cash_flow is not None and market_cap is not None and market_cap > 0:
        facts["methods"]["fcf_yield"] = str(free_cash_flow / market_cap)
    facts["status"] = "PASS" if facts["methods"] else "INSUFFICIENT"
    return facts


def valuation_inputs_from_observations(observations: list) -> dict:
    """Map persisted FUNDAMENTAL observations into existing valuation input names."""
    values = {observation.values.get("field"): observation.value for observation in observations if observation.observation_type == "FUNDAMENTAL" and observation.quality == "VALID" and observation.freshness == "VALID"}
    return {key: str(value) for key, value in values.items() if value is not None}


def _decimal_or_none(value) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, float):
        raise IntelligenceGateError("valuation inputs must not be binary floats")
    return Decimal(str(value))


def load_portfolio_context(state_version: PortfolioStateVersion) -> dict:
    if not state_version.content_hash or not state_version.calculation_version:
        raise IntelligenceGateError("invalid portfolio state version")
    cash = {
        (item["account_id"], item["currency"]): Decimal(item["amount"])
        for item in state_version.cash_balances
    }
    holdings = list(state_version.holdings)
    total_by_currency: dict[str, Decimal] = {}
    for item in holdings:
        currency = item.get("currency", "")
        if currency:
            total_by_currency[currency] = total_by_currency.get(currency, Decimal("0")) + Decimal(item.get("current_value", item.get("cost_basis", "0")))
    return {
        "cash": cash,
        "holdings": holdings,
        "total_by_currency": total_by_currency,
        "total_cash": sum(cash.values(), Decimal("0")),
        "data_context": state_version.data_context,
        "policy_version": state_version.policy_version,
    }


def evaluate_opportunity(context: dict, opportunity, amount: Decimal, max_concentration: Decimal | None) -> dict:
    gates = {
        "identity": "PASS" if opportunity.instrument_id or opportunity.kind in ("CASH", "FIXED_INCOME") else "INSUFFICIENT",
        "quality": opportunity.quality_state,
        "freshness": opportunity.freshness_state,
        "evidence": "PASS" if opportunity.evidence else "INSUFFICIENT",
    }
    current_weight = Decimal(opportunity.portfolio_weight or 0)
    portfolio_total = context["total_by_currency"].get(opportunity.currency, Decimal("0")) + context["total_cash"]
    proposed_weight = current_weight + (amount / portfolio_total if portfolio_total > 0 else Decimal("1"))
    if max_concentration is not None and proposed_weight > max_concentration:
        gates["concentration"] = "BLOCKED"
    else:
        gates["concentration"] = "PASS"
    return {
        "gates": gates,
        "analytics": {
            "current_weight": str(current_weight),
            "proposed_weight": str(proposed_weight),
            "proposed_amount": str(amount),
            "quality": opportunity.analytics.get("quality"),
            "valuation": opportunity.analytics.get("valuation"),
            "return": opportunity.analytics.get("return"),
        },
    }


def gate_is_actionable(gates: dict) -> bool:
    return all(value == "PASS" for value in gates.values())
