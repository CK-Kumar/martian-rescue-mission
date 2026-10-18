# Layout

```
main.py              run one game: python main.py <crew> --seed N [--track]
world/               the simulation, no LLM inside
  constants.py       every number, with the reason for it
  start.py           new_world(seed)
  sensors.py         what the model may see
  tools.py           the 4 tools
  actions.py         what each tool does to the world
  power.py           weather, storm, power split
  life_support.py    make O₂, recycle water, crew use, leak
  rules.py           step(): one sol; death and rescue checks
agents/
  llm.py             one adapter per provider, prices, cost
  single.py          the one-model loop: sensors → tool calls → actions
  prompts/single.md  the system prompt (the manual)
crews/scripted.py    fixed-plan crews for baselines
log.py, tracking.py  JSONL logs and MLflow
viewer/              Streamlit app to replay or launch a game
```
