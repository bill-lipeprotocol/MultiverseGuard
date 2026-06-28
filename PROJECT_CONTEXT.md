# Project Context - MultiverseGuard

## Product Brief

MultiverseGuard is a multimodal multi-agent system for enterprise incident response.  
When an incident occurs, teams typically investigate one possible cause at a time. MultiverseGuard instead explores **multiple competing hypotheses in parallel** (referred to as "universes"), analyzes each using Gemma 4 on Cerebras, and produces a ranked remediation plan with rollback guidance.

**Primary Demo Scenario**: A checkout SEV1 incident following a deployment, involving database pool saturation with several plausible alternative causes.

## Hackathon Compliance

**Rule Reminder**: Pre-existing scaffolding is permitted, but the **core functionality** must be developed during the 24-hour hackathon and must use **Gemma 4 31B on Cerebras** as the central model.

### Scaffolding Completed Before the Hackathon
- Project folder structure and environment setup
- `requirements.txt` and configuration files
- Documentation (`README.md`, `PROJECT_CONTEXT.md`, `HACKATHON_BUILD_GUIDE.md`)
- Example data and demo assets
- Empty source code package structure

### Core Work to Be Completed During the Hackathon
- Pydantic schemas for structured outputs
- Cerebras client supporting mock and live modes
- Agent prompts and reasoning logic
- Multiverse graph with 4 parallel universes
- Streamlit UI integration with the graph
- Tests and demo materials

## Key Concepts

| Term                    | Simple Explanation                                      | Importance |
|-------------------------|---------------------------------------------------------|----------|
| **Multiverse**          | Investigating multiple hypotheses simultaneously        | Demonstrates the value of fast inference |
| **LangGraph**           | Framework for building agent workflows and graphs       | Powers the parallel universe logic |
| **Structured Output**   | Forcing the model to return clean, usable JSON          | Enables reliable agent handoffs |
| **Mock Mode**           | Simulated responses for development and testing         | Speeds up iteration and reduces costs |
| **Universe Worker**     | Component responsible for analyzing one hypothesis      | Core of the parallel reasoning system |

## Success Criteria

- Accept incident logs and at least one dashboard image
- Use Gemma 4 31B on Cerebras for core reasoning
- Generate and investigate 4 universes in parallel
- Rank universes with confidence scores
- Deliver remediation steps that include rollback actions
- Display timing metrics in the UI
- Function correctly in both mock and live modes