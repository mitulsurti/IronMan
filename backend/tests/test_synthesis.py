from datetime import datetime, timezone

import pytest

from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.research.schemas import EvidenceItem, ResearchRequest, ResearchResult, ThesisImpact
from ironman.research.synthesis import FakeSynthesisModel, SynthesisAgent
from ironman.research.agent import ResearchValidationError


def agent(model=None):
    return SynthesisAgent(ModelGateway(ModelRegistry([ModelSpec("fake", "synthesis", "fixture-v1", "synthesis", "synthesis-prompt-v1", {})]), {"fake": model or FakeSynthesisModel()}))


def evidence(text="Evidence supports the candidate", status="VALID"):
    return EvidenceItem(evidence_id="e1", source="fixture", excerpt=text, provenance={"source": "fixture"}, status=status)


def result(**kwargs):
    return ResearchResult(conclusion=kwargs.pop("conclusion", "supported"), claims=kwargs.pop("claims", []), thesis_impacts=kwargs.pop("thesis_impacts", []), uncertainty=kwargs.pop("uncertainty", "MEDIUM"), model_provider="fake", model_version="v1", prompt_version="p1", researched_at=datetime.now(timezone.utc), **kwargs)


def run(**kwargs):
    values = {"research": result(), "fundamental_thesis": result(thesis_impacts=["STRENGTHENS"]), "valuation": result(), "portfolio_risk": result(material_changes=["Portfolio assessment: FAVORABLE"])}
    values.update(kwargs)
    return agent().run(ResearchRequest(question="Synthesize", evidence=[evidence()]), portfolio_state_version_id="state-1", portfolio_facts={"current_weight": "0.1", "proposed_weight": "0.15", "gates": {"concentration": "PASS"}}, deterministic_valuation={"status": "PASS", "methods": {"pe": "10"}}, alternatives=[{"name": "WAIT", "kind": "CASH"}], gates={"concentration": "PASS"}, **values)


def test_favorable_synthesis_preserves_traceability():
    output = run()
    assert "FAVORABLE" in output.conclusion
    assert output.claims[0].evidence_ids == ["e1"]
    assert output.input_evidence_ids == ["e1"]
    assert output.model_version == "fixture-v1"


def test_failed_gate_produces_non_actionable_explanation():
    output = agent().run(ResearchRequest(question="Synthesize", evidence=[evidence()]), portfolio_state_version_id="state-1", portfolio_facts={"current_weight": "0.1", "proposed_weight": "0.5"}, deterministic_valuation={"status": "PASS"}, research=None, fundamental_thesis=None, valuation=None, portfolio_risk=None, alternatives=[{"name": "WAIT", "kind": "CASH"}], gates={"concentration": "BLOCKED"})
    assert "WAIT/NO_ACTION" in output.conclusion


def test_missing_context_is_insufficient():
    output = agent().run(ResearchRequest(question="Synthesize", evidence=[evidence()]), portfolio_state_version_id=None, portfolio_facts={}, deterministic_valuation={}, research=None, fundamental_thesis=None, valuation=None, portfolio_risk=None, alternatives=[], gates={})
    assert output.uncertainty == "HIGH"


def test_conflicting_capabilities_are_explicit():
    output = run(fundamental_thesis=result(thesis_impacts=["STRENGTHENS"]), valuation=result(thesis_impacts=["WEAKENS"]))
    assert output.contradictions
    assert output.uncertainty == "HIGH"


def test_stale_evidence_and_unsupported_fact_rejected():
    stale = agent().run(ResearchRequest(question="x", evidence=[evidence(status="STALE")]), portfolio_state_version_id="s", portfolio_facts={"current_weight": "0", "proposed_weight": "0", "gates": {}}, deterministic_valuation={}, research=None, fundamental_thesis=None, valuation=None, portfolio_risk=None, alternatives=[], gates={})
    assert stale.uncertainty == "HIGH"
    class BadModel:
        def complete(self, request):
            return {"conclusion": "x", "claims": [{"text": "bad", "kind": "FACT", "evidence_ids": [], "confidence": "HIGH"}], "uncertainty": "LOW"}
    with pytest.raises(ResearchValidationError):
        SynthesisAgent(ModelGateway(ModelRegistry([ModelSpec("bad", "s", "v", "synthesis", "p", {})]), {"bad": BadModel()})).run(ResearchRequest(question="x", evidence=[evidence()]), portfolio_state_version_id="s", portfolio_facts={"current_weight": "0", "proposed_weight": "0", "gates": {"concentration": "PASS"}}, deterministic_valuation={}, research=None, fundamental_thesis=None, valuation=None, portfolio_risk=None, alternatives=[], gates={"concentration": "PASS"})
