from __future__ import annotations

import base64
import hmac
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.graph.multiverse_graph import DEMO_UNIVERSE_COUNT, LANGGRAPH_AVAILABLE, run_multiverse_guard
from src.models.schemas import IncidentInput
from src.utils.cerebras_client import CerebrasClient
from src.utils.speed_benchmark import (
    calculate_parallel_speedup,
    calculate_speedup,
    run_cerebras_benchmark,
    run_cerebras_parallel_benchmark,
    run_together_benchmark,
    run_together_parallel_benchmark,
)

load_dotenv(ROOT / ".env")

EXAMPLE_PATH = ROOT / "data" / "examples" / "checkout_sev1.md"


def load_example_logs() -> str:
    if EXAMPLE_PATH.exists():
        return EXAMPLE_PATH.read_text(encoding="utf-8")
    return "checkout-api v2.18.0 deploy followed by 5xx spike and db pool 100/100"


def image_to_data_uri(uploaded_file) -> str:
    mime_type = uploaded_file.type or "image/png"
    encoded = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def pct(value: float) -> str:
    return f"{value:.0%}"


st.set_page_config(page_title="MultiverseGuard", page_icon=":shield:", layout="wide")
st.title("MultiverseGuard")
st.caption("4-universe multimodal incident response with Gemma 4 31B on Cerebras")

def configured_access_code() -> str:
    return os.getenv("APP_ACCESS_CODE", "").strip()


def access_verified() -> bool:
    # No configured code -> open local development, never block.
    if not configured_access_code():
        return True
    return bool(st.session_state.get("mg_access_verified", False))


def live_calls_allowed() -> bool:
    return access_verified()


with st.sidebar:
    st.header("Run Settings")
    default_mock = os.getenv("MULTIVERSEGUARD_MOCK", "true").strip().lower() != "false" or not os.getenv("CEREBRAS_API_KEY")
    mock_mode = st.toggle("Mock mode", value=default_mock, help="Keep enabled while developing and rehearsing.")
    use_parallel = st.toggle("Use LangGraph Send", value=False, help="Runs parallel fan-out when LangGraph is available.")
    st.write("Model:", os.getenv("CEREBRAS_MODEL", "gemma-4-31b"))
    st.write("LangGraph:", "available" if LANGGRAPH_AVAILABLE else "not available")
    if st.button("Load demo incident", use_container_width=True):
        st.session_state["logs"] = load_example_logs()
        st.session_state["image_description"] = (
            "Dashboard shows checkout 5xx spike, p95 latency increase, deploy marker, "
            "DB pool at 100/100, and payment retries without confirmed provider outage."
        )

    # Optional access gate: protects live API usage on public deployments.
    if configured_access_code():
        st.divider()
        st.subheader("Access")
        if access_verified():
            st.caption("Live API access: enabled")
        else:
            st.caption("Live Cerebras/Together calls require an access code. Mock mode works without it.")
            entered = st.text_input("Access code", type="password", key="mg_access_code_input")
            if st.button("Unlock live calls", use_container_width=True):
                if hmac.compare_digest(entered, configured_access_code()):
                    st.session_state["mg_access_verified"] = True
                    st.success("Access granted. Live calls are now enabled.")
                else:
                    st.session_state["mg_access_verified"] = False
                    st.error("Incorrect access code.")

left, right = st.columns([0.42, 0.58], gap="large")

with left:
    st.subheader("Multimodal Input")
    st.caption("Incident logs plus an optional dashboard screenshot / image.")
    logs = st.text_area("Logs", value=st.session_state.get("logs", load_example_logs()), height=260)

    st.markdown("**Dashboard Image**")
    uploaded_image = st.file_uploader(
        "Upload PNG or JPG",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
        help="Live mode sends this image to Gemma 4 via a base64 data URI. Mock mode previews it but does not call the API.",
    )
    image_data_uri = image_to_data_uri(uploaded_image) if uploaded_image else None
    if uploaded_image:
        st.image(uploaded_image, caption=uploaded_image.name, use_container_width=True)

    image_description = st.text_area(
        "Optional image / dashboard notes",
        value=st.session_state.get("image_description", ""),
        height=110,
        placeholder="Optional: describe visible chart labels, thresholds, or architecture details.",
    )
    run = st.button("Run MultiverseGuard", type="primary", use_container_width=True)

with right:
    st.subheader("Parallel Multiverse Exploration")
    st.caption("4 hypotheses -> 4 parallel universe branches -> final synthesis by the critic.")
    st.code(
        "Logs + image -> Extract evidence -> Generate 4 hypotheses -> Investigate 4 universes -> Rank final report",
        language="text",
    )
    st.markdown(
        "The demo keeps the layout stable: upload evidence, show four universe cards, then show timing metrics and the final operator recommendation."
    )

if run:
    if not logs.strip():
        st.error("Paste incident logs or load the demo incident first.")
        st.stop()

    incident = IncidentInput(
        logs=logs,
        image_description=image_description or None,
        image_data_uri=image_data_uri,
    )
    client = CerebrasClient(mock=mock_mode)

    # Gate live (non-mock) runs behind the optional access code.
    if not client.mock and not live_calls_allowed():
        st.error("Access code required for live runs. Enter it in the sidebar or enable Mock mode.")
        st.stop()

    with st.spinner("Running 4 universe investigations..."):
        try:
            state = run_multiverse_guard(incident, client=client, use_parallel=use_parallel)
        except Exception as exc:
            st.exception(exc)
            st.stop()

    final_report = state["final_report"]
    universe_results = state["universe_results"]
    timing_events = state["timing_events"]

    if final_report is None:
        st.error("Run completed without a final report.")
        st.stop()

    # Hard demo invariant: never quietly display an incomplete multiverse report.
    if len(universe_results) != DEMO_UNIVERSE_COUNT:
        st.error(
            f"Expected {DEMO_UNIVERSE_COUNT} universes for this demo, but the run "
            f"produced {len(universe_results)}. Please rerun or inspect branch logs."
        )
        st.stop()

    if len(final_report.ranked_universes) != DEMO_UNIVERSE_COUNT:
        st.error(
            f"Expected {DEMO_UNIVERSE_COUNT} ranked universes in the final report, "
            f"but received {len(final_report.ranked_universes)}. Please rerun or inspect branch logs."
        )
        st.stop()

    st.success("Analysis complete")

    # --- Demo Checklist: prove the 4-universe invariants held end-to-end ---
    synthesize_event = next(
        (e for e in timing_events if e.get("agent") == "synthesize_report"),
        {},
    )
    repair_triggered = bool(synthesize_event.get("repair_triggered", False))
    ranked_confidences = [u.confidence for u in final_report.ranked_universes]
    checklist = [
        ("4 universes generated", len(state["hypotheses"]) == DEMO_UNIVERSE_COUNT),
        ("4 branches completed", len(universe_results) == DEMO_UNIVERSE_COUNT),
        ("4 ranked results", len(final_report.ranked_universes) == DEMO_UNIVERSE_COUNT),
        ("Ranked descending", ranked_confidences == sorted(ranked_confidences, reverse=True)),
        (f"Repair triggered: {str(repair_triggered).lower()}", repair_triggered),
    ]
    with st.expander("Demo Checklist", expanded=True):
        for label, ok in checklist:
            mark = "\u2705" if ok else "\u274C"
            st.markdown(f"{mark} {label}")

    # --- Top-line metrics (mode, count, parallelism, image, speed) ---
    live_events = [e for e in timing_events if e.get("mode") == "live"]
    cerebras_speed = max((e.get("tokens_per_second", 0.0) for e in (live_events or timing_events)), default=0.0)
    metric_cols = st.columns(6)
    metric_cols[0].metric("Mode", "Mock" if client.mock else "Live")
    metric_cols[1].metric("Universes", len(universe_results))
    metric_cols[2].metric("Parallel", "On" if use_parallel else "Off")
    metric_cols[3].metric("Image", "Uploaded" if image_data_uri else "Notes only")
    metric_cols[4].metric("Total time", f"{state['total_elapsed_ms']:,.0f} ms")
    metric_cols[5].metric("Cerebras speed", f"{cerebras_speed:,.0f} tok/s")

    # --- Final synthesis: winner, impact, remediation ---
    st.header("Final Incident Report (Final Synthesis)")
    top = final_report.ranked_universes[0]
    st.success(f"Winning universe: {final_report.winning_universe} - {top.hypothesis} ({pct(top.confidence)})")
    st.subheader("Impact Summary")
    st.write(final_report.overall_summary)
    st.subheader("Remediation Plan")
    for step in final_report.recommended_next_steps:
        st.write("-", step)

    st.subheader("Ranked Universes (by confidence, descending)")
    for index, universe in enumerate(final_report.ranked_universes, start=1):
        st.markdown(f"**#{index} {universe.universe_id}** - {pct(universe.confidence)} - {universe.hypothesis}")

    # --- 4 universe cards ---
    st.header(f"{DEMO_UNIVERSE_COUNT} Universe Investigations")
    cards = st.columns(DEMO_UNIVERSE_COUNT)
    for index, universe in enumerate(universe_results):
        with cards[index % DEMO_UNIVERSE_COUNT]:
            st.subheader(universe.universe_id)
            st.caption("Hypothesis")
            st.write(universe.hypothesis)
            st.metric("Confidence", pct(universe.confidence))
            st.markdown("**Evidence**")
            for item in universe.evidence:
                st.write("-", item)
            st.markdown("**Missing Evidence**")
            if universe.missing_evidence:
                for item in universe.missing_evidence:
                    st.write("-", item)
            else:
                st.write("- None listed")
            st.markdown("**Recommended Action**")
            st.write(universe.recommended_action)
            st.markdown("**Rollback**")
            st.write(universe.rollback)

    # --- Cerebras timing / speed metrics ---
    st.header("Cerebras Timing Metrics")
    st.dataframe(timing_events, use_container_width=True)

    with st.expander("Audit JSON"):
        st.json(
            {
                "vision_report": state["vision_report"].model_dump() if state["vision_report"] else None,
                "hypotheses": [item.model_dump() for item in state["hypotheses"]],
                "universe_results": [item.model_dump() for item in universe_results],
                "final_report": final_report.model_dump(),
                "timing_events": timing_events,
                "total_elapsed_ms": state["total_elapsed_ms"],
                "use_parallel": state["use_parallel"],
                "image_uploaded": bool(image_data_uri),
                "repair_triggered": repair_triggered,
            }
        )

# --- Speed Comparison: Cerebras vs GPU-hosted GLM-5.2 (isolated benchmark) ---
# This panel does NOT run the MultiverseGuard graph on Together. It only sends the
# same compact prompt to each provider and compares latency.
st.divider()
with st.expander("Speed Comparison: Cerebras vs GPU-hosted GLM-5.2", expanded=False):
    st.caption(
        "Runs the same compact incident-response prompt on Cerebras and Together AI "
        "GLM-5.2 and compares latency. The main product path stays Cerebras + LangGraph."
    )
    together_key = os.getenv("TOGETHER_API_KEY", "")
    if not together_key:
        st.warning(
            "Together API key not configured. Set TOGETHER_API_KEY to run GPU-hosted comparison."
        )

    if st.button("Run Single-Call Benchmark"):
        if not live_calls_allowed():
            st.error("Access code required for live benchmarks. Enter it in the sidebar.")
            st.stop()
        with st.spinner("Running compact benchmark on Cerebras and Together AI..."):
            cerebras_result = run_cerebras_benchmark()
            together_result = run_together_benchmark()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Cerebras")
            st.metric("Latency", f"{cerebras_result.latency_seconds:.2f}s")
            if cerebras_result.tokens_per_second is not None:
                st.metric("Tokens/sec", f"{cerebras_result.tokens_per_second:.0f}")
            if cerebras_result.prompt_tokens is not None:
                st.caption(f"prompt tokens: {cerebras_result.prompt_tokens}")
            if cerebras_result.completion_tokens is not None:
                st.caption(f"completion tokens: {cerebras_result.completion_tokens}")
            st.caption(cerebras_result.model)
            if cerebras_result.error:
                st.error(cerebras_result.error)
            else:
                st.code(cerebras_result.output_preview, language="json")

        with col2:
            st.subheader("Together AI GLM-5.2")
            st.metric("Latency", f"{together_result.latency_seconds:.2f}s")
            if together_result.tokens_per_second is not None:
                st.metric("Tokens/sec", f"{together_result.tokens_per_second:.0f}")
            if together_result.prompt_tokens is not None:
                st.caption(f"prompt tokens: {together_result.prompt_tokens}")
            if together_result.completion_tokens is not None:
                st.caption(f"completion tokens: {together_result.completion_tokens}")
            st.caption(together_result.model)
            if together_result.error:
                st.error(together_result.error)
            else:
                st.code(together_result.output_preview, language="json")

        speedup = calculate_speedup(cerebras_result, together_result)
        if speedup is not None:
            st.success(
                f"Cerebras latency speedup: {speedup:.2f}x faster than Together on this benchmark."
            )
        else:
            st.info("Speedup unavailable because one or both providers returned an error.")

    st.markdown("---")
    st.subheader("4-Way Parallel Benchmark")
    st.caption(
        "Sends four concurrent variant prompts to each provider and compares wall time. "
        "This benchmark is separate from the LangGraph four-universe workflow."
    )

    if st.button("Run 4-Way Parallel Benchmark"):
        if not live_calls_allowed():
            st.error("Access code required for live benchmarks. Enter it in the sidebar.")
            st.stop()
        with st.spinner("Running 4 concurrent calls on Cerebras and Together AI..."):
            cerebras_parallel = run_cerebras_parallel_benchmark()
            together_parallel = run_together_parallel_benchmark()

        pcol1, pcol2 = st.columns(2)

        with pcol1:
            st.subheader("Cerebras (4 concurrent)")
            st.metric("Wall time", f"{cerebras_parallel.wall_time_seconds:.2f}s")
            st.metric("Completed calls", cerebras_parallel.completed_count)
            st.metric("Errored calls", cerebras_parallel.errored_count)
            if cerebras_parallel.average_latency_seconds is not None:
                st.metric("Avg per-call latency", f"{cerebras_parallel.average_latency_seconds:.2f}s")
            if cerebras_parallel.max_latency_seconds is not None:
                st.metric("Max per-call latency", f"{cerebras_parallel.max_latency_seconds:.2f}s")
            if cerebras_parallel.aggregate_tokens_per_second is not None:
                st.metric("Aggregate output tok/sec", f"{cerebras_parallel.aggregate_tokens_per_second:.0f}")
            st.caption(cerebras_parallel.model)
            if cerebras_parallel.error:
                st.error(cerebras_parallel.error)

        with pcol2:
            st.subheader("Together AI GLM-5.2 (4 concurrent)")
            st.metric("Wall time", f"{together_parallel.wall_time_seconds:.2f}s")
            st.metric("Completed calls", together_parallel.completed_count)
            st.metric("Errored calls", together_parallel.errored_count)
            if together_parallel.average_latency_seconds is not None:
                st.metric("Avg per-call latency", f"{together_parallel.average_latency_seconds:.2f}s")
            if together_parallel.max_latency_seconds is not None:
                st.metric("Max per-call latency", f"{together_parallel.max_latency_seconds:.2f}s")
            if together_parallel.aggregate_tokens_per_second is not None:
                st.metric("Aggregate output tok/sec", f"{together_parallel.aggregate_tokens_per_second:.0f}")
            st.caption(together_parallel.model)
            if together_parallel.error:
                st.error(together_parallel.error)

        parallel_speedup = calculate_parallel_speedup(cerebras_parallel, together_parallel)
        if parallel_speedup is not None:
            st.success(
                f"Cerebras completed 4 concurrent calls {parallel_speedup:.2f}x faster than Together GLM-5.2 by wall time."
            )
        else:
            st.info(
                "4-way parallel speedup unavailable because one or both providers returned an error."
            )