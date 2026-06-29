from src.utils.speed_benchmark import (
    BenchmarkResult,
    calculate_speedup,
    result_to_display_dict,
    run_cerebras_benchmark,
    run_together_benchmark,
)


def _result(provider, model, latency, comp_tok, error=None):
    tps = comp_tok / latency if comp_tok and latency else None
    return BenchmarkResult(
        provider=provider,
        model=model,
        latency_seconds=latency,
        prompt_tokens=10,
        completion_tokens=comp_tok,
        total_tokens=(10 + comp_tok) if comp_tok else None,
        tokens_per_second=tps,
        output_preview="preview" if not error else "",
        error=error,
    )


# 1. Missing Together key returns a BenchmarkResult with an error (no live call).
def test_missing_together_key_returns_error_result(monkeypatch):
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    result = run_together_benchmark()
    assert isinstance(result, BenchmarkResult)
    assert result.error is not None
    assert "Together AI" in result.error
    assert result.latency_seconds == 0.0
    assert result.tokens_per_second is None


def test_missing_cerebras_key_returns_error_result(monkeypatch):
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    result = run_cerebras_benchmark()
    assert isinstance(result, BenchmarkResult)
    assert result.error is not None
    assert "Cerebras" in result.error


# 2. calculate_speedup returns correct multiplier.
def test_calculate_speedup_returns_multiplier():
    cerebras = _result("Cerebras", "gemma-4-31b", 1.0, 200)
    together = _result("Together AI", "zai-org/GLM-5.2", 4.0, 200)
    assert calculate_speedup(cerebras, together) == 4.0


# 3. calculate_speedup returns None if either result has an error.
def test_calculate_speedup_none_when_cerebras_errors():
    cerebras = _result("Cerebras", "gemma-4-31b", 1.0, 200, error="boom")
    together = _result("Together AI", "zai-org/GLM-5.2", 4.0, 200)
    assert calculate_speedup(cerebras, together) is None


def test_calculate_speedup_none_when_together_errors():
    cerebras = _result("Cerebras", "gemma-4-31b", 1.0, 200)
    together = _result("Together AI", "zai-org/GLM-5.2", 4.0, 200, error="boom")
    assert calculate_speedup(cerebras, together) is None


def test_calculate_speedup_none_when_zero_latency():
    cerebras = _result("Cerebras", "gemma-4-31b", 0.0, 0)
    together = _result("Together AI", "zai-org/GLM-5.2", 4.0, 200)
    assert calculate_speedup(cerebras, together) is None


# 4. result_to_display_dict does not expose API keys.
def test_display_dict_has_no_key_fields():
    result = _result("Cerebras", "gemma-4-31b", 1.0, 200)
    view = result_to_display_dict(result)
    assert "api_key" not in view
    assert "key" not in view
    assert set(view.keys()) == {
        "provider",
        "model",
        "latency_seconds",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "tokens_per_second",
        "error",
    }
    # the serialized view must not contain any secret-like content
    import json
    blob = json.dumps(view)
    assert "sk-" not in blob
    assert "csk-" not in blob


def test_display_dict_rounds_values():
    result = BenchmarkResult(
        provider="Together AI",
        model="zai-org/GLM-5.2",
        latency_seconds=4.123456,
        prompt_tokens=10,
        completion_tokens=200,
        total_tokens=210,
        tokens_per_second=48.5111,
        output_preview="x",
        error=None,
    )
    view = result_to_display_dict(result)
    assert view["latency_seconds"] == 4.1235
    assert view["tokens_per_second"] == 48.51
    assert view["model"] == "zai-org/GLM-5.2"


# 5. Existing 4-universe reliability tests still pass (run alongside via pytest).
def test_together_default_model_is_glm_52(monkeypatch):
    # No TOGETHER_MODEL set -> default should be the GLM-5.2 id, and missing key
    # short-circuits before any network call.
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    monkeypatch.delenv("TOGETHER_MODEL", raising=False)
    result = run_together_benchmark()
    assert result.model == "zai-org/GLM-5.2"
