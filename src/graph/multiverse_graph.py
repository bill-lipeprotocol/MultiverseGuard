from __future__ import annotations

import logging
import operator
import time
from types import SimpleNamespace
from typing import Annotated, Any, Type, TypedDict

try:
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Send

    LANGGRAPH_AVAILABLE = True
except ModuleNotFoundError:
    END = START = StateGraph = None  # type: ignore[assignment]
    LANGGRAPH_AVAILABLE = False

    class Send:  # type: ignore[no-redef]
        def __init__(self, node: str, arg: dict[str, Any]) -> None:
            self.node = node
            self.arg = arg

from src.models.schemas import (
    FinalIncidentReport,
    Hypothesis,
    IncidentInput,
    UniverseResult,
    VisionReport,
)
from src.utils.cerebras_client import CerebrasClient, CerebrasClientError

logger = logging.getLogger(__name__)

# Hard demo invariant: MultiverseGuard always runs exactly four universes.
DEMO_UNIVERSE_COUNT = 4


def _get_universe_id(obj: Any) -> str:
    """Extract universe_id from a Pydantic model or dict."""
    if isinstance(obj, dict):
        universe_id = obj.get("universe_id")
    else:
        universe_id = getattr(obj, "universe_id", None)

    if not universe_id:
        raise CerebrasClientError(
            f"Unable to extract universe_id from object of type {type(obj).__name__}"
        )

    return str(universe_id)


def _hypothesis_universe_id(hypothesis: Hypothesis) -> str:
    """Map a generated hypothesis to its universe branch id (H-n -> U-n)."""
    return str(hypothesis.hypothesis_id).replace("H-", "U-")


def validate_generated_universes(universes: list[Any]) -> list[Any]:
    """Ensure the supervisor generated exactly the required demo universe count."""
    universe_ids = [_get_universe_id(universe) for universe in universes]
    logger.info("Generated universe IDs: %s", universe_ids)

    if len(universes) != DEMO_UNIVERSE_COUNT:
        raise CerebrasClientError(
            f"Expected supervisor to generate {DEMO_UNIVERSE_COUNT} universes, "
            f"but got {len(universes)}. "
            f"Generated universe IDs: {universe_ids}"
        )

    if len(set(universe_ids)) != len(universe_ids):
        raise CerebrasClientError(
            f"Supervisor generated duplicate universe IDs: {universe_ids}"
        )

    return universes


def validate_completed_branches(branch_results: list[Any]) -> list[Any]:
    """Ensure exactly four universe branches completed before final synthesis."""
    branch_ids = [_get_universe_id(branch) for branch in branch_results]
    logger.info("Completed branch IDs: %s", branch_ids)

    if len(branch_results) != DEMO_UNIVERSE_COUNT:
        raise CerebrasClientError(
            f"Expected {DEMO_UNIVERSE_COUNT} completed universe branches, "
            f"but got {len(branch_results)}. "
            f"Completed universe IDs: {branch_ids}"
        )

    if len(set(branch_ids)) != len(branch_ids):
        raise CerebrasClientError(
            f"Duplicate completed universe branch IDs: {branch_ids}"
        )

    return branch_results


def normalize_final_report(report: FinalIncidentReport, branch_results: list[Any]) -> FinalIncidentReport:
    """Enforce final synthesis invariants and sort ranked universes by confidence.

    - exactly four ranked universes
    - every completed universe appears exactly once
    - no unexpected universe IDs are present
    - no duplicate universe IDs are present
    - ranked universes are sorted by confidence descending
    - winning universe is aligned to the top-ranked universe
    """
    expected_ids = {_get_universe_id(branch) for branch in branch_results}

    if len(branch_results) != DEMO_UNIVERSE_COUNT:
        raise CerebrasClientError(
            f"Expected {DEMO_UNIVERSE_COUNT} branch results before final normalization, "
            f"but got {len(branch_results)}. "
            f"Branch IDs: {sorted(expected_ids)}"
        )

    ranked_universes = getattr(report, "ranked_universes", None)

    if ranked_universes is None:
        raise CerebrasClientError(
            "Final synthesis response does not contain ranked_universes."
        )

    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    actual_ids: set[str] = set()

    for ranked_universe in ranked_universes:
        universe_id = _get_universe_id(ranked_universe)

        if universe_id in seen_ids:
            duplicate_ids.add(universe_id)

        seen_ids.add(universe_id)
        actual_ids.add(universe_id)

    missing_ids = expected_ids - actual_ids
    extra_ids = actual_ids - expected_ids

    problems: list[str] = []
    if len(ranked_universes) != DEMO_UNIVERSE_COUNT:
        ranked_ids = sorted(actual_ids) + sorted(duplicate_ids)
        problems.append(
            f"Expected {DEMO_UNIVERSE_COUNT} ranked universes, "
            f"but got {len(ranked_universes)}. Ranked universe IDs: {ranked_ids}"
        )
    if missing_ids:
        problems.append(f"Missing universe IDs: {sorted(missing_ids)}")
    if extra_ids:
        problems.append(f"Unexpected universe IDs: {sorted(extra_ids)}")
    if duplicate_ids:
        problems.append(f"Duplicate universe IDs: {sorted(duplicate_ids)}")

    if problems:
        raise CerebrasClientError(
            "Final synthesis universe mismatch. " + " ".join(problems) + "."
        )

    sorted_ranked_universes = sorted(
        ranked_universes,
        key=lambda universe: getattr(universe, "confidence", 0.0),
        reverse=True,
    )
    winning_universe = _get_universe_id(sorted_ranked_universes[0])
    ranked_ids = [_get_universe_id(u) for u in sorted_ranked_universes]
    logger.info("Final ranked universe IDs: %s", ranked_ids)
    logger.info("Final confidence-sorted order: %s", ranked_ids)

    if hasattr(report, "model_copy"):
        return report.model_copy(
            update={
                "ranked_universes": sorted_ranked_universes,
                "winning_universe": winning_universe,
            }
        )

    if hasattr(report, "copy"):
        return report.copy(
            update={
                "ranked_universes": sorted_ranked_universes,
                "winning_universe": winning_universe,
            }
        )

    report.ranked_universes = sorted_ranked_universes
    report.winning_universe = winning_universe
    return report


def _repair_prompt_suffix(expected_ids: list[str]) -> str:
    return (
        "\n\nRepair the final incident report. The previous response violated "
        "the multiverse completeness invariants.\n\n"
        f"Required universe count: {DEMO_UNIVERSE_COUNT}\n"
        f"Required universe IDs: {expected_ids}\n\n"
        "Rules:\n"
        f"- Return exactly {DEMO_UNIVERSE_COUNT} ranked_universes entries.\n"
        "- Return exactly one ranked_universes entry for each required universe_id.\n"
        "- Do not omit any required universe_id.\n"
        "- Do not add any universe_id that is not in the required list.\n"
        "- Do not duplicate universe IDs.\n"
        "- Sort ranked_universes by confidence descending.\n"
        "- Return only valid JSON matching the requested schema.\n"
    )


def synthesize_with_repair(
    client: CerebrasClient,
    *,
    schema: Type[FinalIncidentReport],
    system_prompt: str,
    user_prompt: str,
    branch_results: list[Any],
    initial_max_tokens: int = 6000,
    repair_max_tokens: int = 9000,
) -> tuple[FinalIncidentReport, dict[str, Any], bool]:
    """Run final synthesis, validate completeness/order, retry once on mismatch."""
    logger.info("Requested universe count: %s", DEMO_UNIVERSE_COUNT)
    branch_results = validate_completed_branches(branch_results)
    expected_ids = sorted(_get_universe_id(branch) for branch in branch_results)

    try:
        report, timing = client.structured_output(
            schema=schema,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_completion_tokens=initial_max_tokens,
        )
        normalized = normalize_final_report(report, branch_results)
        logger.info("Final synthesis repair retry triggered: %s", False)
        timing = {**timing, "repair_triggered": False}
        return normalized, timing, False
    except CerebrasClientError as exc:
        error_text = str(exc)

        repairable_markers = [
            "Final synthesis universe mismatch",
            "Expected 4 ranked universes",
            "ranked_universes",
            "Missing universe IDs",
            "Unexpected universe IDs",
            "Duplicate universe IDs",
        ]

        if not any(marker in error_text for marker in repairable_markers):
            raise

        logger.warning("Final synthesis incomplete (%s); retrying once with repair prompt", error_text)
        repair_messages_prompt = user_prompt + _repair_prompt_suffix(expected_ids)

        repaired_report, timing = client.structured_output(
            schema=schema,
            system_prompt=system_prompt,
            user_prompt=repair_messages_prompt,
            max_completion_tokens=repair_max_tokens,
        )
        normalized = normalize_final_report(repaired_report, branch_results)
        logger.info("Final synthesis repair retry triggered: %s", True)
        timing = {**timing, "repair_triggered": True}
        return normalized, timing, True


class MultiverseState(TypedDict):
    incident: IncidentInput
    vision_report: VisionReport | None
    hypotheses: list[Hypothesis]
    universe_results: list[UniverseResult]
    final_report: FinalIncidentReport | None
    timing_events: list[dict[str, Any]]
    total_elapsed_ms: float
    use_parallel: bool


class UniverseBranchState(TypedDict, total=False):
    incident: IncidentInput
    vision_report: VisionReport
    hypothesis: Hypothesis
    universe_results: Annotated[list[UniverseResult], operator.add]
    timing_events: Annotated[list[dict[str, Any]], operator.add]


EVIDENCE_SYSTEM_PROMPT = """You extract observable incident evidence from logs and image context.
Do not decide root cause. Return only the requested structured output."""

HYPOTHESIS_SYSTEM_PROMPT = """You generate one clear, testable incident hypothesis.
Return only the requested structured output."""

UNIVERSE_SYSTEM_PROMPT = """You investigate one assigned universe.
Use only the provided incident evidence and hypothesis. Return confidence, evidence,
recommended action, rollback, and missing evidence as structured output."""

SYNTHESIS_SYSTEM_PROMPT = """You rank four universe investigations and synthesize the final incident response.
Return only the requested structured output."""


DEFAULT_HYPOTHESIS_SEEDS = [
    ("H-1", "Recent checkout release caused database pool exhaustion."),
    ("H-2", "Payment gateway latency cascaded into checkout failures."),
    ("H-3", "Cache pressure or thundering herd saturated the database."),
    ("H-4", "Feature flag introduced an expensive checkout path."),
]


def initial_state(incident: IncidentInput, *, use_parallel: bool = False) -> MultiverseState:
    return {
        "incident": incident,
        "vision_report": None,
        "hypotheses": [],
        "universe_results": [],
        "final_report": None,
        "timing_events": [],
        "total_elapsed_ms": 0.0,
        "use_parallel": use_parallel,
    }


def extract_evidence(state: MultiverseState, client: CerebrasClient) -> MultiverseState:
    incident = state["incident"]
    prompt = f"""Incident logs:
{incident.logs}

Image description:
{incident.image_description or "No image description provided yet."}

Extract a concise incident summary and key observations.
"""
    report, timing = client.structured_output(
        schema=VisionReport,
        system_prompt=EVIDENCE_SYSTEM_PROMPT,
        user_prompt=prompt,
        image_data_uri=incident.image_data_uri,
    )
    state["vision_report"] = report
    state["timing_events"].append({"agent": "extract_evidence", **timing})
    return state


def generate_hypotheses(state: MultiverseState, client: CerebrasClient) -> MultiverseState:
    vision_report = state["vision_report"]
    if vision_report is None:
        raise ValueError("Cannot generate hypotheses before evidence extraction.")

    hypotheses: list[Hypothesis] = []
    for hypothesis_id, description in DEFAULT_HYPOTHESIS_SEEDS:
        prompt = f"""Evidence summary:
{vision_report.summary}

Key observations:
{chr(10).join(vision_report.key_observations)}

Create hypothesis {hypothesis_id}: {description}
"""
        hypothesis, timing = client.structured_output(
            schema=Hypothesis,
            system_prompt=HYPOTHESIS_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        hypotheses.append(Hypothesis(hypothesis_id=hypothesis_id, description=hypothesis.description or description))
        state["timing_events"].append({"agent": f"generate_{hypothesis_id}", **timing})

    # Hard demo invariant: the supervisor must hand off exactly four universes.
    validate_generated_universes(
        [SimpleNamespace(universe_id=_hypothesis_universe_id(h)) for h in hypotheses]
    )
    state["hypotheses"] = hypotheses
    return state


def investigate_universe(
    incident: IncidentInput,
    vision_report: VisionReport,
    hypothesis: Hypothesis,
    client: CerebrasClient,
) -> tuple[UniverseResult, dict[str, Any]]:
    universe_id = hypothesis.hypothesis_id.replace("H-", "U-")
    prompt = f"""Universe ID: {universe_id}
Hypothesis: {hypothesis.description}

Incident logs:
{incident.logs}

Image description:
{incident.image_description or "No image description provided."}

Evidence summary:
{vision_report.summary}

Key observations:
{chr(10).join(vision_report.key_observations)}

Investigate this universe only.
"""
    result, timing = client.structured_output(
        schema=UniverseResult,
        system_prompt=UNIVERSE_SYSTEM_PROMPT,
        user_prompt=prompt,
    )
    if result.universe_id != universe_id:
        result = result.model_copy(update={"universe_id": universe_id, "hypothesis": hypothesis.description})
    return result, timing


def run_universes_sequential(state: MultiverseState, client: CerebrasClient) -> MultiverseState:
    vision_report = state["vision_report"]
    if vision_report is None:
        raise ValueError("Cannot run universes before evidence extraction.")

    results: list[UniverseResult] = []
    for hypothesis in state["hypotheses"]:
        result, timing = investigate_universe(state["incident"], vision_report, hypothesis, client)
        results.append(result)
        state["timing_events"].append({"agent": f"universe_{result.universe_id}", **timing})

    state["universe_results"] = results
    return state


def run_universes_parallel(state: MultiverseState, client: CerebrasClient) -> MultiverseState:
    """Run universe branches with LangGraph Send when available."""
    vision_report = state["vision_report"]
    if vision_report is None:
        raise ValueError("Cannot run universes before evidence extraction.")
    if not LANGGRAPH_AVAILABLE:
        state["timing_events"].append(
            {
                "agent": "parallel_fallback",
                "mode": "fallback",
                "model": "local",
                "elapsed_ms": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "tokens_per_second": 0,
            }
        )
        return run_universes_sequential(state, client)

    def fanout(_: UniverseBranchState) -> dict[str, Any]:
        return {}

    def dispatch(branch_state: UniverseBranchState) -> list[Send]:
        return [
            Send(
                "run_universe_branch",
                {
                    "incident": branch_state["incident"],
                    "vision_report": branch_state["vision_report"],
                    "hypothesis": hypothesis,
                    "universe_results": [],
                    "timing_events": [],
                },
            )
            for hypothesis in state["hypotheses"]
        ]

    def run_universe_branch(branch_state: UniverseBranchState) -> UniverseBranchState:
        result, timing = investigate_universe(
            branch_state["incident"],
            branch_state["vision_report"],
            branch_state["hypothesis"],
            client,
        )
        return {
            "universe_results": [result],
            "timing_events": [{"agent": f"universe_{result.universe_id}", **timing}],
        }

    graph = StateGraph(UniverseBranchState)
    graph.add_node("fanout", fanout)
    graph.add_node("run_universe_branch", run_universe_branch)
    graph.add_edge(START, "fanout")
    graph.add_conditional_edges("fanout", dispatch)
    graph.add_edge("run_universe_branch", END)

    compiled = graph.compile()
    result = compiled.invoke(
        {
            "incident": state["incident"],
            "vision_report": vision_report,
            "universe_results": [],
            "timing_events": [],
        }
    )
    state["universe_results"] = result.get("universe_results", [])
    state["timing_events"].extend(result.get("timing_events", []))
    return state


def synthesize_report(state: MultiverseState, client: CerebrasClient) -> MultiverseState:
    branch_results = state["universe_results"]
    expected_universe_ids = sorted(_get_universe_id(branch) for branch in branch_results)

    universe_lines = []
    for result in branch_results:
        universe_lines.append(
            f"{result.universe_id}: {result.hypothesis} | confidence={result.confidence} | action={result.recommended_action}"
        )

    prompt = f"""Incident logs:
{state["incident"].logs}

Universe investigations:
{chr(10).join(universe_lines)}

Expected universe IDs:
{expected_universe_ids}

Rank all four universes and recommend next steps.
"""
    report, timing, repair_triggered = synthesize_with_repair(
        client=client,
        schema=FinalIncidentReport,
        system_prompt=SYNTHESIS_SYSTEM_PROMPT,
        user_prompt=prompt,
        branch_results=branch_results,
        initial_max_tokens=6000,
        repair_max_tokens=9000,
    )
    state["final_report"] = report
    state["timing_events"].append(
        {"agent": "synthesize_report", "repair_triggered": repair_triggered, **timing}
    )
    return state


def run_multiverse_guard(
    incident: IncidentInput,
    *,
    client: CerebrasClient | None = None,
    use_parallel: bool = False,
) -> MultiverseState:
    """Run the 4-universe flow and return state with a Pydantic final report."""
    started = time.perf_counter()
    active_client = client or CerebrasClient()
    state = initial_state(incident, use_parallel=use_parallel)
    state = extract_evidence(state, active_client)
    state = generate_hypotheses(state, active_client)

    if state["use_parallel"]:
        state = run_universes_parallel(state, active_client)
    else:
        state = run_universes_sequential(state, active_client)

    # Fail fast if branch execution did not complete exactly four universes.
    validate_completed_branches(state["universe_results"])

    state = synthesize_report(state, active_client)
    state["total_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return state


def run_multiverse_guard_report(
    incident: IncidentInput,
    *,
    client: CerebrasClient | None = None,
    use_parallel: bool = False,
) -> FinalIncidentReport:
    """Convenience wrapper for callers that only need the Pydantic final report."""
    state = run_multiverse_guard(incident, client=client, use_parallel=use_parallel)
    if state["final_report"] is None:
        raise ValueError("MultiverseGuard completed without a final report.")
    return state["final_report"]


