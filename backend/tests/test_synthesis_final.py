from datetime import datetime, timezone

import pytest

from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.research.schemas import EvidenceItem, ResearchRequest, ResearchResult
from ironman.research.synthesis import FakeSynthesisModel, SynthesisAgent
from ironman.research.agent import ResearchValidationError


def agent(model=None):
    return SynthesisAgent(ModelGateway(ModelRegistry([ModelSpec("fake", "synthesis", "fixture-v1", "synthesis", "synthesis-prompt-v1", {})]), {"fake": model or FakeSynthesisModel()}))


def evidence(text="Evidence supports the candidate", status="VALID"):
    return EvidenceItem(evidence_id="e1", source="fixture", excerpt=text, provenance={"source": "fixture"}, status=status)


def result(**kwargs):
    return ResearchResult(conclusion="supported", claims=[], uncertainty="MEDIUM", model_provider="fake", model_version="v1", prompt_version="p1", researched_at=datetime.now(timezone.utc), **kwargs)


def base(**kwargs):
    values = {"research": result(), "fundamental_thesis": result(thesis_impacts=["STRENGTHENS"]), "valuation": result(), "portfolio_risk": result(material_changes=["Portfolio assessment: FAVORABLE"])}
    values.update(kwargs)
    defaults = dict(portfolio_state_version_id="state-1", portfolio_facts={"current_weight": "0.1", "proposed_weight": "0.15"}, deterministic_valuation={"status": "PASS", "methods": {"pe": "10"}}, alternatives=[{"name": "WAIT", "kind": "CASH"}], gates={"concentration": "PASS"})
    defaults.update(values)
    return defaults


def test_favorable_traceable_synthesis():
    output = agent().run(ResearchRequest(question="Synthesize", evidence=[evidence()]), **base())
    assert "FAVORABLE" in output.conclusion
    assert output.input_evidence_ids == ["e1"]
    assert output.model_version == "fixture-v1"


def test_gate_failure_and_missing_context_are_non_actionable():
    blocked = agent().run(ResearchRequest(question="Synthesize", evidence=[evidence()]), **base(gates={"concentration": "BLOCKED"}))
    assert "WAIT/NO_ACTION" in blocked.conclusion
    insufficient = agent().run(ResearchRequest(question="Synthesize", evidence=[evidence()]), **base(portfolio_state_version_id=None, portfolio_facts={}, gates={}))
    assert insufficient.uncertainty == "HIGH"


def test_stale_evidence_abstains_and_conflict_is_explicit():
    stale = agent().run(ResearchRequest(question="Synthesize", evidence=[evidence(status="STALE")]), **base())
    assert stale.uncertainty == "HIGH"
    conflict = agent().run(ResearchRequest(question="Synthesize", evidence=[evidence()]), **base(fundamental_thesis=result(thesis_impacts=["STRENGTHENS"]), valuation=result(thesis_impacts=["WEAKENS"])))
    assert conflict.contradictions
    assert conflict.uncertainty == "HIGH"


def test_malformed_fact_claim_is_rejected():
    class BadModel:
        def complete(self, request):
            return {"conclusion": "bad", "claims": [{"text": "unsupported", "kind": "FACT", "evidence_ids": []}], "uncertainty": "LOW"}
    with pytest.raises(ResearchValidationError):
        SynthesisAgent(ModelGateway(ModelRegistry([ModelSpec("bad", "s", "v", "synthesis", "p", {})]), {"bad": BadModel()})).run(ResearchRequest(question="x", evidence=[evidence()]), **base())
