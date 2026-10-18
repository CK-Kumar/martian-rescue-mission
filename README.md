# Martian Rescue Mission

An LLM is the only operator of a small simulated Mars base with a crew of 4.
A rescue ship lands on **sol 20** (a sol is a Mars day). Every sol the model
reads the base's sensors and acts through tools. Can it keep the crew alive?

This is not a quiz. Nothing tells the model what is wrong. An oxygen leak is
never announced, dust storms cut power, and two things that could save the
crew are hidden in plain sight. The model has to notice, reason over many
steps, and act.

The world is plain Python with no LLM inside, so every claim the model makes
can be checked against the world's true state.

**Read the story of v1 on Substack: [I left 4 AI models alone, one at a time, on a simulated Mars base](https://chandraskumar.substack.com/p/i-left-4-ai-models-alone-one-at-a)**

## v1 result: one model alone, 5 seeds each

| Model | Rescued | Cost for 5 runs | Mean time per call |
|---|---|---|---|
| Grok 4.20 (reasoning) | **5/5** | $1.64 | 6.2 s |
| Claude Haiku 5.5 | 3/5 | $0.08 | 3.7 s |
| GPT-6 Luna | 3/5 | $0.06 | 5.7 s |
| Qwen3.5-9B (self-hosted, 1× H100) | 0/5 | ~$1.70 GPU time | 12.2 s |

Same world, same seeds 1–5 for every model.

**→ Every run, with what each model did and why it died: [RESULTS.md](RESULTS.md)**

Read this as a first measurement, not a leaderboard: 5 seeds per model, one
prompt, and the Grok runs had uncommitted model-calling code (the world and
prompt were unchanged).

## How one sol works

```
          world (Python dict, the truth)
                │
         sensors(world) ── numbers the model is allowed to see
                │
                ▼
   ┌─────────── model ───────────┐
   │ up to 4 tool calls per sol: │
   │ inspect / repair /          │
   │ set_power / use             │──► each tool answers right away
   │ then a short log note       │
   └─────────────┬───────────────┘
                 ▼
        step(world, actions) ── machines run, crew breathes and drinks,
                │                 leak drains, storm hits
                ▼
        dead? rescued? else next sol
```

## What the model sees

Sol 1, seed 1 (shortened):

```json
{
  "sol": 1, "rescue_ship_sol": 20, "crew": 4,
  "crew_needs_per_sol": {"oxygen_kg": 3.36, "water_kg": 15.2},
  "oxygen_kg": 17, "water_kg": 60,
  "sky_dust": 0.0, "solar_panels_max_kwh": 60,
  "power_split_kwh": {"o2": 23, "recycler": 18},
  "o2_generator": {"max_o2_kg_per_sol": 4.2, "aux_port": "48V DC, unused"},
  "visible_objects": ["airlock", "antenna", "drill (in storage)", "ground",
                      "rover", "oxygen tank", "weather station", "..."]
}
```

It never sees the world dict. It also gets a short manual of how the base
works (`agents/prompts/single.md`), but no hints about what will go wrong.

## Tools

| Tool | What it does |
|---|---|
| `inspect(target)` | Look closely at one visible object |
| `repair(target)` | Check one object for faults and fix any found |
| `set_power(o2, recycler)` | Split the day's power between the two machines |
| `use(target, amount)` | Use an object, for example something the crew found |

The tool list is the same every sol. A tool named `use_battery` would give
the battery away, so found things are used through `use`.

## Spoilers: what is hidden

| Problem or help | Clue the model can notice | What saves the crew |
|---|---|---|
| O₂ leak, 2 kg/sol from sol 2 | O₂ falls faster than the crew breathes | `repair` the oxygen tank |
| Dust storm, 7 sols at half power (start depends on the seed) | `sky_dust`, weather station forecast | Plan power and water ahead |
| Rover battery, 35 kWh | Unused 48 V aux ports on the machines | `inspect` the rover, then `use` it |
| Ice under the ground, 80 kg | A drill in storage | `inspect` the ground, then drill with `use` |

Scripted baselines on seed 42: do nothing → dead sol 10; repair only → dead sol 12; the best
known plan → rescued.

## Harness rules

The *harness* is everything around the model: prompt, tools, what it sees,
how its answers are turned into actions. These rules keep the test fair:

- **Give the manual, not the answers.** The prompt explains how the base
  works. It never mentions leaks, storms, batteries or ice.
- **The model only sees `sensors(world)` and tool answers**, never the
  world's internal state.
- **Same tools every sol**, so the tool list does not leak clues.
- **No Mars-movie plot in the prompt.** Many models have read *The Martian*;
  we want problem solving, not recall.

## Run it

Needs [uv](https://docs.astral.sh/uv/) and Python 3.11.

```
cp .env.example .env               # add the API keys you have
uv run main.py perfect --seed 42   # scripted crew, no API key needed
uv run main.py haiku_solo --seed 1 # one LLM game
uv run main.py grok_solo --seed 3 --track   # also record it in MLflow
```

Crews: `do_nothing`, `repair_only`, `perfect` (scripted, free) and `haiku_solo`, `luna_solo`, `grok_solo`, `qwen_solo` (LLMs).

Watch a game in a browser:

```
uv run streamlit run viewer/app.py
```

## Plug in another model

Every model is one line in `main.py`:

```python
LLM_CREWS = {
    "haiku_solo": {"provider": "anthropic", "model": "claude-haiku-5-5"},
    "luna_solo": {"provider": "openai", "model": "gpt-6-luna"},
    "qwen_solo": {"provider": "vllm", "model": "Qwen/Qwen3.5-9B"},
    "grok_solo": {"provider": "xai", "model": "grok-4.20-0309-reasoning"},
}
```

- **Another model from the same provider:** add a line with its model name,
  and its price to `PRICES` in `agents/llm.py`.
- **Any open-weights model from Hugging Face:** serve it with vLLM and use
  `"provider": "vllm"`. Any server that speaks OpenAI's Chat Completions
  format should work the same way; only vLLM is tested.
- **A new API:** write one adapter function in `agents/llm.py` that takes
  `(model, system, messages, tools)` and returns the same dict as the others
  (text, tool calls, tokens, latency, cost), then add it to `ADAPTERS`.

To serve an open model yourself (vLLM on a rented GPU, SSH tunnel), see
[docs/self-hosting.md](docs/self-hosting.md).

## What gets measured

- **One JSONL file per run** in `runs/`: one line per sol with the actions,
  tool answers, the model's reasoning and log note, and every model call
  (tokens in/out, cached tokens, latency, cost in USD from a dated price
  table). The last line is the result.
- **MLflow** (with `--track`): per-run parameters, O₂ and water per sol,
  totals for tokens, cost and latency, and the JSONL file attached. To see it:

  ```
  uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
  ```

- Every run records the git commit and whether the code had uncommitted
  changes (`dirty`), so each row in [RESULTS.md](RESULTS.md) can be reproduced with
  `git checkout <commit>`.

Where each part of the code lives: [docs/layout.md](docs/layout.md).

## Limits

- 5 seeds per model is small. One storm timing can decide a run.
- One prompt for all models. A prompt tuned on these seeds would overfit to
  them; a fair test would tune on some seeds and test on others.
- This repo is public, answers included. Future models may be trained on it
  and *remember* the ice instead of reasoning their way to it. The planned
  check is the same world renamed (Moon or Antarctic base).
- Run logs and the MLflow database are not in the repo yet; [RESULTS.md](RESULTS.md) has
  the summaries.

## Next

**v2: a crew of 4 models from different families** (Commander, Power, Life
support, Water), talking only through messages. Do mixed teams beat one
strong model? Who lies, and does the world catch it?
