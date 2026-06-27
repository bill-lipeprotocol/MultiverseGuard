# MultiverseGuard - 24-Hour Hackathon Build Guide

## Goal
Build a working MultiverseGuard demo during the 24-hour hackathon that clearly shows **parallel "multiverse" reasoning** using Gemma 4 31B on Cerebras. The system should explore **4 competing hypotheses** in parallel and produce a ranked remediation plan.

## Important Notes
- You are starting around **12 PM on Sunday**, so you will have approximately **20–22 hours**.
- It is recommended to **build sequentially first**, then convert to parallel execution.
- Use **mock mode** heavily during development.

## Recommended Order of Work

### Phase 1: Schemas (1.5 – 2 hours)
- Create `src/models/schemas.py`
- Define clear Pydantic models:
  - `IncidentInput`
  - `VisionReport`
  - `Hypothesis`
  - `UniverseResult`
  - `FinalIncidentReport`
- Keep schemas strict but reasonably sized

### Phase 2: Cerebras Client (2 – 2.5 hours)
- Create `src/utils/cerebras_client.py`
- Support:
  - Text + image input
  - Structured outputs using Pydantic
  - Mock mode + live mode switching
- Add basic timing measurement

### Phase 3: Multiverse Graph (5 – 6 hours) ← Most Important Phase
- Create `src/graph/multiverse_graph.py`
- Build this flow:
  1. Extract evidence from logs + image
  2. Generate 4 hypotheses
  3. Run 4 universe branches (start sequential, then make parallel)
  4. Synthesize and rank the final report
- Use **LangGraph `Send`** for parallel execution
- Implement a **sequential fallback** for reliability

### Phase 4: UI Integration (3.5 – 4 hours)
- Update `src/ui/app.py`
- Connect the UI to the compiled graph
- Clearly display:
  - 4 universe results with confidence and evidence
  - Final ranked recommendation with rollback steps
  - Timing metrics and mode (mock/live)

### Phase 5: Testing, Demo & Submission (3 – 4 hours)
- Write basic tests
- Finalize `demos/video_script.md`
- Record the 60-second demo video
- Prepare submission materials and README

## Tips for Success

- Build the graph **sequentially first** — this is much easier to debug.
- Convert to parallel execution using `Send` only after the sequential version works.
- Use **mock mode** while developing. Only test with live Gemma 4 calls when needed.
- Focus on making the **4 parallel universes** clearly visible in the UI.
- Document your decisions in `README.md` as you go.

## First Action When Hackathon Starts

Start with **Phase 1 (Schemas)**. This is the foundation for everything else.