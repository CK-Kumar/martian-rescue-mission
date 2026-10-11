# Results

One row per run. Append only, never edit old rows: the commit pins the exact
world version, so any row can be reproduced with `git checkout <commit>`.

| Date | Commit | Seed | Crew | Result | Note |
|---|---|---|---|---|---|
| 2026-10-11 | b52b3ae | 42 | do-nothing (scripted) | dead sol 10, suffocation | Baseline. Leak 2.0 kg/sol from sol 2 never repaired; storm from sol 9. Water also hit 0 on sol 10. |
| 2026-10-11 | b935c4e | 42 | repair-only (scripted) | dead sol 12, dehydration | Repairs leak on sol 3, O₂ holds at 15. Storm from sol 9 empties water on sol 10; no water means no O₂ made either. |
