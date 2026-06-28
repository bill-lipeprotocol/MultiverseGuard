# MultiverseGuard

**Enterprise Multimodal Multi-Agent Incident Response System**  
Built for the Cerebras x Google Gemma 4 Hackathon.

MultiverseGuard enables faster incident response by exploring **4 root-cause universes in parallel** instead of investigating one theory at a time. It uses **Gemma 4 31B on Cerebras** to analyze logs and dashboard context, then produces a ranked remediation plan with rollback steps.

## Hackathon Compliance

This project adheres to the hackathon rules:

- Only **scaffolding** (project structure, dependencies, documentation, and example assets) was prepared before the event.
- The **core functionality** — including schemas, Cerebras client, multiverse graph logic, prompts, UI integration, and tests — is built during the 24-hour hackathon.
- **Gemma 4 31B on Cerebras** serves as the central model for reasoning and decision-making in live mode.
- Mock mode is used for development and demo rehearsal to protect stability and API usage.

## Key Features

- Accepts incident logs and dashboard/image descriptions
- Uses Gemma 4 31B on Cerebras for structured multimodal analysis in live mode
- Explores **4 parallel universes**: release regression, payment latency, cache pressure, and feature-flag regression
- Ranks universes with confidence scores
- Provides remediation actions with rollback guidance
- Displays timing metrics and audit information
- Supports both **mock mode** and **live mode**

## Architecture Overview

```text
Incident Logs + Image Context
        ↓
Extract Evidence
        ↓
Generate 4 Hypotheses
        ↓
Investigate 4 Universes (sequential fallback or LangGraph Send)
        ↓
Rank & Synthesize Final Report
        ↓
Display in Streamlit UI
```

## Setup

```powershell
cd multiverseguard
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and add your Cerebras API key for live mode:

```env
CEREBRAS_API_KEY=your_key_here
CEREBRAS_MODEL=gemma-4-31b
MULTIVERSEGUARD_MOCK=true
```

Keep `MULTIVERSEGUARD_MOCK=true` while developing.

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Run The Application

```powershell
.\.venv\Scripts\streamlit.exe run src\ui\app.py
```

## Demo

A 60-second demo script is available in `demos/video_script.md`.
