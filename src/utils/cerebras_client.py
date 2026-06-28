from __future__ import annotations

import json
import os
import time
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

from src.models.schemas import (
    FinalIncidentReport,
    Hypothesis,
    IncidentInput,
    UniverseResult,
    VisionReport,
)

T = TypeVar("T", bound=BaseModel)


def _strictify(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively enforce additionalProperties=false on every object schema.

    Cerebras/GLM strict json_schema mode rejects the request unless every
    nested object (including $defs entries) sets additionalProperties=false,
    not just the top-level schema.
    """
    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "type" in node and node["type"] == "object":
                node["additionalProperties"] = False
            if "type" in node and node["type"] == "array":
                # Cerebras strict json_schema rejects array minItems/maxItems.
                node.pop("minItems", None)
                node.pop("maxItems", None)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)
    return schema


class CerebrasClientError(RuntimeError):
    """Raised when a live or structured model call cannot be completed."""


class CerebrasClient:
    """Cerebras/OpenAI-compatible client with mock and live structured output modes."""

    def __init__(self, mock: bool | None = None) -> None:
        self.model = os.getenv("CEREBRAS_MODEL", "gemma-4-31b")
        self.base_url = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1")
        self.api_key = os.getenv("CEREBRAS_API_KEY")
        self.reasoning_effort = os.getenv("CEREBRAS_REASONING_EFFORT", "low")
        self.mock = self._env_bool("MULTIVERSEGUARD_MOCK", True) if mock is None else mock
        if not self.api_key:
            self.mock = True

        self._client = None
        if not self.mock:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise CerebrasClientError("Install openai or set MULTIVERSEGUARD_MOCK=true.") from exc
            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    def structured_output(
        self,
        *,
        schema: Type[T],
        system_prompt: str,
        user_prompt: str,
        image_data_uri: str | None = None,
        temperature: float = 0.2,
        max_completion_tokens: int = 3000,
    ) -> tuple[T, dict[str, Any]]:
        """Return a Pydantic object plus timing metadata."""
        started = time.perf_counter()

        if self.mock:
            result = self._mock_response(schema=schema, user_prompt=user_prompt)
            elapsed_ms = (time.perf_counter() - started) * 1000
            return result, self._timing(result, elapsed_ms, user_prompt, mode="mock")

        if self._client is None:
            raise CerebrasClientError("Live client is not initialized.")

        user_content: str | list[dict[str, Any]] = user_prompt
        if image_data_uri:
            user_content = [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": image_data_uri}},
            ]

        schema_dict = _strictify(schema.model_json_schema())

        request: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "max_completion_tokens": max_completion_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": schema_dict,
                },
            },
        }
        if self.reasoning_effort and self.reasoning_effort.lower() != "none":
            request["reasoning_effort"] = self.reasoning_effort

        def _complete(req: dict[str, Any]):
            try:
                return self._client.chat.completions.create(**req)
            except Exception:
                if "reasoning_effort" not in req:
                    raise
                req.pop("reasoning_effort", None)
                return self._client.chat.completions.create(**req)

        response = _complete(request)

        # If the model hit the token budget the JSON is truncated and will not
        # parse. Retry once with a larger budget so verbose synthesis output
        # (4 ranked universes with long evidence lists) can complete.
        finish_reason = getattr(response.choices[0], "finish_reason", None)
        if finish_reason == "length":
            request["max_completion_tokens"] = min(max_completion_tokens * 4, 16384)
            response = _complete(request)

        elapsed_ms = (time.perf_counter() - started) * 1000
        content = response.choices[0].message.content or ""
        if isinstance(content, list):
            content = "".join(str(part.get("text", "")) if isinstance(part, dict) else str(part) for part in content)

        finish_reason = getattr(response.choices[0], "finish_reason", None)
        try:
            payload = json.loads(str(content))
        except json.JSONDecodeError as exc:
            if finish_reason == "length":
                raise CerebrasClientError(
                    f"{schema.__name__} response was truncated (finish_reason=length) at "
                    f"max_completion_tokens={request['max_completion_tokens']}; raise the budget or shorten the prompt."
                ) from exc
            raise CerebrasClientError(f"{schema.__name__} response was not valid JSON: {str(content)[:500]}") from exc

        try:
            result = schema.model_validate(payload)
        except ValidationError as exc:
            raise CerebrasClientError(f"{schema.__name__} response failed schema validation: {exc}") from exc

        timing = self._timing(result, elapsed_ms, user_prompt, mode="live")
        usage = getattr(response, "usage", None)
        timing["input_tokens"] = int(getattr(usage, "prompt_tokens", 0) or timing["input_tokens"])
        timing["output_tokens"] = int(getattr(usage, "completion_tokens", 0) or timing["output_tokens"])
        timing["tokens_per_second"] = round(timing["output_tokens"] / (elapsed_ms / 1000), 2) if elapsed_ms else 0.0
        return result, timing

    def _timing(self, result: BaseModel, elapsed_ms: float, user_prompt: str, *, mode: str) -> dict[str, Any]:
        output_tokens = max(1, len(result.model_dump_json()) // 4)
        seconds = max(elapsed_ms / 1000, 0.001)
        return {
            "mode": mode,
            "model": self.model,
            "elapsed_ms": round(elapsed_ms, 2),
            "input_tokens": max(1, len(user_prompt) // 4),
            "output_tokens": output_tokens,
            "tokens_per_second": round(output_tokens / seconds, 2),
        }

    def _mock_response(self, *, schema: Type[T], user_prompt: str) -> T:
        if schema is VisionReport:
            return VisionReport(
                summary="Checkout failures began shortly after a full checkout-api deployment, with DB pool saturation, payment retries, cache uncertainty, and a feature flag all present as competing signals.",
                key_observations=[
                    "checkout-api v2.18.0 was promoted before latency and 5xx increased",
                    "database pool reached 100/100 active connections with acquisition timeouts",
                    "payment retries appear, but the provider status page is green",
                    "Redis hit rate is slightly lower, suggesting but not proving cache pressure",
                    "checkout_recommendations_v2 was enabled before the incident window",
                ],
            )  # type: ignore[return-value]

        if schema is Hypothesis:
            return self._mock_hypothesis(user_prompt)  # type: ignore[return-value]

        if schema is UniverseResult:
            return self._mock_universe(user_prompt)  # type: ignore[return-value]

        if schema is FinalIncidentReport:
            universes = sorted(
                [
                    self._mock_universe("U-1"),
                    self._mock_universe("U-2"),
                    self._mock_universe("U-3"),
                    self._mock_universe("U-4"),
                ],
                key=lambda item: item.confidence,
                reverse=True,
            )
            return FinalIncidentReport(
                winning_universe=universes[0].universe_id,
                ranked_universes=universes,
                overall_summary=(
                    "The strongest mock universe is database connection pool exhaustion after the checkout deployment. "
                    "Payment latency, cache thundering herd, and feature-flag regression remain visible alternate universes with lower confidence."
                ),
                recommended_next_steps=[
                    "Freeze checkout deploys and roll back checkout-api v2.18.0",
                    "Watch checkout 5xx, p95 latency, and DB pool active connections for recovery",
                    "In parallel, inspect payment p99 latency, cache hit rate, and feature-flag exposure",
                    "Keep rollback and validation notes attached to the incident timeline",
                ],
            )  # type: ignore[return-value]

        if schema is IncidentInput:
            return IncidentInput(logs=user_prompt, image_description=None)  # type: ignore[return-value]

        raise CerebrasClientError(f"No mock response is defined for {schema.__name__}.")

    def _mock_hypothesis(self, hint: str) -> Hypothesis:
        if "H-2" in hint:
            return Hypothesis(
                hypothesis_id="H-2",
                description="Payment gateway latency cascaded into checkout failures.",
            )
        if "H-3" in hint:
            return Hypothesis(
                hypothesis_id="H-3",
                description="Cache invalidation caused a thundering herd against the database.",
            )
        if "H-4" in hint:
            return Hypothesis(
                hypothesis_id="H-4",
                description="Feature flag introduced an expensive synchronous checkout code path.",
            )
        return Hypothesis(
            hypothesis_id="H-1",
            description="Database connection pool exhaustion after checkout deployment.",
        )

    def _mock_universe(self, hint: str) -> UniverseResult:
        if "Universe ID: U-2" in hint or hint.strip() == "U-2" or "H-2" in hint:
            return UniverseResult(
                universe_id="U-2",
                hypothesis="Payment gateway latency cascaded into checkout failures.",
                confidence=0.71,
                evidence=[
                    "payment_authorize retries appear during the incident window",
                    "customers report payment spinner and intermittent payment failure symptoms",
                    "checkout threads could hold resources while waiting on downstream authorization",
                ],
                recommended_action="Check provider p95/p99 latency and enable the payment circuit breaker only if degradation is confirmed.",
                rollback="Disable the circuit-breaker override and return traffic to the normal payment path after provider metrics recover.",
                missing_evidence=[
                    "provider p95/p99 latency for the exact incident window",
                    "payment adapter error-code breakdown",
                    "thread or trace samples proving checkout waits on payment calls",
                ],
            )
        if "Universe ID: U-3" in hint or hint.strip() == "U-3" or "H-3" in hint:
            return UniverseResult(
                universe_id="U-3",
                hypothesis="Cache invalidation caused a thundering herd against the database.",
                confidence=0.65,
                evidence=[
                    "Redis hit rate is reported as slightly lower near incident start",
                    "DB saturation can follow cache miss storms on cart, pricing, or promotion reads",
                    "autoscaling checkout pods did not relieve pressure, suggesting a shared downstream bottleneck",
                ],
                recommended_action="Inspect cache hit rate and temporarily disable nonessential checkout enrichments that trigger DB reads.",
                rollback="Re-enable enrichments one at a time after cache hit rate and DB active connections return to baseline.",
                missing_evidence=[
                    "cache hit-rate graph by key family",
                    "DB read QPS grouped by query fingerprint",
                    "cache invalidation or TTL-change audit event",
                ],
            )
        if "Universe ID: U-4" in hint or hint.strip() == "U-4" or "H-4" in hint:
            return UniverseResult(
                universe_id="U-4",
                hypothesis="Feature flag introduced an expensive synchronous checkout code path.",
                confidence=0.54,
                evidence=[
                    "checkout_recommendations_v2 was enabled before the incident window",
                    "feature-gated recommendation calls could add expensive reads to the checkout critical path",
                    "a 25% cohort can still create visible DB pressure during peak checkout traffic",
                ],
                recommended_action="Disable checkout_recommendations_v2 for the incident cohort and compare checkout latency and DB pool recovery.",
                rollback="Re-enable the flag gradually behind canary cohorts after traces prove the code path is safe.",
                missing_evidence=[
                    "feature exposure audit by user cohort",
                    "trace spans showing recommendation calls inside checkout submit",
                    "comparison of impacted versus non-impacted cohorts",
                ],
            )
        return UniverseResult(
            universe_id="U-1",
            hypothesis="Database connection pool exhaustion after checkout deployment.",
            confidence=0.82,
            evidence=[
                "checkout-api v2.18.0 reached 100% shortly before the 5xx spike",
                "orders-db pool active connections pinned at 100/100 with pending requests",
                "logs show db connection acquisition exceeded 2500ms on checkout submit",
                "autoscaling application pods did not resolve the shared DB bottleneck",
            ],
            recommended_action="Freeze checkout deploys and roll back checkout-api v2.18.0 while watching DB pool recovery.",
            rollback="Re-deploy v2.18.0 only as a limited canary after the slow query or connection leak is fixed.",
            missing_evidence=[
                "slow query sample from v2.18.0",
                "connection acquisition wait histogram before and after rollback",
                "rollback recovery result from checkout 5xx and DB pool metrics",
            ],
        )
