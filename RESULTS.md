# Results

One row per run. Append only, never edit old rows: the commit pins the exact
world version, so any row can be reproduced with `git checkout <commit>`.

| Date | Commit | Seed | Crew | Result | Note |
|---|---|---|---|---|---|
| 2026-10-11 | b52b3ae | 42 | do-nothing (scripted) | dead sol 10, suffocation | Baseline. Leak 2.0 kg/sol from sol 2 never repaired; storm from sol 9. Water also hit 0 on sol 10. |
| 2026-10-11 | b935c4e | 42 | repair-only (scripted) | dead sol 12, dehydration | Repairs leak on sol 3, O₂ holds at 15. Storm from sol 9 empties water on sol 10; no water means no O₂ made either. |
| 2026-10-11 | 07c8701 | 42 | perfect (scripted) | rescued sol 20 | Repair + inspect rover and ground on sol 3; drill 10 kg/sol on sunny sols (gets 9.5); battery 11 kWh/sol in storm. Lowest water 5.6 kg on sol 15. Best known plan, not proven optimal. do_nothing and repair_only rerun at this commit: same results. Tracked in MLflow. |
| 2026-10-11 | 9290e53 | 42 | haiku_solo (claude-haiku-5-5) | rescued sol 20 | Run was dirty at 0a9e2ba; code committed unchanged right after as 9290e53. Found ice sol 2, sealed leak sol 4, never found battery. Misread storm water loss as a leak; turned O₂ generator off sol 11; O₂ fell to 1.68 kg on sol 18. 38 calls, 598k tokens in / 22k out, $0.071, 4.2 s mean latency. One run, one seed. |
| 2026-10-11 | c548c14 | 1–5 | haiku_solo (claude-haiku-5-5) | 1/5 rescued (seed 2) | Seed 1 (storm sol 5) dead sol 8; seed 2 (storm 10) rescued; seed 3 (storm 5) dead 12; seed 4 (storm 5) dead 13; seed 5 (storm 8) dead 15; all suffocation. Every sol-5 storm killed it. Fixed the leak in 4/5, found ice in 1/5. Repeated pattern: notices dust, then blames a water leak instead of the starved recycler. Total $0.18. All runs clean, tracked in MLflow. |
| 2026-10-12 | c0af0c8 | 1–5 | haiku_solo (claude-haiku-5-5) | 3/5 rescued (seeds 1, 2, 3) | New prompt with a base manual. Sealed the leak in 5/5 (sol 3–4). Seeds 4 and 5 never inspected the ground: water ran out sol 14, then no water for O₂, suffocated sol 16. Total $0.077, 177 calls, mean latency 3.7 s. All runs clean. |
| 2026-10-12 | c0af0c8 | 1–5 | luna_solo (gpt-6-luna, Responses API, effort medium) | 3/5 rescued (seeds 2, 4, 5) | Found the ice in 5/5, the battery in 4/5. Leak sealed late or never: seed 1 never (dead sol 9), seed 3 on sol 9 (dead sol 12, water out sol 11). Total $0.057, 186 calls, mean latency 5.7 s. All runs clean. |
| 2026-10-12 | c0af0c8 (dirty) | 1–5 | grok_solo (grok-4.20-0309-reasoning) | 5/5 rescued | Found ice and battery sol 1–3, sealed the leak sol 4–5, but drained the battery before the storm in 4/5 and still made it. Total $1.64 (~20× Haiku), 232 calls, mean latency 6.2 s. Runs were dirty: uncommitted adapter code (agents/llm.py, main.py), committed as 1bdbc85; world and prompts unchanged from c0af0c8. |
