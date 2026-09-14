"""Opt-in live Azure smoke test. Normal CI/local runs skip without configuration."""
import os

import pytest

from ironman.ai.azure_provider import AzureChatModel, AzureModelConfig
from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.research.agent import ResearchEvidenceAgent
from ironman.research.schemas import EvidenceItem, ResearchRequest


@pytest.mark.live
@pytest.mark.live_azure
def test_live_azure_research_smoke():
    config = AzureModelConfig.from_environment()
    deployment = os.getenv("IRONMAN_AZURE_OPENAI_DEPLOYMENT")
    if config is None or not deployment:
        pytest.skip("Azure smoke test skipped: endpoint, API key, or deployment is not configured")
    model = ModelSpec("azure", deployment, os.getenv("IRONMAN_AZURE_MODEL_VERSION", "configured"), "research", os.getenv("IRONMAN_RESEARCH_PROMPT_VERSION", "research-prompt-v1"), {})
    gateway = ModelGateway(ModelRegistry([model]), {"azure": AzureChatModel(config)})
    result = ResearchEvidenceAgent(gateway).run(ResearchRequest(
        question="Summarize only the supplied evidence; do not calculate or recommend execution.",
        evidence=[EvidenceItem(evidence_id="smoke-1", source="fixture", excerpt="The supplied fixture states revenue increased.", provenance={"source": "smoke-fixture"})],
    ))
    assert result.model_provider == "azure"
    assert result.model_version == model.model_version
    assert result.prompt_version == model.prompt_version
    assert result.input_evidence_ids == ["smoke-1"]
    assert gateway.telemetry and gateway.telemetry[-1].status == "SUCCEEDED"
    assert gateway.telemetry[-1].input_tokens is None or gateway.telemetry[-1].input_tokens >= 0
    assert gateway.telemetry[-1].output_tokens is None or gateway.telemetry[-1].output_tokens >= 0
