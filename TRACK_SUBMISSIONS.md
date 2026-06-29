# Track Submissions

Ready-to-post submission blocks for each eligible track. Copy the block for the track you are entering.

Tracks: Enterprise Impact, Multiverse Agents, and People’s Choice.

## Enterprise Impact

```markdown
## Enterprise Impact Submission

**Project:** MultiverseGuard
**Track:** Enterprise Impact

MultiverseGuard addresses a real enterprise pain point: slow incident diagnosis during noisy SEV-1 events. It ingests logs, dashboard screenshots, and operator notes, then uses Gemma 4 on Cerebras to generate and explore four parallel root-cause universes.

The final report ranks all hypotheses, identifies the most likely cause, and produces impact analysis, remediation steps, and rollback guidance. This helps incident teams reduce mean time to diagnosis while preserving an auditable evidence trail.

**Cerebras advantage:** In the included 4-way benchmark, Cerebras completed four concurrent incident-analysis prompts in 0.44s versus 7.27s on Together AI GLM-5.2, a 16.49x wall-time speedup in this run.

**Links**
- Video: [ADD VIDEO LINK]
- Live app: [ADD STREAMLIT LINK]
- GitHub: https://github.com/bill-lipeprotocol/MultiverseGuard
- X post: [ADD X POST LINK]
- People’s Choice post/channel: [ADD DISCORD OR CONTEST LINK]
```

## Multiverse Agents

```markdown
## Multiverse Agents Submission

**Project:** MultiverseGuard
**Track:** Multiverse Agents

MultiverseGuard models incident response as four parallel hypothesis universes. A supervisor creates distinct branches, LangGraph dispatches them in parallel, and each universe keeps independent state: evidence, confidence, missing evidence, recommended action, and rollback plan.

A final synthesizer validates that all four universes completed, ranks them by confidence, and produces a structured incident response report.

**Why it fits:** The project demonstrates explicit multiverse tracking, multi-agent collaboration, multimodal input, and Cerebras-powered speed.

**Links**
- Video: [ADD VIDEO LINK]
- Live app: [ADD STREAMLIT LINK]
- GitHub: https://github.com/bill-lipeprotocol/MultiverseGuard
- X post: [ADD X POST LINK]
- People’s Choice post/channel: [ADD DISCORD OR CONTEST LINK]
```

## People’s Choice

```markdown
## People’s Choice Submission

**Project:** MultiverseGuard
**Track:** People’s Choice

MultiverseGuard is a public, hosted demo of enterprise multimodal incident response with parallel AI hypothesis universes.

The app ingests logs, operator notes, and dashboard screenshots, then uses Gemma 4 on Cerebras to launch four LangGraph hypothesis branches in parallel. Each branch investigates a different root-cause theory and preserves its own evidence, confidence, missing evidence, recommended action, and rollback plan.

The final report ranks all four universes, selects the most likely root cause, and produces impact and remediation guidance.

For the public demo, MultiverseGuard also includes a speed comparison panel. In one 4-way parallel benchmark run, Cerebras completed four concurrent incident-analysis prompts in 0.44s versus 7.27s on Together AI GLM-5.2, a 16.49x wall-time speedup in that benchmark run.

**Why vote for it:**
MultiverseGuard is easy to understand, practical for real enterprise teams, visually demoable, and shows why fast inference matters when incidents are unfolding live.

**Links**
- 59-second video: [ADD VIDEO LINK]
- Live Streamlit app: [ADD STREAMLIT LINK]
- GitHub: https://github.com/bill-lipeprotocol/MultiverseGuard
- X post: [ADD X POST LINK]
- People’s Choice post/channel: [ADD DISCORD OR CONTEST LINK]
```

## Wording Rule

Always qualify the benchmark result as a single run, for example:

- "16.49x faster by wall time in this benchmark run."

Do **not** say "Cerebras is always 16.49x faster."
