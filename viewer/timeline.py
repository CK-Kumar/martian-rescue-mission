# The crew log, one section per sol, ordered for a reader: what the operator
# decided (its end-of-sol log), what it did and what the base answered, and,
# folded away, how it reasoned. Every piece of model or world text goes
# through escape().

from html import escape

from viewer.story import FIRSTS

START = {"o2": 17, "water": 60}  # new_world's starting tanks
ICONS = {"inspect": "🔍", "repair": "🔧", "set_power": "⚡", "use": "✋",
         "use_battery": "🔋", "drill_ice": "⛏️"}
# World answers that mean the crew discovered or fixed something. Routine
# answers (drilling, drawing power) are left out so blue stays rare.
FINDINGS = [needle for needle, kind, _ in FIRSTS if kind == "good"] + ["hiss", "sealed it"]

CSS = """
<style>
.mm-sol { display: grid; grid-template-columns: 92px 1fr; gap: 0 22px; padding: 26px 0 30px;
          border-top: 1px solid #e0d1ba; scroll-margin-top: 40px; }
.mm-num { font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 64px; line-height: 0.85;
          color: #2A2320; font-variant-numeric: tabular-nums; }
.mm-num small { display: block; font-size: 15px; font-weight: 600; letter-spacing: 0.02em; color: #76675a; margin-top: 8px; }
.mm-head { display: flex; flex-wrap: wrap; gap: 10px 26px; align-items: center; margin-bottom: 14px; }
.mm-sky-chip { font-size: 14px; padding: 3px 11px; border-radius: 999px; background: #E9CFA4; color: #4a3424; }
.mm-sky-chip.mm-storm { background: #6F523B; color: #F1E6D4; }
.mm-meter { display: grid; grid-template-columns: auto 120px auto; gap: 8px; align-items: center; font-size: 15px; }
.mm-bar { height: 8px; background: #e6d9c5; border-radius: 99px; overflow: hidden; }
.mm-bar i { display: block; height: 100%; border-radius: 99px; }
.mm-meter b { font-variant-numeric: tabular-nums; font-weight: 600; }
.mm-low b { color: #B3261E; }
.mm-decision { font-size: 17px; line-height: 1.55; margin: 0 0 16px; max-width: 70ch; white-space: pre-wrap; }
.mm-decision::before { content: "“"; font-family: 'Barlow Condensed', sans-serif; font-size: 40px; line-height: 0;
                       vertical-align: -0.35em; margin-right: 4px; color: #3E6FA8; }
.mm-steps { display: grid; gap: 6px; margin-bottom: 14px; }
.mm-step { display: grid; grid-template-columns: 26px minmax(160px, 260px) 1fr; gap: 10px;
           align-items: baseline; padding: 7px 12px; border-radius: 8px; background: #FBF6EE; font-size: 15px; }
.mm-step .mm-did { font-weight: 600; }
.mm-step .mm-got { color: #76675a; }
.mm-step.mm-found { background: #3E6FA8; color: #fff; }
.mm-step.mm-found .mm-got { color: #fff; font-weight: 600; }
.mm-step.mm-refused .mm-got { color: #B3261E; }
.mm-rest { margin: -8px 0 16px; }
.mm-why summary { cursor: pointer; color: #3E6FA8; font-size: 15px; font-weight: 600; }
.mm-why p { font-size: 15px; line-height: 1.6; color: #4d4238; max-width: 75ch; white-space: pre-wrap;
            border-left: 3px solid #d9c6a6; padding-left: 14px; margin: 12px 0; }
.mm-cost { font-size: 13px; color: #76675a; margin-top: 12px; }
.mm-script { font-size: 15px; color: #76675a; margin: 0 0 8px; }
@media (max-width: 700px) {
  .mm-sol { grid-template-columns: 1fr; }
  .mm-num { font-size: 44px; margin-bottom: 8px; }
  .mm-step { grid-template-columns: 22px 1fr; }
  .mm-step .mm-got { grid-column: 2; }
}
</style>
"""


def doing(action):
    # The operator's action in plain words.
    kind = action.get("type", "?")
    target = action.get("target", "")
    if kind == "inspect":
        return f"Checked the {target}"
    if kind == "repair":
        return f"Repaired the {target}"
    if kind == "set_power":
        return f"Power: O₂ {action.get('o2')} kWh, recycler {action.get('recycler')} kWh"
    if kind == "use":
        return f"Used the {target} ({action.get('amount')})"
    if kind == "use_battery":
        return f"Drew {action.get('kwh')} kWh from the battery"
    if kind == "drill_ice":
        return f"Ordered {action.get('kg')} kg of ice"
    return kind


def step(icon, did, got):
    if got is None:
        css, got = "mm-step mm-refused", "Refused: no tool calls left this sol."
    elif any(f in got for f in FINDINGS):
        css = "mm-step mm-found"
    else:
        css = "mm-step"
    return (f'<div class="{css}"><span>{icon}</span><span class="mm-did">{escape(did)}</span>'
            f'<span class="mm-got">{escape(got)}</span></div>')


def meter(label, value, start, color):
    # Bar is relative to the starting level; red once below 30% of it.
    share = max(0.0, min(1.0, value / start))
    low = " mm-low" if share < 0.3 else ""
    fill = "#B3261E" if low else color
    return (f'<div class="mm-meter{low}"><span>{label}</span><div class="mm-bar">'
            f'<i style="width:{share * 100:.0f}%;background:{fill}"></i></div><b>{value:.1f} kg</b></div>')


def steps_for(row):
    lines = []
    if "llm_calls" in row:
        # Executed tool calls are logged in order; any beyond the budget were
        # refused, so the i-th tool call pairs with the i-th action.
        i = 0
        for call in row["llm_calls"]:
            for tool in call["tool_calls"]:
                done = row["actions"][i] if i < len(row["actions"]) else None
                i += 1
                lines.append(step(ICONS.get(tool["name"], "•"), doing({"type": tool["name"], **tool["args"]}),
                                  done["message"] if done else None))
        overnight = row.get("messages", [])
    else:
        # Scripted crew: its answers come first in "messages", overnight ones after.
        answers = row.get("messages", [])
        for n, action in enumerate(row["actions"]):
            lines.append(step(ICONS.get(action.get("type"), "•"), doing(action),
                              answers[n] if n < len(answers) else ""))
        overnight = answers[len(row["actions"]):]
    for message in overnight:
        lines.append(step("🌙", "Overnight", message))
    return f'<div class="mm-steps">{"".join(lines)}</div>' if lines else ""


def reasoning_for(row):
    thoughts = [c["reasoning"].strip() for c in row["llm_calls"] if c["reasoning"].strip()]
    if not thoughts:
        return ""
    paragraphs = "".join(f"<p>{escape(t)}</p>" for t in thoughts)
    # Open by default: seeing how the agent thinks is the point of the viewer.
    return f'<details class="mm-why" open><summary>How it reasoned ({len(thoughts)} thoughts)</summary>{paragraphs}</details>'


def cost_for(row):
    calls = row["llm_calls"]
    reads = sum(c["tokens_in"] for c in calls)
    cached = sum(c.get("cache_read", 0) for c in calls)
    tokens = reads + sum(c["tokens_out"] for c in calls)
    cost = sum(c["cost_usd"] or 0 for c in calls)
    secs = sum(c["latency_ms"] for c in calls) / 1000
    cache_part = f" ({round(100 * cached / reads)}% from cache)" if reads and cached else ""
    return (f'<div class="mm-cost">{len(calls)} model calls, {tokens:,} tokens{cache_part}, '
            f'${cost:.4f}, {secs:.1f} s of thinking</div>')


def sol_block(row, before):
    # One sol of the log. Used for the replay and, one at a time, for a live run.
    storm = row.get("dust", 0) > 0
    head = (f'<div class="mm-head"><span class="mm-sky-chip{" mm-storm" if storm else ""}">'
            f'{"🌪 Dust storm" if storm else "☀ Clear sky"}</span>'
            f'{meter("O₂", row["o2"], START["o2"], "#3E6FA8")}'
            f'{meter("Water", row["water"], START["water"], "#2F8C8A")}</div>')
    parts = [head]
    if "llm_calls" in row:
        note = row.get("log_note", "").strip()
        if note:
            parts.append(f'<p class="mm-decision">{escape(note)}</p>')
        parts.append(steps_for(row))
        parts.append(reasoning_for(row))
        parts.append(cost_for(row))
    else:
        parts.append(steps_for(row))
    return (f'<section class="mm-sol" id="sol-{row["sol"]}"><div class="mm-num">{row["sol"]:02d}'
            f'<small>sol</small></div><div>{"".join(parts)}</div></section>')


def crew_log_html(rows):
    blocks = [CSS]
    if rows and "llm_calls" not in rows[0]:
        blocks.append('<p class="mm-script">This crew follows a fixed script. It does not think or talk, '
                      'so you only see what it did and what the base answered.</p>')
    before = START
    for row in rows:
        blocks.append(sol_block(row, before))
        before = row
    return "".join(blocks)
