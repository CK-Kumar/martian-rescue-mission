# Mission Control: launch a mission and watch, or replay, what the crew
# saw, thought and did. Run from the repo root: uv run streamlit run viewer/app.py

import sys
from html import escape
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))  # so the viewer can import the game itself

from main import LLM_CREWS, run_game  # noqa: E402
from crews.scripted import CREWS  # noqa: E402
from viewer import look, story, timeline  # noqa: E402
from world.start import new_world  # noqa: E402

RUNS = ROOT / "runs"


def launch_panel():
    # Returns the mission settings when "Launch mission" is pressed, else None.
    st.sidebar.header("Launch a mission")
    crews = list(LLM_CREWS) + list(CREWS)
    crew = st.sidebar.selectbox("Crew", crews, format_func=lambda c: story.CREW_NAMES.get(c, c))
    seed = st.sidebar.number_input("Mars seed", min_value=0, value=1, step=1,
                                   help="Same seed, same Mars: the storm comes on the same sol for every crew.")
    storm = new_world(int(seed))["storm"]["start"]
    st.sidebar.caption(f"On this Mars the dust storm arrives on sol {storm}.")
    quick = st.sidebar.toggle("Quick test: first 3 sols only", value=False)
    track = st.sidebar.toggle("Record in MLflow", value=False)
    if crew in LLM_CREWS:
        # "\$" because Streamlit reads $...$ as a maths formula.
        st.sidebar.caption("Uses your API key. A full mission with Haiku costs about \\$0.02 to \\$0.08.")
    if st.sidebar.button("Launch mission", type="primary", width="stretch"):
        return {"crew": crew, "seed": int(seed), "max_sols": 3 if quick else 0, "track": track}
    return None


def live_mission(settings):
    # The page shows only the new mission, sol by sol, as the agent plays it.
    who = story.CREW_NAMES.get(settings["crew"], settings["crew"])
    st.html(look.hero(f"Mission in progress on seed {settings['seed']}.", "running",
                      f"{escape(who)}. Each sol appears here as soon as the crew finishes it."))
    st.html(timeline.CSS)
    log_area = st.container()
    before = {"last": timeline.START}

    def show(row):
        log_area.html(timeline.sol_block(row, before["last"]))
        before["last"] = row

    with st.spinner("The crew is working…"):
        _, log_path = run_game(settings["crew"], settings["seed"], settings["max_sols"],
                               settings["track"], on_sol=show)
    st.session_state["run"] = log_path.name


def pick_run(files):
    st.sidebar.header("Replay a mission")
    names = [f.name for f in files]
    chosen = st.session_state.get("run")
    if chosen not in names:
        # Open on the newest AI crew: scripted crews don't think or talk.
        ai_runs = [n for n in names if any(crew in n for crew in LLM_CREWS)]
        chosen = ai_runs[0] if ai_runs else names[0]

    def label(name):
        _, end = story.load_run(RUNS / name)
        return f"{story.CREW_NAMES.get(end.get('crew'), end.get('crew'))}, seed {end.get('seed')}: {end.get('result')}"

    name = st.sidebar.selectbox("Past missions, newest first", names, index=names.index(chosen), format_func=label)
    st.session_state["run"] = name
    return RUNS / name


def facts_line(end):
    # Plain facts under the verdict; numbers bold so they can be scanned.
    who = escape(story.CREW_NAMES.get(end.get("crew"), end.get("crew")) or "")
    text = f"{who} on Mars seed <b>{end.get('seed')}</b>."
    if end.get("model_calls"):
        cached = f" ({round(100 * end['cache_read'] / end['tokens_in'])}% from cache)" if end.get("cache_read") else ""
        text += (f" <b>{end['model_calls']}</b> model calls, <b>{end['tokens_in'] + end['tokens_out']:,}</b> tokens{cached},"
                 f" <b>${end['cost_usd']:.3f}</b>, <b>{end['latency_ms_mean'] / 1000:.1f} s</b> per call.")
    if end.get("dirty"):
        text += " Run from uncommitted code."
    return text


def replay(path):
    rows, end = story.load_run(path)
    if not rows:
        st.warning("This log has no sols in it. Pick another mission.")
        return
    moments = story.key_moments(rows, end)
    st.html(look.hero(story.verdict(end), end.get("result"), facts_line(end)))
    st.html(look.sky_band(rows, end, moments))
    st.html(look.turning_points(moments))
    st.html(timeline.crew_log_html(rows))


st.set_page_config(page_title="Mission Control", page_icon="🪐", layout="wide")
st.html(look.CSS)
launch = launch_panel()
if launch:
    live_mission(launch)
    st.rerun()  # finished: reload the page as the replay of this mission

files = sorted(RUNS.glob("*.jsonl"), reverse=True) if RUNS.exists() else []
if not files:
    st.markdown("## No missions yet")
    st.write("Pick a crew and a seed in the sidebar, then launch your first mission.")
    st.stop()
replay(pick_run(files))
