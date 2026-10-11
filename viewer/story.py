# Turns a run log into plain sentences a product manager can read:
# one verdict, and the moments that decided the mission.

import json

from world.constants import LEAK_START_SOL

CAUSES = {"suffocation": "ran out of air", "dehydration": "ran out of water"}

CREW_NAMES = {
    "haiku_solo": "Claude Haiku 5.5, flying solo",
    "perfect": "Scripted crew, best known plan",
    "repair_only": "Scripted crew, repairs only",
    "do_nothing": "Scripted crew, does nothing",
}

# First time a world answer contains this text, it becomes a key moment.
FIRSTS = [
    ("found a leaking valve", "good", "Sealed the oxygen leak."),
    ("rover battery:", "good", "Found the rover battery."),
    ("ice under the regolith", "good", "Found ice under the ground."),
    ("dust storm approaching", "good", "Checked the forecast and saw the storm coming."),
    ("drew ", "info", "Started drawing power from the rover battery."),
    ("drilled ", "info", "Started drilling ice for water."),
]


def load_run(path):
    lines = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    rows = [line for line in lines if "result" not in line]
    end = next((line for line in lines if "result" in line), {})
    return rows, end


def verdict(end):
    sol = end.get("sol", "?")
    if end.get("result") == "rescued":
        return f"The crew was rescued on sol {sol}."
    if end.get("result") == "dead":
        return f"The crew {CAUSES.get(end.get('cause'), 'died')} on sol {sol}."
    return f"Mission paused after sol {sol - 1 if isinstance(sol, int) else sol}."


def world_answers(row):
    # LLM rows keep each answer with its action; scripted rows keep them
    # in "messages". Overnight messages (drilling) are in "messages" for both.
    answers = [a["message"] for a in row["actions"] if isinstance(a, dict) and "message" in a]
    return answers + row.get("messages", [])


def key_moments(rows, end):
    # Returns [(sol, kind, text)], kind = good / bad / risk / info / storm / hidden.
    moments = []
    if rows and rows[0]["sol"] <= LEAK_START_SOL <= rows[-1]["sol"]:
        moments.append((LEAK_START_SOL, "hidden", "An oxygen leak started. Nobody told the crew."))
    seen = set()
    prev_dust = 0
    for row in rows:
        sol, dust = row["sol"], row.get("dust", 0)
        if dust > 0 and prev_dust == 0:
            moments.append((sol, "storm", "A dust storm arrived and halved solar power."))
        if dust == 0 and prev_dust > 0:
            moments.append((sol, "storm", "The dust storm cleared."))
        prev_dust = dust
        for answer in world_answers(row):
            for needle, kind, text in FIRSTS:
                if needle in answer and needle not in seen:
                    seen.add(needle)
                    moments.append((sol, kind, text))
        for a in row["actions"]:
            action = a.get("action", a) if isinstance(a, dict) else {}
            if action.get("type") == "set_power" and action.get("o2") == 0 and "o2_off" not in seen:
                seen.add("o2_off")
                moments.append((sol, "risk", "Switched the O₂ generator off to save water."))
    if end.get("result") == "rescued":
        moments.append((end["sol"], "good", "The rescue ship landed."))
    elif end.get("result") == "dead":
        moments.append((end["sol"], "bad", f"The crew {CAUSES.get(end.get('cause'), 'died')}."))
    return sorted(moments, key=lambda m: m[0])
