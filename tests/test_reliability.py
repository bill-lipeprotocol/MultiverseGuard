from types import SimpleNamespace

import pytest

from src.graph.multiverse_graph import (
    DEMO_UNIVERSE_COUNT,
    normalize_final_report,
    synthesize_with_repair,
    validate_completed_branches,
    validate_generated_universes,
)
from src.models.schemas import FinalIncidentReport, UniverseResult
from src.utils.cerebras_client import CerebrasClientError


def _u(universe_id: str, confidence: float = 0.5) -> UniverseResult:
    return UniverseResult(
        universe_id=universe_id,
        hypothesis=f"hypothesis {universe_id}",
        confidence=confidence,
        evidence=["evidence"],
        recommended_action="action",
        rollback="rollback",
        missing_evidence=[],
    )


def _ns(universe_id: str):
    return SimpleNamespace(universe_id=universe_id)


def _report(ranked) -> FinalIncidentReport:
    # Bypass the min_length=4 constraint so we can exercise the application-level
    # invariants with incomplete payloads (missing/duplicate/extra universes).
    data = {
        "winning_universe": ranked[0].universe_id if ranked else "U-1",
        "ranked_universes": list(ranked),
        "overall_summary": "summary",
        "recommended_next_steps": ["step"],
    }
    return FinalIncidentReport.model_construct(**data)


# --- Test A: supervisor generation requires exactly four universes ---
def test_validate_generated_universes_rejects_three():
    with pytest.raises(CerebrasClientError) as exc:
        validate_generated_universes([_ns("u1"), _ns("u2"), _ns("u3")])
    assert "Expected supervisor to generate 4 universes" in str(exc.value)


def test_validate_generated_universes_accepts_four():
    universes = [_ns("u1"), _ns("u2"), _ns("u3"), _ns("u4")]
    assert validate_generated_universes(universes) is universes


# --- Test B: completed branches require exactly four results ---
def test_validate_completed_branches_rejects_three():
    with pytest.raises(CerebrasClientError) as exc:
        validate_completed_branches([_u("u1"), _u("u2"), _u("u3")])
    assert "Expected 4 completed universe branches" in str(exc.value)


def test_validate_completed_branches_accepts_four():
    branches = [_u("u1"), _u("u2"), _u("u3"), _u("u4")]
    assert validate_completed_branches(branches) is branches


# --- Test C: final report sorts ranked universes by confidence descending ---
def test_normalize_final_report_sorts_by_confidence_descending():
    branches = [_u("u1"), _u("u2"), _u("u3"), _u("u4")]
    report = _report([
        _u("u1", 0.40),
        _u("u3", 0.90),
        _u("u2", 0.70),
        _u("u4", 0.55),
    ])
    normalized = normalize_final_report(report, branches)
    assert [u.universe_id for u in normalized.ranked_universes] == ["u3", "u2", "u4", "u1"]
    assert normalized.winning_universe == "u3"


# --- Test D: missing universe raises clear error containing the missing id ---
def test_normalize_final_report_missing_universe():
    branches = [_u("u1"), _u("u2"), _u("u3"), _u("u4")]
    report = _report([_u("u1"), _u("u2"), _u("u3")])
    with pytest.raises(CerebrasClientError) as exc:
        normalize_final_report(report, branches)
    assert ("Expected 4 ranked universes" in str(exc.value)) or ("Missing universe IDs" in str(exc.value))
    assert "u4" in str(exc.value)


# --- Test E: duplicate universe raises clear error ---
def test_normalize_final_report_duplicate_universe():
    branches = [_u("u1"), _u("u2"), _u("u3"), _u("u4")]
    report = _report([_u("u1"), _u("u2"), _u("u3"), _u("u3")])
    with pytest.raises(CerebrasClientError) as exc:
        normalize_final_report(report, branches)
    assert "Duplicate universe IDs" in str(exc.value)


# --- Test F: extra universe raises clear error containing the extra id ---
def test_normalize_final_report_extra_universe():
    branches = [_u("u1"), _u("u2"), _u("u3"), _u("u4")]
    report = _report([_u("u1"), _u("u2"), _u("u3"), _u("u999")])
    with pytest.raises(CerebrasClientError) as exc:
        normalize_final_report(report, branches)
    assert ("Unexpected universe IDs" in str(exc.value)) or ("mismatch" in str(exc.value))
    assert "u999" in str(exc.value)


# --- Test G: repair path retries once and returns complete sorted report ---
class _StubClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def structured_output(self, *, schema, system_prompt, user_prompt, max_completion_tokens, **kwargs):
        self.calls += 1
        response = self._responses[self.calls - 1]
        if isinstance(response, Exception):
            raise response
        return response, {"mode": "live", "elapsed_ms": 1.0, "input_tokens": 1, "output_tokens": 1, "tokens_per_second": 1.0}


def test_synthesize_with_repair_retries_once_on_missing_universe():
    branches = [_u("u1"), _u("u2"), _u("u3"), _u("u4")]
    first = _report([_u("u1"), _u("u2"), _u("u3")])  # missing u4 -> mismatch
    second = _report([_u("u1", 0.40), _u("u2", 0.70), _u("u3", 0.90), _u("u4", 0.55)])
    client = _StubClient([first, second])

    report, timing, repair_triggered = synthesize_with_repair(
        client=client,
        schema=FinalIncidentReport,
        system_prompt="sys",
        user_prompt="prompt",
        branch_results=branches,
    )

    assert client.calls == 2
    assert repair_triggered is True
    assert timing["repair_triggered"] is True
    assert [u.universe_id for u in report.ranked_universes] == ["u3", "u2", "u4", "u1"]
    assert report.winning_universe == "u3"


# --- Test H: repair failure raises clear error and does not loop ---
def test_synthesize_with_repair_failure_raises_and_does_not_loop():
    branches = [_u("u1"), _u("u2"), _u("u3"), _u("u4")]
    incomplete = _report([_u("u1"), _u("u2"), _u("u3")])
    client = _StubClient([incomplete, incomplete])

    with pytest.raises(CerebrasClientError) as exc:
        synthesize_with_repair(
            client=client,
            schema=FinalIncidentReport,
            system_prompt="sys",
            user_prompt="prompt",
            branch_results=branches,
        )

    assert client.calls == 2  # one initial + one repair, no third attempt
    assert "4" in str(exc.value)


# --- Test: non-repairable error is not retried ---
def test_synthesize_with_repair_does_not_retry_non_repairable_error():
    branches = [_u("u1"), _u("u2"), _u("u3"), _u("u4")]
    client = _StubClient([CerebrasClientError("response was truncated (finish_reason=length)")])

    with pytest.raises(CerebrasClientError) as exc:
        synthesize_with_repair(
            client=client,
            schema=FinalIncidentReport,
            system_prompt="sys",
            user_prompt="prompt",
            branch_results=branches,
        )

    assert client.calls == 1
    assert "truncated" in str(exc.value)


# --- Test: completed branch count guard in the full graph (mock) ---
def test_mock_full_flow_produces_exactly_four_ranked_universes_sorted():
    from src.graph.multiverse_graph import run_multiverse_guard
    from src.models.schemas import IncidentInput
    from src.utils.cerebras_client import CerebrasClient

    state = run_multiverse_guard(
        IncidentInput(logs="checkout deploy then 5xx and db pool 100/100"),
        client=CerebrasClient(mock=True),
        use_parallel=False,
    )
    report = state["final_report"]
    assert len(report.ranked_universes) == DEMO_UNIVERSE_COUNT
    confidences = [u.confidence for u in report.ranked_universes]
    assert confidences == sorted(confidences, reverse=True)
    assert {u.universe_id for u in report.ranked_universes} == {"U-1", "U-2", "U-3", "U-4"}
    assert report.winning_universe == report.ranked_universes[0].universe_id
