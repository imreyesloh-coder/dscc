import csv
import os

_DIR = os.path.dirname(os.path.abspath(__file__))

_AGE_BOUNDS = [22, 25, 28, 31, 34, 37, 40, 43, 46, 49, 52, 55, 58]


def _read_csv(filename):
    with open(os.path.join(_DIR, filename), newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [row for row in reader if row and row[0].strip()]
    return header[1:], rows


def _cells(row):
    """Score cells of one CSV row as ints, with blank cells as None."""
    return [int(c) if c.strip() else None for c in row[1:]]


def _load_rep_table(filename):
    """Rows sorted from the highest reps to the lowest."""
    categories, rows = _read_csv(filename)
    table = [{"reps": int(r[0]), "scores": _cells(r)} for r in rows]
    table.sort(key=lambda r: r["reps"], reverse=True)
    return {"categories": categories, "rows": table, "max_score": table[0]["scores"][0]}


def _parse_time(text):
    """'8:30' -> 510"""
    minutes, seconds = text.strip().split(":")
    return int(minutes) * 60 + int(seconds)


def _load_run_table(filename):
    """Rows sorted from the fastest time to the slowest."""
    categories, rows = _read_csv(filename)
    table = [{"time_sec": _parse_time(r[0]), "scores": _cells(r)} for r in rows]
    table.sort(key=lambda r: r["time_sec"])
    return {"categories": categories, "rows": table, "max_score": table[0]["scores"][0]}


RUN_TABLE = _load_run_table("run_2_4km.csv")
PUSHUP_TABLE = _load_rep_table("pushup.csv")
SITUP_TABLE = _load_rep_table("situp.csv")
AGE_CATEGORIES = RUN_TABLE["categories"]


def age_to_column(age: int) -> int:
    """Maps an age to the correct column index (0-13) in the tables."""
    for i, upper in enumerate(_AGE_BOUNDS):
        if age < upper:
            return i
    return len(AGE_CATEGORIES) - 1  # 58-60 and above


def get_run_score(age: int, time_sec: int) -> int:
    """time_sec: actual 2.4km finish time in seconds. Lower is better."""
    col = age_to_column(age)
    for row in RUN_TABLE["rows"]:
        if time_sec <= row["time_sec"]:
            score = row["scores"][col]
            return score if score is not None else RUN_TABLE["max_score"]
    return 0  # slower than the slowest listed time


def _get_rep_score(table, age: int, reps: int) -> int:
    col = age_to_column(age)
    for row in table["rows"]:
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
    print(get_total_score(age=23, pushup_reps=40, situp_reps=45, run_time_sec=630))
