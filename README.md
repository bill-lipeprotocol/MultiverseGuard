# MultiverseGuard

**Enterprise Multimodal Multi-Agent Incident Response System**  
Built for the Cerebras x Google Gemma 4 Hackathon.

MultiverseGuard helps incident response teams by exploring **multiple root cause hypotheses in parallel** (called "universes") instead of one at a time. It uses **Gemma 4 31B on Cerebras** to analyze logs and dashboard images, then produces a ranked remediation plan with rollback steps.

## Hackathon Compliance

This project follows the hackathon rules:

- Only **scaffolding** (project structure, dependencies, basic documentation, and example data) was prepared before the event.
- The **core functionality** — including schemas, agent logic, multiverse graph, prompts, and UI integration — will be built **during the 24-hour hackathon**.
- **Gemma 4 31B on Cerebras** is the central model used for all reasoning and decision-making.

## Features

- Accepts incident logs and dashboard screenshots
- Uses Gemma 4 31B on Cerebras for multimodal analysis
- Explores **4 parallel universes** (competing hypotheses)
- Ranks universes with confidence scores
- Provides actionable remediation steps with rollback guidance
- Shows timing metrics and audit information
- Supports both **mock mode** (for development) and **live mode**

## Architecture Overview

Incident Logs + Image
        ↓
   Extract Evidence (Gemma 4)
        ↓
   Generate 4 Hypotheses
        ↓
   Investigate 4 Universes in Parallel
        ↓
   Rank & Synthesize Final Report
        ↓
   Display in Streamlit UI

## How to Run

### 1. Setup

```powershell
cd multiverseguard
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

2. Configure EnvironmentCopy the example file and add your Cerebras API key:powershell

copy .env.example .env

Edit .env and add your key:env

CEREBRAS_API_KEY=your_cerebras_api_key

3. Run the Applicationpowershell

streamlit run src/ui/app.py

4. Run in Mock Mode (Recommended while developing)Set this in your .env file:env

MULTIVERSEGUARD_MOCK=true

Demo VideoA 60-second demo video is available in demos/video_script.md.LicenseThis project was built for the Cerebras x Google Gemma 4 Hackathon.

---

### Quick Notes on This Version:

- Clear **Hackathon Compliance** section (very important)
- Beginner-friendly language
- Clean structure
- Good balance between detail and readability
- Matches the improved `PROJECT_CONTEXT.md` I gave earlier