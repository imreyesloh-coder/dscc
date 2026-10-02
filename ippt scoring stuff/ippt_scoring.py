"""
Deterministic IPPT scoring, using the official scoring tables directly.

Design note: this is intentionally NOT sent to the Claude API as raw
table text. Score calculation is exact, sensitive to being correct,
and doesn't need judgement, so it belongs in code, not in a prompt.
The AI only ever sees a derived summary (e.g. "current score 62,
target 90"), never the tables themselves. This is both cheaper
(no massive table in every prompt) and more reliable (no risk of the
model mis-reading a score off a table it was only shown once).
"""

import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

with open(os.path.join(_DATA_DIR, "run_2_4km.json")) as f:
    RUN_TABLE = json.load(f)
with open(os.path.join(_DATA_DIR, "pushup.json")) as f:
    PUSHUP_TABLE = json.load(f)
with open(os.path.join(_DATA_DIR, "situp.json")) as f:
    SITUP_TABLE = json.load(f)

AGE_CATEGORIES = RUN_TABLE["age_categories"]


def age_to_column(age: int) -> int:
    """Maps an age to the correct column index (0-13) in the tables."""
    bounds = [22, 25, 28, 31, 34, 37, 40, 43, 46, 49, 52, 55, 58]
    for i, upper in enumerate(bounds):
        if age < upper:
            return i
    return len(AGE_CATEGORIES) - 1  # 58-60 and above


def get_run_score(age: int, time_sec: int) -> int:
    """time_sec: actual 2.4km finish time in seconds. Lower is better."""
    col = age_to_column(age)
    rows = RUN_TABLE["rows"]  # already sorted fastest to slowest
    for row in rows:
        if time_sec <= row["time_sec"]:
            score = row["scores"][col]
            return score if score is not None else RUN_TABLE["max_score"]
    return 0  # slower than the worst listed time


def _get_rep_score(table, age: int, reps: int) -> int:
    col = age_to_column(age)
    rows = table["rows"]  # already sorted highest reps to lowest
    for row in rows:
        if reps >= row["reps"]:
            score = row["scores"][col]
            return score if score is not None else table["max_score"]
    return 0  # fewer reps than the lowest listed row


def get_pushup_score(age: int, reps: int) -> int:
    return _get_rep_score(PUSHUP_TABLE, age, reps)


def get_situp_score(age: int, reps: int) -> int:
    return _get_rep_score(SITUP_TABLE, age, reps)


def get_total_score(age: int, pushup_reps: int, situp_reps: int, run_time_sec: int) -> dict:
    pushup = get_pushup_score(age, pushup_reps)
    situp = get_situp_score(age, situp_reps)
    run = get_run_score(age, run_time_sec)
    return {
        "pushup_score": pushup,
        "situp_score": situp,
        "run_score": run,
        "total_score": pushup + situp + run,
    }


if __name__ == "__main__":
    # quick sanity check
    print(get_total_score(age=23, pushup_reps=40, situp_reps=45, run_time_sec=630))
