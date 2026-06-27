# Project Context - MultiverseGuard

## Product Brief

MultiverseGuard is a multimodal multi-agent system for enterprise incident response.  
When an incident happens, teams usually investigate one possible cause at a time. MultiverseGuard instead explores **multiple competing hypotheses in parallel** (called "universes"), analyzes each one using Gemma 4 on Cerebras, and produces a ranked remediation plan with rollback steps.

**Demo Scenario**: A checkout SEV1 incident after a deployment, involving database pool issues with several possible causes.

## Hackathon Compliance

**Rule Reminder**: Pre-existing scaffolding is allowed, but the **core functionality** must be built during the 24-hour hackathon and must use **Gemma 4 31B on Cerebras** as the main model.

### What Was Done Before the Hackathon (Scaffolding)
- Project folder structure
- `requirements.txt` and environment setup
- Basic documentation
- Example data and demo assets
- Empty source code folders

### What Will Be Built During the Hackathon (Core Work)
- Pydantic schemas for structured outputs
- Cerebras client with mock and live mode
- Agent prompts
- Multiverse graph with 4 parallel universes
- Streamlit UI connected to the graph
- Tests and demo video

## Key Concepts

| Term                    | Simple Meaning                                      | Why It Matters |
|-------------------------|-----------------------------------------------------|----------------|
| **Multiverse**          | Running multiple hypotheses at the same time        | Shows the benefit of fast inference |
| **LangGraph**           | Tool to build agent workflows and parallel logic    | Used to create the 4-universe system |
| **Structured Output**   | Forcing the model to return clean JSON data         | Makes the system reliable |
| **Mock Mode**           | Fake responses for testing (no API calls)           | Helps development without using credits |
| **Universe Worker**     | The part that investigates one hypothesis           | Core of the parallel reasoning |

## Success Criteria

- Accept logs + dashboard image
- Use Gemma 4 31B on Cerebras for reasoning
- Generate and investigate 4 universes
- Rank the universes with confidence scores
- Provide remediation steps with rollback
- Show timing metrics in the UI
- Work in both mock and live mode