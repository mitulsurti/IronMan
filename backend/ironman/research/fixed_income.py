"""Bounded fixed-income comparison over application-supplied deterministic facts."""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from ironman.ai.gateway import ModelGateway
from ironman.research.agent import ResearchValidationError
from ironman.research.evidence import EvidenceBoundaryError, validate_claim_references, validate_evidence_items
from ironman.research.schemas import ResearchRequest, ResearchResult


class FixedIncomeComparisonError(ValueError):
    pass


def deterministic_fixed_income_facts(instrument: dict, alternative: dict | None = None) -> dict:
    """Validate supplied fixed-income terms and calculate only transparent cash-flow totals."""
    required = {"instrument_id", "instrument_type", "currency", "maturity_date", "cash_flows", "quality", "freshness"}
    if not required.issubset(instrument):
        raise FixedIncomeComparisonError("fixed-income input is missing required terms")
    if instrument["quality"] != "VALID" or instrument["freshness"] not in ("VALID", "PASS"):
        return {"status": "INSUFFICIENT", "data_quality": "STALE_OR_INVALID", "instrument": instrument}
    currency = instrument["currency"]
    if not isinstance(currency, str) or len(currency) != 3:
        raise FixedIncomeComparisonError("fixed-income currency must be an explicit ISO-style code")
    try:
        maturity = date.fromisoformat(str(instrument["maturity_date"]))
    except (TypeError, ValueError) as exc:
        raise FixedIncomeComparisonError("maturity_date must be an ISO date") from exc
    if not instrument["cash_flows"]:
        return {"status": "INSUFFICIENT", "data_quality": "MISSING_CASH_FLOWS", "instrument": instrument}
    cash_flows = []
    for flow in instrument["cash_flows"]:
        if not {"date", "amount", "currency"}.issubset(flow):
            raise FixedIncomeComparisonError("cash-flow entries require date, amount, and currency")
        if flow["currency"] != currency:
            raise FixedIncomeComparisonError("cash-flow currency must match instrument currency")
        try:
            amount = Decimal(str(flow["amount"]))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise FixedIncomeComparisonError("cash-flow amount must be numeric") from exc
        if not amount.is_finite() or amount < 0:
            raise FixedIncomeComparisonError("cash-flow amount must be finite and non-negative")
        try:
            flow_date = date.fromisoformat(str(flow["date"]))
        except (TypeError, ValueError) as exc:
            raise FixedIncomeComparisonError("cash-flow date must be an ISO date") from exc
        cash_flows.append({"date": flow_date.isoformat(), "amount": str(amount), "currency": currency})
    if any(date.fromisoformat(flow["date"]) > maturity for flow in cash_flows):
        raise FixedIncomeComparisonError("cash-flow date cannot be after maturity")

    facts = {
        "status": "PASS", "data_quality": "VALID", "currency": currency,
        "instrument_id": str(instrument["instrument_id"]), "instrument_type": instrument["instrument_type"],
        "maturity_date": maturity.isoformat(), "cash_flows": cash_flows,
        "cash_flow_total": str(sum((Decimal(flow["amount"]) for flow in cash_flows), Decimal("0"))),
        "liquidity": instrument.get("liquidity"), "credit_quality": instrument.get("credit_quality"),
        "issuer": instrument.get("issuer"), "tax_treatment": instrument.get("tax_treatment"),
        "portfolio_role": instrument.get("portfolio_role"), "provenance": instrument.get("provenance", {}),
    }
    for name in ("face_amount", "settlement_amount", "clean_price", "accrued_interest", "coupon_rate"):
        if instrument.get(name) is not None:
            try:
                value = Decimal(str(instrument[name]))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise FixedIncomeComparisonError(f"{name} must be numeric") from exc
            if not value.is_finite() or value < 0:
                raise FixedIncomeComparisonError(f"{name} must be finite and non-negative")
            facts[name] = str(value)
    if "settlement_amount" in facts and "clean_price" in facts and "accrued_interest" in facts:
        expected = Decimal(facts["clean_price"]) + Decimal(facts["accrued_interest"])
        if Decimal(facts["settlement_amount"]) != expected:
            return {"status": "CONFLICTING", "data_quality": "CONFLICTING_TERMS", "instrument": instrument}
    if instrument.get("yield_metric") is not None:
        metric = instrument["yield_metric"]
        if not {"name", "value", "unit"}.issubset(metric):
            raise FixedIncomeComparisonError("yield_metric requires name, value, and unit")
        try:
            yield_value = Decimal(str(metric["value"]))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise FixedIncomeComparisonError("yield metric must be numeric") from exc
        if not yield_value.is_finite() or yield_value < 0:
            raise FixedIncomeComparisonError("yield metric must be finite and non-negative")
        facts["yield_metric"] = {"name": metric["name"], "value": str(yield_value), "unit": metric["unit"]}
    if alternative is not None:
        facts["alternative"] = {key: alternative[key] for key in ("name", "kind", "currency") if key in alternative}
    return facts


class FixedIncomeComparatorAgent:
    """Interpret a supplied fixed-income alternative against another capital use."""

    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    def run(self, request: ResearchRequest, fixed_income: dict, alternative: dict | None = None) -> ResearchResult:
        model = self.gateway.registry.resolve("fixed_income_comparator")
        try:
            validate_evidence_items(None, request.evidence)
            facts = deterministic_fixed_income_facts(fixed_income, alternative)
        except (EvidenceBoundaryError, FixedIncomeComparisonError) as exc:
            raise FixedIncomeComparisonError(str(exc)) from exc
        if facts["status"] != "PASS":
            return ResearchResult(
                conclusion="Fixed-income comparison is insufficient or conflicting; no comparison conclusion is authorized.",
                claims=[], uncertainty="HIGH", data_quality_concerns=[facts["data_quality"]],
                data_quality_assessment=facts["data_quality"], assessment="INSUFFICIENT",
                model_provider=model.provider, model_version=model.model_version, prompt_version=model.prompt_version,
                researched_at=datetime.now(timezone.utc), input_evidence_ids=[item.evidence_id for item in request.evidence],
            )
        response = self.gateway.invoke("fixed_income_comparator", request.question, {
            "question": request.question, "fixed_income_facts": facts,
            "alternative": alternative, "evidence": [item.model_dump() for item in request.evidence],
            "instruction": "Interpret only supplied fixed-income facts and supplied alternative facts. Do not calculate yield, duration, return, settlement, tax, credit, or expected return. Do not rank universally, allocate capital, forecast, or invent missing terms. Use FACT/INFERENCE/UNKNOWN/CONTRADICTION and preserve explicit currency, maturity, liquidity, credit, tax, and cost semantics. Return structured JSON only.",
        })
        result = ResearchResult.model_validate({
            **response.output, "model_provider": response.model.provider, "model_version": response.model.model_version,
            "prompt_version": response.model.prompt_version, "researched_at": response.requested_at,
            "input_evidence_ids": [item.evidence_id for item in request.evidence],
        })
        try:
            validate_claim_references(result.claims, {item.evidence_id for item in request.evidence}, {item.evidence_id: item.status for item in request.evidence})
        except EvidenceBoundaryError as exc:
            raise ResearchValidationError(str(exc)) from exc
        return result


class FakeFixedIncomeComparatorModel:
    def complete(self, request) -> dict:
        facts = request.payload["fixed_income_facts"]
        evidence = request.payload.get("evidence", [])
        claims = [] if not evidence else [{"text": evidence[0]["excerpt"], "kind": "FACT", "evidence_ids": [evidence[0]["evidence_id"]], "confidence": "MEDIUM"}]
        yield_text = "Supplied yield metric was interpreted without recalculation." if facts.get("yield_metric") else "Yield interpretation is UNKNOWN because no supplied yield metric was provided."
        return {
            "conclusion": "The supplied fixed-income alternative provides an explicit maturity and cash-flow profile for comparison; no allocation decision was made.",
            "claims": claims, "material_changes": [], "thesis_impacts": ["DOES_NOT_ADDRESS"],
            "contradictions": [], "unanswered_questions": [],
            "risks": ["Liquidity and credit risks remain dependent on supplied terms."], "uncertainty": "MEDIUM",
            "data_quality_concerns": [], "assessment": "COMPARABLE",
            "comparison_summary": "Compare the supplied cash-flow, maturity, liquidity, credit, currency, and opportunity-cost facts.",
            "cash_flow_interpretation": f"Total supplied cash flows: {facts['cash_flow_total']} {facts['currency']}.",
            "yield_interpretation": yield_text,
            "maturity_liquidity_interpretation": f"Maturity is {facts['maturity_date']}; liquidity is {facts.get('liquidity') or 'UNKNOWN'}.",
            "credit_interpretation": f"Credit quality is {facts.get('credit_quality') or 'UNKNOWN'}.",
            "currency_interpretation": f"All supplied cash flows are denominated in {facts['currency']}; no conversion was applied.",
            "tax_cost_interpretation": "Tax and cost interpretation is UNKNOWN unless explicitly supplied.",
            "portfolio_role": facts.get("portfolio_role") or "UNKNOWN",
            "opportunity_cost_interpretation": "Opportunity cost requires comparison with supplied alternative facts; no expected return was assumed.",
            "data_quality_assessment": "VALID",
        }