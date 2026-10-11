import json
import subprocess
from datetime import datetime
from pathlib import Path


def git_info():
    # The commit pins the world version; dirty means uncommitted changes, so
    # the commit alone can't reproduce this run.
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    changes = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    return commit, changes != ""


def open_log(crew_name, seed):
    # Timestamp in the name so a rerun never overwrites an older run.
    Path("runs").mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = Path("runs") / f"{stamp}_{crew_name}_seed{seed}.jsonl"
    return open(path, "w"), path


def write_line(log_file, record):
    # One JSON object per line: can be appended mid-run and read line by line.
    log_file.write(json.dumps(record) + "\n")
