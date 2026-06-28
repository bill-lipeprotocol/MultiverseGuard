# MultiverseGuard - 24-Hour Hackathon Build Guide

## Goal
Build a working MultiverseGuard demo during the 24-hour hackathon that clearly demonstrates **parallel "multiverse" reasoning** using Gemma 4 31B on Cerebras. The system should explore **4 competing hypotheses** in parallel and deliver a ranked remediation plan with rollback steps.

## Important Notes
- You are starting around **12:00 PM on Sunday**, giving you approximately **20–22 hours**.
- It is strongly recommended to **build the graph sequentially first**, then convert it to parallel execution.
- Use **mock mode** heavily during development to move quickly and save API usage.

## Recommended Order of Work

### Phase 1: Schemas (1.5 – 2 hours)
- Create `src/models/schemas.py`
- Define the following Pydantic models:
  - `IncidentInput`
  - `VisionReport`
  - `Hypothesis`
  - `UniverseResult`
  - `FinalIncidentReport`
- Keep schemas strict but reasonably sized for reliable structured outputs.

### Phase 2: Cerebras Client (2 – 2.5 hours)
- Create `src/utils/cerebras_client.py`
- The client should support:
  - Text and image inputs
  - Structured outputs using Pydantic
  - Easy switching between mock mode and live mode
- Include basic timing measurement.

### Phase 3: Multiverse Graph (5 – 6 hours) ← Highest Priority
- Create `src/graph/multiverse_graph.py`
- Implement the following flow:
  1. Extract evidence from logs and image
  2. Generate 4 hypotheses
  3. Investigate 4 universe branches (build sequentially first, then add parallelism)
  4. Synthesize and rank the final report
- Use **LangGraph `Send`** for parallel execution.
- Implement a **sequential fallback** for reliability and easier debugging.

### Phase 4: UI Integration (3.5 – 4 hours)
- Update `src/ui/app.py`
- Connect the Streamlit UI to the compiled graph.
- Clearly display:
  - Results from all 4 universes (with confidence and evidence)
  - Final ranked recommendation with rollback steps
  - Timing metrics and current mode (mock/live)

### Phase 5: Testing, Demo & Submission (3 – 4 hours)
- Write basic tests to validate the core flow.
- Finalize `demos/video_script.md`
- Record the 60-second demo video.
- Prepare submission materials.

## Tips for Success

- Build the graph **sequentially first** — this significantly reduces debugging difficulty.
- Only convert to parallel execution (`Send`) after the sequential version is working reliably.
- Keep prompts focused and relatively concise.
- Make the **4 parallel universes** clearly visible and easy to understand in the UI.
- Document key decisions in `README.md` as you build.

## First Action When the Hackathon Starts

Begin with **Phase 1 (Schemas)**. This forms the foundation for the entire system.