from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.intelligence.analytics import valuation_facts
from ironman.research.schemas import EvidenceItem, ResearchRequest
from ironman.research.synthesis import FakeSynthesisModel, SynthesisAgent


def test_yahoo_shaped_facts_flow_to_deterministic_synthesis():
    yahoo_observations = {
        "price": "123.45",
        "eps": "10.25",
        "book_value_per_share": "50.50",
        "ebitda": "1000",
        "enterprise_value": "10000",
        "free_cash_flow": "450",
        "market_cap": "9000",
        "currency": "USD",
    }
    facts = valuation_facts(yahoo_observations)
    assert facts["methods"]["pe"] == str(Decimal("123.45") / Decimal("10.25"))
    assert facts["methods"]["pb"] == str(Decimal("123.45") / Decimal("50.50"))
    assert facts["currency"] == "USD"
    gateway = ModelGateway(ModelRegistry([ModelSpec("fake", "synthesis", "fixture-v1", "synthesis", "synthesis-prompt-v1", {})]), {"fake": FakeSynthesisModel()})
    result = SynthesisAgent(gateway).run(
        ResearchRequest(question="Assess supplied real-data-shaped facts", evidence=[EvidenceItem(evidence_id="e1", source="yahoo-fixture", excerpt="Current facts supplied by adapter fixture", provenance={"source": "test"})]),
        portfolio_state_version_id=uuid4(),
        portfolio_facts={"current_weight": "0.05", "proposed_weight": "0.10"},
        deterministic_valuation=facts,
        research=None,
        fundamental_thesis=None,
        valuation=None,
        portfolio_risk=None,
        alternatives=[{"name": "WAIT", "kind": "CASH"}],
        gates={"observations": "PASS", "concentration": "PASS"},
    )
    assert result.input_evidence_ids == ["e1"]
    assert result.model_provider == "fake"
