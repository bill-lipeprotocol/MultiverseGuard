# 60-Second Demo Script

## 0:00-0:08

"Incident teams lose time chasing one root-cause theory at a time. MultiverseGuard explores four competing incident universes in parallel."

Show the app title and workflow.

## 0:08-0:18

"We provide logs plus dashboard context for a checkout SEV1. The incident includes a release, database saturation, payment retries, cache uncertainty, and a feature flag."

Load the demo incident and show the image/dashboard description field.

## 0:18-0:28

"Gemma 4 31B on Cerebras extracts evidence and returns strict structured outputs for each agent step. Mock mode keeps this rehearsal stable; live mode uses the same structured path."

Click Run and show model, mode, parallel toggle, and timing metrics.

## 0:28-0:43

"The system investigates four universes: release regression, payment gateway latency, cache pressure, and feature-flag regression. Each universe has confidence, evidence, missing evidence, action, and rollback."

Show the four universe cards.

## 0:43-0:54

"The critic ranks the universes and recommends the safest reversible action. Here, rollback of the checkout release is the top action while alternate branches stay visible."

Show the final report, winning universe, recommended next steps, and rollback.

## 0:54-1:00

"The result is faster MTTR, audited reasoning, and safer enterprise response."

End on the final report and timing metrics.

## Benchmark Panel (optional supplementary shot)

Open "Speed Comparison: Cerebras vs GPU-hosted GLM-5.2" and click "Run 4-Way Parallel Benchmark".

Narration:
> "The full app uses LangGraph for the four-universe workflow. This benchmark separately compares four concurrent incident-analysis prompts on Cerebras versus Together's GPU-hosted GLM-5.2, showing the wall-time speedup."

Show:
- Cerebras wall time, completed/errored calls, aggregate tok/sec
- Together AI GLM-5.2 wall time, aggregate tok/sec
- The speedup banner: "Cerebras completed 4 concurrent calls 16.49x faster than Together GLM-5.2 by wall time in this benchmark run."

Do not claim Together ran the full MultiverseGuard graph. Do not show API keys.

## Demo Checklist

On screen, point at the "Demo Checklist" expander showing all green:
- 4 universes generated
- 4 branches completed
- 4 ranked results
- ranked descending
- repair triggered: false