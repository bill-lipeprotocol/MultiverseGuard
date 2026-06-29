# MultiverseGuard

MultiverseGuard is an enterprise multimodal incident response system powered by Gemma 4 on Cerebras. It ingests logs, operator notes, and dashboard screenshots, then dispatches four LangGraph hypothesis universes in parallel. Each universe investigates a different root-cause theory while preserving its own evidence trail, confidence score, missing evidence, recommended action, and rollback plan.

A final synthesizer verifies that all four branches completed, ranks them by confidence, selects the most likely root cause, and generates an impact summary plus remediation plan.

The demo includes a live speed comparison: four concurrent incident-analysis prompts completed on Cerebras in 0.44s versus 7.27s on Together AI GLM-5.2, a 16.49x wall-time speedup in this benchmark run.

## Links

- 59-second video: [ADD VIDEO LINK]
- Live app: [ADD STREAMLIT LINK]
- GitHub: https://github.com/bill-lipeprotocol/MultiverseGuard
- X post: [ADD X POST LINK]
- People’s Choice post/channel: [ADD DISCORD OR CONTEST LINK]

## People’s Choice Angle

MultiverseGuard is designed to be immediately understandable in a public demo: noisy incident data goes in, four parallel root-cause universes are explored, and a ranked response plan comes out.

The People’s Choice story is simple:

> What if every SEV-1 incident commander could instantly explore four plausible realities before choosing a rollback, mitigation, or escalation path?

The hosted app, short video, and GitHub repo are public so viewers can inspect and share the project.

## Why It Matters

Enterprise incident teams lose time correlating logs, dashboards, deploys, dependency health, and operator notes. MultiverseGuard turns this multimodal evidence into a structured, auditable response plan in seconds.

## Cerebras Advantage

Cerebras speed makes four-branch parallel scenario exploration practical during live incidents. The application includes token-level timing metrics and a side-by-side benchmark against Together AI GLM-5.2.

## Built With

- Cerebras Inference
- Gemma 4 31B
- LangGraph
- Streamlit
- Pydantic
- Together AI benchmark adapter

## Try It

1. Open the live app link above.
2. Load the demo incident (checkout SEV-1).
3. Optionally upload one of the synthetic dashboards in `data/examples/`.
4. Turn LangGraph on and run. Confirm exactly four universe cards and four ranked results.
5. Open "Speed Comparison: Cerebras vs GPU-hosted GLM-5.2" and run the single-call and 4-way parallel benchmarks.

## Reliability

The system enforces a hard four-universe invariant end-to-end: exactly four hypotheses generated, exactly four branches completed, and exactly four ranked results sorted by confidence descending. If final synthesis omits a universe, it retries once with a strict repair prompt; if that fails, it errors clearly instead of presenting an incomplete report.
