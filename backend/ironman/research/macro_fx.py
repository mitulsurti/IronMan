"""Bounded interpretation of application-supplied macroeconomic and FX facts."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from ironman.ai.gateway import ModelGateway
from ironman.research.agent import ResearchValidationError
from ironman.research.evidence import EvidenceBoundaryError, validate_claim_references, validate_evidence_items
from ironman.research.schemas import ResearchRequest, ResearchResult


class MacroFXValidationError(ValueError):
    pass


def deterministic_macro_fx_facts(observations: list[dict]) -> dict:
    """Validate and normalize supplied macro/FX observations without forecasting."""
    if not observations:
        return {"status": "INSUFFICIENT", "observations": [], "data_quality": "MISSING"}
    normalized = []
    for item in observations:
        required = {"observation_id", "factor", "value", "unit", "currency", "quality", "freshness"}
        if not required.issubset(item):
            raise MacroFXValidationError("macro observation is missing required fields")
        if item["quality"] != "VALID" or item["freshness"] not in ("VALID", "PASS"):
            return {"status": "INSUFFICIENT", "observations": observations, "data_quality": "STALE_OR_INVALID"}
        try:
            value = Decimal(str(item["value"]))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise MacroFXValidationError("macro observation value is not numeric") from exc
        if not value.is_finite():
            raise MacroFXValidationError("macro observation value is not finite")
        factor = item["factor"]
        if factor in {"usd_inr", "inr_per_usd"} and item["unit"] != "INR_per_USD":
            raise MacroFXValidationError("USD/INR direction must use unit INR_per_USD")
        if factor == "usd_per_inr" and item["unit"] != "USD_per_INR":
            raise MacroFXValidationError("INR/USD direction must use unit USD_per_INR")
        normalized.append({**item, "value": str(value)})
    by_factor: dict[str, list[dict]] = {}
    for item in normalized:
        by_factor.setdefault(item["factor"], []).append(item)
    if any(len(items) > 1 and len({item["value"] for item in items}) > 1 for items in by_factor.values()):
        return {"status": "CONFLICTING", "observations": normalized, "data_quality": "CONFLICTING"}
    return {"status": "PASS", "observations": normalized, "data_quality": "VALID"}


class MacroFXAgent:
    """Bounded macro/FX interpretation; it cannot forecast or mutate financial state."""

    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    def run(self, request: ResearchRequest, macro_observations: list[dict]) -> ResearchResult:
        model = self.gateway.registry.resolve("macro_fx")
        try:
            validate_evidence_items(None, request.evidence)
            facts = deterministic_macro_fx_facts(macro_observations)
        except (EvidenceBoundaryError, MacroFXValidationError) as exc:
            raise MacroFXValidationError(str(exc)) from exc
        if facts["status"] != "PASS":
            return ResearchResult(
                conclusion="Macro/FX context is insufficient or conflicting; no macro conclusion is authorized.",
                claims=[], uncertainty="HIGH", data_quality_concerns=[facts["data_quality"]],
                data_quality_assessment=facts["data_quality"], assessment="INSUFFICIENT",
                model_provider=model.provider, model_version=model.model_version, prompt_version=model.prompt_version,
                researched_at=datetime.now(timezone.utc), input_evidence_ids=[item.evidence_id for item in request.evidence],
            )
        response = self.gateway.invoke("macro_fx", request.question, {
            "question": request.question, "instrument_id": request.instrument_id,
            "observations": facts["observations"], "thesis": request.thesis,
            "evidence": [item.model_dump() for item in request.evidence],
            "instruction": "Interpret only supplied macro/FX facts. Do not forecast prices, returns, rates, FX, inflation, growth, or policy. Do not invert currency direction. Do not calculate authoritative financial values or change allocations. Use FACT/INFERENCE/UNKNOWN/CONTRADICTION. Return only the required structured fields.",
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


class FakeMacroFXModel:
    def complete(self, request) -> dict:
        observations = request.payload["observations"]
        factors = [item["factor"] for item in observations]
        fx = [f"{item['factor']} is quoted as {item['unit']}; no inversion was applied." for item in observations if "inr" in item["factor"]]
        evidence = request.payload.get("evidence", [])
        claims = [] if not evidence else [{"text": evidence[0]["excerpt"], "kind": "FACT", "evidence_ids": [evidence[0]["evidence_id"]], "confidence": "MEDIUM"}]
        return {
            "conclusion": "Supplied macro/FX observations are relevant context only; no forecast or allocation decision was made.",
            "claims": claims, "material_changes": [], "thesis_impacts": ["DOES_NOT_ADDRESS"],
            "contradictions": [], "unanswered_questions": [], "risks": ["Macro conditions may change outside this supplied snapshot."],
            "uncertainty": "MEDIUM", "data_quality_concerns": [], "assessment": "RELEVANT",
            "relevant_macro_factors": factors, "fx_implications": fx, "data_quality_assessment": "VALID",
        }