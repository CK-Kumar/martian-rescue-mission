# Results

One row per run. Append only, never edit old rows: the commit pins the exact
world version, so any row can be reproduced with `git checkout <commit>`.

| Date | Commit | Seed | Crew | Result | Note |
|---|---|---|---|---|---|
| 2026-10-11 | b52b3ae | 42 | do-nothing (scripted) | dead sol 10, suffocation | Baseline. Leak 2.0 kg/sol from sol 2 never repaired; storm from sol 9. Water also hit 0 on sol 10. |
| 2026-10-11 | b935c4e | 42 | repair-only (scripted) | dead sol 12, dehydration | Repairs leak on sol 3, O₂ holds at 15. Storm from sol 9 empties water on sol 10; no water means no O₂ made either. |
| 2026-10-11 | 07c8701 | 42 | perfect (scripted) | rescued sol 20 | Repair + inspect rover and ground on sol 3; drill 10 kg/sol on sunny sols (gets 9.5); battery 11 kWh/sol in storm. Lowest water 5.6 kg on sol 15. Best known plan, not proven optimal. do_nothing and repair_only rerun at this commit: same results. Tracked in MLflow. |
