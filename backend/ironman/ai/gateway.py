from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Protocol


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    deployment_id: str
    model_version: str
    capability: str
    prompt_version: str
    cost_metadata: dict


@dataclass(frozen=True)
class ModelRequest:
    task: str
    payload: dict
    model: ModelSpec


@dataclass(frozen=True)
class ModelResponse:
    output: dict
    model: ModelSpec
    status: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    requested_at: datetime
    error_category: str | None = None


class ModelImplementation(Protocol):
    def complete(self, request: ModelRequest) -> dict: ...


class ModelRegistry:
    def __init__(self, models: list[ModelSpec] | None = None) -> None:
        self._models = {model.capability: model for model in (models or [])}

    def register(self, model: ModelSpec) -> None:
        self._models[model.capability] = model

    def resolve(self, capability: str) -> ModelSpec:
        if capability not in self._models:
            raise LookupError(f"no model registered for capability: {capability}")
        return self._models[capability]


class ModelGateway:
    def __init__(self, registry: ModelRegistry, implementations: dict[str, ModelImplementation]) -> None:
        self.registry = registry
        self.implementations = implementations
        self.telemetry: list[ModelResponse] = []

    def invoke(self, capability: str, task: str, payload: dict) -> ModelResponse:
        model = self.registry.resolve(capability)
        implementation = self.implementations[model.provider]
        request = ModelRequest(task=task, payload=payload, model=model)
        started = perf_counter()
        try:
            output = implementation.complete(request)
        except Exception as exc:
            error_category = getattr(exc, "category", "provider_error")
            response = ModelResponse(
                output={}, model=model, status="FAILED", latency_ms=int((perf_counter() - started) * 1000),
                input_tokens=None, output_tokens=None, requested_at=datetime.now(timezone.utc), error_category=error_category,
            )
            self.telemetry.append(response)
            raise
        usage = output.pop("_provider_usage", {}) if isinstance(output, dict) else {}
        response = ModelResponse(
            output=output,
            model=model,
            status="SUCCEEDED",
            latency_ms=int((perf_counter() - started) * 1000),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            requested_at=datetime.now(timezone.utc),
        )
        self.telemetry.append(response)
        return response
