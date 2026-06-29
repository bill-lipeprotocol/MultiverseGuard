"""Lightweight speed benchmark comparing Cerebras against Together AI.

This module is intentionally isolated from the main MultiverseGuard graph.
It only runs the same compact text-only prompt against each provider and
reports timing. It does NOT run the four-universe LangGraph workflow.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
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

# Four variant prompts used by the 4-way parallel benchmark. The base incident is
# identical, but each branch label differs so providers cannot trivially cache an
# identical prompt.
PARALLEL_BENCHMARK_PROMPTS = [
    BENCHMARK_PROMPT + "\nFocus universe: deployment/configuration regression.",
    BENCHMARK_PROMPT + "\nFocus universe: database or connection-pool saturation.",
    BENCHMARK_PROMPT + "\nFocus universe: upstream dependency/payment-provider latency.",
    BENCHMARK_PROMPT + "\nFocus universe: infrastructure/network/load-balancer failure.",
]


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


@dataclass
class ParallelBenchmarkResult:
    provider: str
    model: str
    wall_time_seconds: float
    call_count: int
    completed_count: int
    errored_count: int
    average_latency_seconds: Optional[float]
    max_latency_seconds: Optional[float]
    total_completion_tokens: Optional[int]
    aggregate_tokens_per_second: Optional[float]
    results: list[BenchmarkResult] = field(default_factory=list)
    error: Optional[str] = None


def run_openai_compatible_benchmark(
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str = BENCHMARK_PROMPT,
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
                {"role": "user", "content": prompt},
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


def run_parallel_openai_compatible_benchmark(
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    prompts: list[str] = PARALLEL_BENCHMARK_PROMPTS,
    max_workers: int = 4,
    max_tokens: int = 500,
    temperature: float = 0.2,
) -> ParallelBenchmarkResult:
    """Run several benchmark calls concurrently against one provider."""
    start = time.perf_counter()

    if not api_key:
        return ParallelBenchmarkResult(
            provider=provider,
            model=model,
            wall_time_seconds=0.0,
            call_count=len(prompts),
            completed_count=0,
            errored_count=len(prompts),
            average_latency_seconds=None,
            max_latency_seconds=None,
            total_completion_tokens=None,
            aggregate_tokens_per_second=None,
            results=[],
            error=f"{provider} API key is not configured.",
        )

    results: list[BenchmarkResult] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                run_openai_compatible_benchmark,
                provider,
                base_url,
                api_key,
                model,
                prompt,
                max_tokens,
                temperature,
            )
            for prompt in prompts
        ]

        for future in as_completed(futures):
            results.append(future.result())

    wall_time = time.perf_counter() - start

    completed = [result for result in results if result.error is None]
    errored = [result for result in results if result.error is not None]

    latencies = [result.latency_seconds for result in completed]
    completion_tokens = [
        result.completion_tokens
        for result in completed
        if result.completion_tokens is not None
    ]
    total_completion_tokens = sum(completion_tokens) if completion_tokens else None
    aggregate_tokens_per_second = (
        total_completion_tokens / wall_time
        if total_completion_tokens is not None and wall_time > 0
        else None
    )

    return ParallelBenchmarkResult(
        provider=provider,
        model=model,
        wall_time_seconds=wall_time,
        call_count=len(prompts),
        completed_count=len(completed),
        errored_count=len(errored),
        average_latency_seconds=sum(latencies) / len(latencies) if latencies else None,
        max_latency_seconds=max(latencies) if latencies else None,
        total_completion_tokens=total_completion_tokens,
        aggregate_tokens_per_second=aggregate_tokens_per_second,
        results=results,
        error=None if not errored else f"{len(errored)} of {len(prompts)} calls failed.",
    )


def run_cerebras_parallel_benchmark() -> ParallelBenchmarkResult:
    return run_parallel_openai_compatible_benchmark(
        provider="Cerebras",
        base_url=os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1"),
        api_key=os.getenv("CEREBRAS_API_KEY", ""),
        model=os.getenv("CEREBRAS_MODEL", "gemma-4-31b"),
    )


def run_together_parallel_benchmark() -> ParallelBenchmarkResult:
    return run_parallel_openai_compatible_benchmark(
        provider="Together AI",
        base_url=os.getenv("TOGETHER_BASE_URL", "https://api.together.ai/v1"),
        api_key=os.getenv("TOGETHER_API_KEY", ""),
        model=os.getenv("TOGETHER_MODEL", "zai-org/GLM-5.2"),
    )


def calculate_parallel_speedup(
    cerebras_result: ParallelBenchmarkResult, together_result: ParallelBenchmarkResult
) -> Optional[float]:
    """Return together_wall_time / cerebras_wall_time when both fully succeeded."""
    if cerebras_result.error or together_result.error:
        return None
    if cerebras_result.wall_time_seconds <= 0:
        return None
    return together_result.wall_time_seconds / cerebras_result.wall_time_seconds