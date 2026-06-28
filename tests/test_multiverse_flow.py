from src.graph.multiverse_graph import run_multiverse_guard, run_multiverse_guard_report
from src.models.schemas import FinalIncidentReport, IncidentInput, UniverseResult
from src.utils.cerebras_client import CerebrasClient


def sample_incident() -> IncidentInput:
    return IncidentInput(
        logs="""
        checkout-api v2.18.0 deploy promoted to 100%.
        checkout 5xx rate rises above 12%.
        database pool active connections pinned at 100/100.
        payment_authorize retries appear, but provider status is green.
        Redis hit rate slightly lower and checkout_recommendations_v2 flag enabled.
        """.strip(),
        image_description="Dashboard shows deploy marker, latency spike, 5xx spike, and DB pool saturation.",
    )


def test_run_multiverse_guard_report_returns_final_incident_report():
    report = run_multiverse_guard_report(sample_incident(), client=CerebrasClient(mock=True))

    assert isinstance(report, FinalIncidentReport)
    assert report.winning_universe
    assert report.winning_universe == "U-1"


def test_sequential_flow_returns_exactly_four_universe_results():
    state = run_multiverse_guard(sample_incident(), client=CerebrasClient(mock=True), use_parallel=False)

    assert len(state["universe_results"]) == 4
    assert [result.universe_id for result in state["universe_results"]] == ["U-1", "U-2", "U-3", "U-4"]
    assert all(isinstance(result, UniverseResult) for result in state["universe_results"])


def test_parallel_flow_returns_exactly_four_universe_results():
    state = run_multiverse_guard(sample_incident(), client=CerebrasClient(mock=True), use_parallel=True)

    assert len(state["universe_results"]) == 4
    assert {result.universe_id for result in state["universe_results"]} == {"U-1", "U-2", "U-3", "U-4"}
    assert state["use_parallel"] is True


def test_report_contains_winning_universe_and_ranked_universes():
    state = run_multiverse_guard(sample_incident(), client=CerebrasClient(mock=True), use_parallel=False)
    report = state["final_report"]

    assert report is not None
    assert report.winning_universe
    assert len(report.ranked_universes) == 4
    assert report.ranked_universes[0].universe_id == report.winning_universe


def test_each_universe_has_action_rollback_and_missing_evidence():
    state = run_multiverse_guard(sample_incident(), client=CerebrasClient(mock=True), use_parallel=True)

    for result in state["universe_results"]:
        assert result.recommended_action.strip()
        assert result.rollback.strip()
        assert isinstance(result.missing_evidence, list)


def test_timing_metrics_are_present():
    state = run_multiverse_guard(sample_incident(), client=CerebrasClient(mock=True), use_parallel=False)

    assert state["total_elapsed_ms"] >= 0
    assert len(state["timing_events"]) >= 7
    assert all("agent" in event for event in state["timing_events"])
