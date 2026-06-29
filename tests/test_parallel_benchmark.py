import pytest

from src.utils.speed_benchmark import (
    BenchmarkResult,
    ParallelBenchmarkResult,
    calculate_parallel_speedup,
    run_cerebras_parallel_benchmark,
    run_parallel_openai_compatible_benchmark,
    run_together_parallel_benchmark,
)


def _call(provider, model, latency, comp_tok, error=None):
    return BenchmarkResult(
        provider=provider,
        model=model,
        latency_seconds=latency,
        prompt_tokens=10,
        completion_tokens=comp_tok,
        total_tokens=(10 + comp_tok) if comp_tok is not None else None,
        tokens_per_second=(comp_tok / latency) if comp_tok and latency else None,
        output_preview="ok" if not error else "",
        error=error,
    )


# 1. Missing key parallel result returns a friendly error (no live call).
def test_missing_together_key_parallel_returns_error(monkeypatch):
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    result = run_together_parallel_benchmark()
    assert isinstance(result, ParallelBenchmarkResult)
    assert result.error is not None
    assert "Together AI" in result.error
    assert result.call_count == 4
    assert result.completed_count == 0
    assert result.errored_count == 4
    assert result.wall_time_seconds == 0.0
    assert result.aggregate_tokens_per_second is None
    assert result.results == []


def test_missing_cerebras_key_parallel_returns_error(monkeypatch):
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    result = run_cerebras_parallel_benchmark()
    assert result.error is not None
    assert "Cerebras" in result.error
    assert result.call_count == 4
    assert result.errored_count == 4


# 2. Parallel speedup calculation is correct.
def test_calculate_parallel_speedup_correct():
    c = ParallelBenchmarkResult("Cerebras", "gemma-4-31b", 1.0, 4, 4, 0, 1.0, 1.5, 800, 800.0, [], None)
    t = ParallelBenchmarkResult("Together AI", "zai-org/GLM-5.2", 5.0, 4, 4, 0, 4.0, 5.0, 800, 160.0, [], None)
    assert calculate_parallel_speedup(c, t) == 5.0


# 3. Parallel speedup returns None if either result has an error.
def test_calculate_parallel_speedup_none_when_cerebras_error():
    c = ParallelBenchmarkResult("Cerebras", "gemma-4-31b", 1.0, 4, 4, 0, 1.0, 1.5, 800, 800.0, [], "err")
    t = ParallelBenchmarkResult("Together AI", "zai-org/GLM-5.2", 5.0, 4, 4, 0, 4.0, 5.0, 800, 160.0, [], None)
    assert calculate_parallel_speedup(c, t) is None


def test_calculate_parallel_speedup_none_when_together_error():
    c = ParallelBenchmarkResult("Cerebras", "gemma-4-31b", 1.0, 4, 4, 0, 1.0, 1.5, 800, 800.0, [], None)
    t = ParallelBenchmarkResult("Together AI", "zai-org/GLM-5.2", 5.0, 4, 4, 0, 4.0, 5.0, 800, 160.0, [], "err")
    assert calculate_parallel_speedup(c, t) is None


def test_calculate_parallel_speedup_none_when_zero_wall_time():
    c = ParallelBenchmarkResult("Cerebras", "gemma-4-31b", 0.0, 4, 4, 0, 1.0, 1.5, 800, None, [], None)
    t = ParallelBenchmarkResult("Together AI", "zai-org/GLM-5.2", 5.0, 4, 4, 0, 4.0, 5.0, 800, 160.0, [], None)
    assert calculate_parallel_speedup(c, t) is None


# 4 & 5. Completed/errored counts and aggregate tokens/sec computed correctly,
#        using a stubbed single-call function (no live network).
def test_parallel_counts_and_aggregate(monkeypatch):
    import src.utils.speed_benchmark as sb

    def fake_single(provider, base_url, api_key, model, prompt, max_tokens, temperature):
        # vary latency a bit per call to test max/avg
        idx = sb.PARALLEL_BENCHMARK_PROMPTS.index(prompt)
        return _call(provider, model, 1.0 + idx * 0.5, 200)

    monkeypatch.setattr(sb, "run_openai_compatible_benchmark", fake_single)

    result = run_parallel_openai_compatible_benchmark(
        provider="Cerebras",
        base_url="https://example/v1",
        api_key="fake-key",
        model="gemma-4-31b",
    )

    assert result.error is None
    assert result.call_count == 4
    assert result.completed_count == 4
    assert result.errored_count == 0
    assert len(result.results) == 4
    # latencies 1.0, 1.5, 2.0, 2.5 -> avg 1.75, max 2.5
    assert result.average_latency_seconds == pytest.approx(1.75)
    assert result.max_latency_seconds == pytest.approx(2.5)
    assert result.total_completion_tokens == 800
    # aggregate tokens/sec = total completion tokens / measured wall time
    assert result.wall_time_seconds > 0
    assert result.aggregate_tokens_per_second == pytest.approx(800 / result.wall_time_seconds)


def test_parallel_partial_failure_counts(monkeypatch):
    import src.utils.speed_benchmark as sb

    def fake_single(provider, base_url, api_key, model, prompt, max_tokens, temperature):
        idx = sb.PARALLEL_BENCHMARK_PROMPTS.index(prompt)
        if idx == 1:
            return _call(provider, model, 1.0, None, error="boom")
        return _call(provider, model, 1.0, 200)

    monkeypatch.setattr(sb, "run_openai_compatible_benchmark", fake_single)

    result = run_parallel_openai_compatible_benchmark(
        provider="Together AI",
        base_url="https://example/v1",
        api_key="fake-key",
        model="zai-org/GLM-5.2",
    )

    assert result.completed_count == 3
    assert result.errored_count == 1
    assert result.call_count == 4
    assert result.error == "1 of 4 calls failed."
    assert result.total_completion_tokens == 600  # 3 * 200


def test_parallel_benchmark_uses_four_variant_prompts():
    import src.utils.speed_benchmark as sb
    assert len(sb.PARALLEL_BENCHMARK_PROMPTS) == 4
    # each variant appends a distinct focus universe
    assert all(p.startswith(sb.BENCHMARK_PROMPT) for p in sb.PARALLEL_BENCHMARK_PROMPTS)
    focuses = [p.split("Focus universe:", 1)[1].strip() for p in sb.PARALLEL_BENCHMARK_PROMPTS]
    assert len(set(focuses)) == 4
