import pytest

from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.research.agent import ResearchEvidenceAgent
from ironman.research.schemas import EvidenceItem, ResearchRequest
from datetime import datetime, timezone


class BrokenModel:
    def complete(self, request):
        raise RuntimeError("provider unavailable")


def test_gateway_missing_capability_is_clear():
    with pytest.raises(LookupError):
        ModelGateway(ModelRegistry(), {}).invoke("research", "x", {})


def test_research_agent_preserves_malformed_model_output_as_validation_failure():
    gateway = ModelGateway(ModelRegistry([ModelSpec("bad", "d", "v", "research", "p", {})]), {"bad": BrokenModel()})
    with pytest.raises(RuntimeError):
        ResearchEvidenceAgent(gateway).run(ResearchRequest(question="x", evidence=[]))
