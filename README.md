# MultiverseGuard

Enterprise multimodal incident response with parallel hypothesis universes on Cerebras.

> Submitted to Enterprise Impact, Multiverse Agents, and People’s Choice.
>
> If you like the project, please consider watching the demo, trying the app, starring the repo, sharing the X post, or supporting it in People’s Choice.

## Demo Links

- 59-second video: [ADD VIDEO LINK]
- Live Streamlit app: [ADD STREAMLIT LINK]
- GitHub: https://github.com/bill-lipeprotocol/MultiverseGuard
- X post: [ADD X POST LINK]
- People’s Choice post/channel: [ADD DISCORD OR CONTEST LINK]

## People’s Choice / Public Support

MultiverseGuard is submitted to:

- Enterprise Impact
- Multiverse Agents
- People’s Choice

If you find the project useful or interesting, please support it by:

- watching the 59-second demo video
- trying the hosted Streamlit app
- starring the GitHub repo
- sharing the X post
- voting/supporting in the People’s Choice channel if available

Links:

- Video: [ADD VIDEO LINK]
- Live app: [ADD STREAMLIT LINK]
- GitHub: https://github.com/bill-lipeprotocol/MultiverseGuard
- X post: [ADD X POST LINK]
- People’s Choice post/channel: [ADD DISCORD OR CONTEST LINK]

## What It Does

MultiverseGuard ingests incident logs, operator notes, and dashboard screenshots, then dispatches four parallel hypothesis universes through LangGraph. Each universe investigates a different root-cause theory and returns evidence, confidence, missing evidence, remediation, and rollback guidance. A final synthesizer verifies that all four branches completed, ranks them by confidence, and produces an actionable incident response plan.

## Why Cerebras

Cerebras makes deep parallel exploration practical during live incidents.

In our 4-way parallel benchmark, Cerebras Gemma 4 31B completed four concurrent incident-analysis prompts in 0.44s versus 7.27s on Together AI GLM-5.2, a 16.49x wall-time speedup in that benchmark run.

## Architecture

- Streamlit UI
- Gemma 4 31B on Cerebras
- LangGraph branch orchestration
- Four hypothesis explorer branches
- Pydantic structured outputs
- Final critic/synthesizer
- Together AI GLM-5.2 benchmark adapter

## Core Features

- Multimodal incident input
- Four parallel hypothesis universes
- Evidence and missing-evidence tracking
- Ranked final incident report
- Remediation and rollback plan
- Cerebras timing metrics
- Cerebras vs Together benchmark
- 4-way parallel speed comparison

## Primary Demo Scenario

Checkout SEV-1 incident:
- 5xx checkout spike
- p95 latency rise
- DB pool saturation
- payment retries
- deployment shortly before incident

## Test Scenarios

- Checkout SEV-1 incident
- Auth/login incident
- Kafka/event-pipeline lag incident
- Regional load-balancer incident

See `TEST_CASES.md` and `data/examples/` for synthetic logs, operator notes, and alert summaries for each scenario.

## Local Setup

```powershell
git clone https://github.com/bill-lipeprotocol/MultiverseGuard.git
cd MultiverseGuard

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Configure secrets locally (never commit these)
$env:CEREBRAS_API_KEY="your_cerebras_key_here"
$env:CEREBRAS_MODEL="gemma-4-31b"
$env:MULTIVERSEGUARD_MOCK="false"

$env:TOGETHER_API_KEY="your_together_key_here"
$env:TOGETHER_BASE_URL="https://api.together.ai/v1"
$env:TOGETHER_MODEL="zai-org/GLM-5.2"

python -m streamlit run src/ui/app.py
```

For mock-mode rehearsal (no API calls), keep `MULTIVERSEGUARD_MOCK=true`.

## Streamlit Cloud Deployment

See `DEPLOYMENT.md` for full instructions. In short:

- Repository: `bill-lipeprotocol/MultiverseGuard`
- Branch: `main`
- Main file path: `src/ui/app.py`
- Python version: `3.10`
- Secrets configured in Streamlit Cloud secrets (never in GitHub)

## Security

No API keys are committed. Runtime secrets are configured through local environment variables or Streamlit Cloud secrets. See `SECURITY.md` for the secret-handling policy and scan commands.

If `APP_ACCESS_CODE` is configured on the hosted app, live Cerebras/Together calls require that code; mock mode and documentation remain visible without it.

## Limitations and Future Work

- The Together comparison is a benchmark path, not the full graph.
- More enterprise connectors could be added.
- Real monitoring integrations could replace synthetic incidents.

## Project Layout

- `src/ui/app.py` - Streamlit application
- `src/graph/multiverse_graph.py` - LangGraph four-universe workflow + reliability invariants
- `src/utils/cerebras_client.py` - Cerebras/OpenAI-compatible structured output client
- `src/utils/speed_benchmark.py` - Cerebras vs Together benchmark (single-call + 4-way parallel)
- `src/models/schemas.py` - Pydantic structured output models
- `src/agents/prompts.py` - system prompts
- `tests/` - offline test suite
- `data/examples/` - synthetic incident scenarios and dashboard images
