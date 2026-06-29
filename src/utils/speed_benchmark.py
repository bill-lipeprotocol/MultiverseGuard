"""Lightweight speed benchmark comparing Cerebras against Together AI.

This module is intentionally isolated from the main MultiverseGuard graph.
It only runs the same compact text-only prompt against each provider and
reports timing. It does NOT run the four-universe LangGraph workflow.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

BENCHMARK_PROMPT = """You are an enterprise incident response analyst.

Incident:
Checkout error rate increased after a deployment. Database pool usage is high, payment API latency is elevated, and the dashboard shows rising p95 latency.

Return compact JSON with:
- four possible root causes
- confidence for each root cause
- one recommended first action
- one rollback or mitigation step

Keep the answer under 250 words.
"""

BENCHMARK_SYSTEM_PROMPT = "Return concise, valid JSON only."


@dataclass
class BenchmarkResult:
    provider: str
    model: str
    latency_seconds: float
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    tokens_per_second: Optional[float]
    output_preview: str
    error: Optional[str] = None


def run_openai_compatible_benchmark(
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    max_tokens: int = 500,
    temperature: float = 0.2,
) -> BenchmarkResult:
    """Run the benchmark prompt against one OpenAI-compatible endpoint."""
    if not api_key:
        return BenchmarkResult(
            provider=provider,
            model=model,
            latency_seconds=0.0,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            tokens_per_second=None,
            output_preview="",
            error=f"{provider} API key is not configured.",
        )

    client = OpenAI(api_key=api_key, base_url=base_url)

    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": BENCHMARK_SYSTEM_PROMPT},
                {"role": "user", "content": BENCHMARK_PROMPT},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = time.perf_counter() - start
        message = response.choices[0].message.content or ""

        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
        total_tokens = getattr(usage, "total_tokens", None) if usage else None

        tokens_for_rate = completion_tokens or total_tokens
        tokens_per_second = (
            tokens_for_rate / latency
            if tokens_for_rate is not None and latency > 0
            else None
        )

        return BenchmarkResult(
            provider=provider,
            model=model,
            latency_seconds=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            tokens_per_second=tokens_per_second,
            output_preview=message[:800],
            error=None,
        )
    except Exception as exc:  # noqa: BLE001 - benchmark must not crash the UI
        latency = time.perf_counter() - start
        return BenchmarkResult(
            provider=provider,
            model=model,
            latency_seconds=latency,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            tokens_per_second=None,
            output_preview="",
            error=str(exc),
        )


def run_cerebras_benchmark() -> BenchmarkResult:
    return run_openai_compatible_benchmark(
        provider="Cerebras",
        base_url=os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1"),
        api_key=os.getenv("CEREBRAS_API_KEY", ""),
        model=os.getenv("CEREBRAS_MODEL", "gemma-4-31b"),
        max_tokens=500,
        temperature=0.2,
    )


def run_together_benchmark() -> BenchmarkResult:
    return run_openai_compatible_benchmark(
        provider="Together AI",
        base_url=os.getenv("TOGETHER_BASE_URL", "https://api.together.ai/v1"),
        api_key=os.getenv("TOGETHER_API_KEY", ""),
        model=os.getenv("TOGETHER_MODEL", "zai-org/GLM-5.2"),
        max_tokens=500,
        temperature=0.2,
    )


def calculate_speedup(
    cerebras_result: BenchmarkResult, together_result: BenchmarkResult
) -> Optional[float]:
    """Return together_latency / cerebras_latency when both calls succeeded."""
    if cerebras_result.error or together_result.error:
        return None
    if cerebras_result.latency_seconds <= 0:
        return None
    return together_result.latency_seconds / cerebras_result.latency_seconds


def result_to_display_dict(result: BenchmarkResult) -> dict:
    """Return a key-safe view of a benchmark result for UI/audit display.

    Intentionally excludes any API keys; only timing, model, and output metadata.
    """
    return {
        "provider": result.provider,
        "model": result.model,
        "latency_seconds": round(result.latency_seconds, 4),
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "total_tokens": result.total_tokens,
        "tokens_per_second": (
            round(result.tokens_per_second, 2)
            if result.tokens_per_second is not None
            else None
        ),
        "error": result.error,
    }
