import json
from io import BytesIO

import pytest

from ironman.ai.azure_provider import AzureChatModel, AzureModelConfig, AzureProviderError
from ironman.ai.gateway import ModelRequest, ModelSpec


def request():
    return ModelRequest("research", {"evidence": [{"evidence_id": "e1", "excerpt": "Revenue increased"}]}, ModelSpec("azure", "research-deployment", "2025", "research", "prompt-v1", {}))


def test_missing_azure_configuration_returns_none(monkeypatch):
    monkeypatch.delenv("IRONMAN_AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("IRONMAN_AZURE_OPENAI_API_KEY", raising=False)
    assert AzureModelConfig.from_environment() is None


def test_azure_configuration_uses_environment_without_exposing_key(monkeypatch):
    monkeypatch.setenv("IRONMAN_AZURE_OPENAI_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("IRONMAN_AZURE_OPENAI_API_KEY", "secret-not-printed")
    config = AzureModelConfig.from_environment()
    assert config is not None
    assert config.endpoint == "https://example.invalid"
    assert "secret-not-printed" not in repr(config)


def test_request_construction_and_structured_response(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return json.dumps({"output_text": json.dumps({"conclusion": "supported", "claims": []}), "usage": {"input_tokens": 10, "output_tokens": 4, "total_tokens": 14}}).encode()

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.headers)
        captured["body"] = json.loads(req.data.decode())
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("ironman.ai.azure_provider.urlopen", fake_urlopen)
    result = AzureChatModel(AzureModelConfig("https://example", "secret", "2024", 9)).complete(request())
    assert result["conclusion"] == "supported"
    assert captured["url"] == "https://example/openai/v1/responses"
    assert captured["body"]["model"] == "research-deployment"
    assert captured["body"]["input"] == json.dumps(request().payload)
    assert captured["body"]["instructions"].endswith("Return JSON only.")
    assert captured["timeout"] == 9


def test_provider_failure_is_categorized(monkeypatch):
    def fail(*args, **kwargs):
        raise TimeoutError()
    monkeypatch.setattr("ironman.ai.azure_provider.urlopen", fail)
    with pytest.raises(AzureProviderError, match="unavailable") as error:
        AzureChatModel(AzureModelConfig("https://example", "secret", "2024")).complete(request())
    assert error.value.category == "network_or_timeout"
