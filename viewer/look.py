# The page-level visuals: the verdict and the Mars sky band, the one bold
# element. Every class starts with "mm-": plain names like "marks" clash with
# Streamlit's and charting libraries' own classes and broke the layout once.

import base64
from html import escape

INK = "#2A2320"
SUNSET = "#3E6FA8"
ALARM = "#B3261E"
MUTED = "#76675a"

# Sky colours per sol, top to horizon. On Mars the daytime sky is
# butterscotch and sunsets are blue; we use that blue for the rescue.
SKY = {
    "clear": ("#E9CFA4", "#D7A867"),
    "storm": ("#9A7A5C", "#6F523B"),
    "night": ("#1E2140", "#2F2F55"),   # sols after the crew died
    "rescue": ("#5F86C2", "#B8C9E2"),
    "future": ("#EDE3D3", "#E2D5C1"),  # sols a stopped run never reached
}
EVENT_ICONS = {"Sealed the oxygen leak.": "🔧", "Found the rover battery.": "🔋",
               "Found ice under the ground.": "🧊", "Checked the forecast and saw the storm coming.": "📡",
               "An oxygen leak started. Nobody told the crew.": "💨",
               "Switched the O₂ generator off to save water.": "⚠️"}

CSS = f"""
<style>
/* Quiet Streamlit's own chrome so the page reads as a product, not a tool. */
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.2rem; max-width: 1180px; }}
.mm-verdict {{ font-family: 'Barlow Condensed', sans-serif; font-weight: 700; letter-spacing: -0.01em;
              font-size: clamp(40px, 6.2vw, 76px); line-height: 0.98; margin: 0 0 10px; color: {INK}; }}
.mm-verdict.mm-dead {{ color: {ALARM}; }}
.mm-facts {{ font-size: 17px; color: {MUTED}; max-width: 80ch; margin: 0 0 22px; }}
.mm-facts b {{ color: {INK}; font-weight: 600; }}
.mm-skywrap {{ position: relative; }}
.mm-sky {{ width: 100%; height: auto; display: block; border-radius: 10px; }}
.mm-skylinks {{ position: absolute; inset: 0; display: grid; grid-template-columns: repeat(20, 1fr); }}
.mm-skylinks a:hover, .mm-skylinks a:focus-visible {{ background: rgba(255,255,255,0.18); outline: 2px solid #fff; outline-offset: -2px; }}
.mm-sky-key {{ font-size: 14px; color: {MUTED}; margin: 8px 0 28px; }}
.mm-turns {{ display: flex; flex-wrap: wrap; gap: 8px 10px; margin: 0 0 34px; }}
.mm-turn {{ background: #FBF6EE; border: 1px solid #e3d5bf; border-radius: 999px; padding: 5px 14px 5px 10px;
           font-size: 15px; text-decoration: none; color: {INK}; }}
.mm-turn:hover, .mm-turn:focus-visible {{ border-color: {INK}; }}
.mm-turn b {{ font-family: 'Barlow Condensed', sans-serif; font-size: 16px; margin-right: 6px; }}
</style>
"""


def hero(verdict_text, result, facts_html):
    # facts_html is built by the caller from escaped values.
    css = "mm-verdict mm-dead" if result == "dead" else "mm-verdict"
    return f'<div class="{css}">{escape(verdict_text)}</div><p class="mm-facts">{facts_html}</p>'


def sky_state(sol, by_sol, end):
    if end.get("result") == "rescued" and sol == end.get("sol"):
        return "rescue"
    if end.get("result") == "dead" and sol > end.get("sol", 99):
        return "night"
    if sol not in by_sol:
        return "night" if end.get("result") == "dead" else "future"
    return "storm" if by_sol[sol].get("dust", 0) > 0 else "clear"


def sky_band(rows, end, moments, last_sol=20):
    # A strip of Martian sky: one slice per sol, the horizon below with sol
    # numbers, and an icon above the horizon for each turning point.
    by_sol = {row["sol"]: row for row in rows}
    width, slice_w, sky_h, ground_h = 1000, 50, 150, 54
    defs, body = [], []
    for state, (top, bottom) in SKY.items():
        defs.append(f'<linearGradient id="mm-g-{state}" x1="0" y1="0" x2="0" y2="1">'
                    f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>')
    # Dust hatching drawn over storm sols.
    defs.append('<pattern id="mm-dust" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(25)">'
                '<line x1="0" y1="0" x2="0" y2="8" stroke="#E9CFA4" stroke-opacity="0.35" stroke-width="2"/></pattern>')
    for sol in range(1, last_sol + 1):
        x = (sol - 1) * slice_w
        state = sky_state(sol, by_sol, end)
        body.append(f'<rect x="{x}" y="0" width="{slice_w + 0.5}" height="{sky_h}" fill="url(#mm-g-{state})"/>')
        if state == "storm":
            body.append(f'<rect x="{x}" y="0" width="{slice_w + 0.5}" height="{sky_h}" fill="url(#mm-dust)"/>')
        if state == "night":
            body.append(f'<circle cx="{x + 14}" cy="28" r="1.4" fill="#fff" opacity="0.8"/>'
                        f'<circle cx="{x + 36}" cy="52" r="1" fill="#fff" opacity="0.6"/>')
    # Horizon: a low ridge, then the ground with sol numbers.
    ridge = " ".join(f"L{x},{sky_h - 8 - (11 if (x // 70) % 3 == 0 else 4 if (x // 70) % 3 == 1 else 0)}"
                     for x in range(0, width + 70, 70))
    body.append(f'<path d="M0,{sky_h} {ridge} L{width},{sky_h} Z" fill="#7A4A31"/>')
    body.append(f'<rect x="0" y="{sky_h}" width="{width}" height="{ground_h}" fill="#5A3624"/>')
    for sol in range(1, last_sol + 1):
        x = (sol - 1) * slice_w + 25
        body.append(f'<text x="{x}" y="{sky_h + 33}" text-anchor="middle" font-family="Barlow Condensed, Arial Narrow, sans-serif" '
                    f'font-size="20" font-weight="600" fill="#F1E6D4">{sol}</text>')
    # Turning points: icons standing on the horizon; outcome marked large.
    stacked = {}
    for sol, kind, text in moments:
        x = (sol - 1) * slice_w + 25
        if kind == "bad":
            icon, size = "✕", 34
        elif text.startswith("The rescue ship"):
            icon, size = "🚀", 30
        elif text in EVENT_ICONS:
            icon, size = EVENT_ICONS[text], 24
        else:
            continue
        level = stacked.get(sol, 0)
        stacked[sol] = level + 1
        y = sky_h - 30 - level * 40
        if icon == "✕":
            body.append(f'<text x="{x}" y="{y + 8}" text-anchor="middle" font-size="{size}" fill="#fff" '
                        f'font-weight="700">{icon}</text>')
        else:
            # A light badge behind the icon so it reads on any sky.
            body.append(f'<circle cx="{x}" cy="{y - 7}" r="17" fill="#FFF8EC" opacity="0.92"/>'
                        f'<text x="{x}" y="{y + 1}" text-anchor="middle" font-size="{size}">{icon}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {sky_h + ground_h}">'
           f'<defs>{"".join(defs)}</defs>{"".join(body)}</svg>')
    # Streamlit strips inline SVG, so the sky is an image; an invisible row of
    # links on top keeps "click a sol" and hover tooltips working.
    src = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    links = []
    for sol in range(1, last_sol + 1):
        tip = " ".join(text for s_, _, text in moments if s_ == sol) or f"Sol {sol}"
        if sol in by_sol:
            links.append(f'<a href="#sol-{sol}" title="Sol {sol}: {escape(tip)}"></a>')
        else:
            links.append(f'<span title="Sol {sol}"></span>')
    return (f'<div class="mm-skywrap"><img class="mm-sky" src="{src}" '
            f'alt="Mars sky over the {last_sol} sols of the mission"><div class="mm-skylinks">{"".join(links)}</div></div>'
            '<div class="mm-sky-key">Each slice of sky is one sol: clear, dust storm, blue sunset for the rescue, '
            'night after the crew died. Hover a sol for what happened, click it to read it.</div>')


def turning_points(moments):
    chips = [f'<a class="mm-turn" href="#sol-{sol}"><b>Sol {sol}</b>{escape(text)}</a>'
             for sol, kind, text in moments if kind != "storm"]
    return f'<div class="mm-turns">{"".join(chips)}</div>'
