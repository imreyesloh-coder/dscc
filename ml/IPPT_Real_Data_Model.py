import re
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

# ---------------------------------------------------------
# 1. Load the CSV
#    In Colab this opens a "Choose Files" button; just pick the CSV.
#    Outside Colab, pass the file path as an argument.
# ---------------------------------------------------------
try:
    from google.colab import files
    uploaded = files.upload()
    CSV_PATH = list(uploaded.keys())[0]
except ImportError:
    CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "responses.csv"

raw = pd.read_csv(CSV_PATH)


# ---------------------------------------------------------
# 2. Find each column by keywords in its header (order doesn't matter)
# ---------------------------------------------------------
def find(*keywords):
    for c in raw.columns:
        low = c.lower()
        if all(k in low for k in keywords):
            return c
    raise KeyError(f"No column found with keywords: {keywords}")


age_col = [c for c in raw.columns if c.strip().lower() == "age"][0]
mapping = {
    "age": age_col,
    "new_pushups": find("most recent", "push"),
    "new_situps": find("most recent", "sit"),
    "new_run": find("most recent", "2.4"),
    "prev_pushups": find("previous", "push"),
    "prev_situps": find("previous", "sit"),
    "prev_run": find("previous", "2.4"),
    "months": find("months between"),
    "train_days": find("days per week"),
    "adherence": find("actually complete"),
}
d = pd.DataFrame({k: raw[v] for k, v in mapping.items()})  # names are never loaded
d["row"] = d.index + 2  # spreadsheet row number, for reporting


# ---------------------------------------------------------
# 3. Turn messy text answers into numbers
# ---------------------------------------------------------
def parse_run(x):
    s = str(x).strip()
    try:
        if ":" in s:
            m, sec = s.split(":")[:2]
            return int(m) * 60 + int(sec)
        if "." in s:
            m, sec = s.split(".")[:2]
            return int(m) * 60 + int(sec.ljust(2, "0")[:2])
        v = float(s)
        return v if v > 60 else v * 60
    except Exception:
        return np.nan


def parse_range(x):
    s = str(x)
    nums = re.findall(r"\d+\.?\d*", s)
    if not nums:
        return np.nan
    if "<" in s:
        return float(nums[0]) / 2
    if len(nums) == 1:
        return float(nums[0])
    return (float(nums[0]) + float(nums[1])) / 2


def parse_months(x):
    s = str(x).lower()
    nums = re.findall(r"\d+\.?\d*", s)
    if not nums:
        return np.nan
    if "year" in s:
        y = re.search(r"(\d+\.?\d*)\s*year", s)
        mo = re.search(r"(\d+\.?\d*)\s*month", s)
        return (float(y.group(1)) * 12 if y else 0) + (float(mo.group(1)) if mo else 0)
    if "week" in s:
        return float(nums[0]) / 4.3
    return float(nums[0])


for c in ["new_run", "prev_run"]:
    d[c] = d[c].apply(parse_run)
for c in ["train_days", "adherence"]:
    d[c] = d[c].apply(parse_range)
d["months"] = d["months"].apply(parse_months)
for c in ["age", "new_pushups", "new_situps", "prev_pushups", "prev_situps"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")

print(f"Responses in file: {len(d)}")
print()

# ---------------------------------------------------------
# 4. Per-component cleaning, then leave-one-out testing
# ---------------------------------------------------------
targets = {
    "pushups": ("prev_pushups", "new_pushups", "reps"),
    "situps": ("prev_situps", "new_situps", "reps"),
    "run (sec)": ("prev_run", "new_run", "run"),
}

rows = []
fitted = {}
for label, (prev_col, new_col, kind) in targets.items():
    need = ["age", prev_col, new_col, "months", "train_days", "adherence"]
    sub = d.dropna(subset=need)

    bad = (sub["months"] <= 0) | (sub["months"] > 36)
    if kind == "reps":
        bad |= (sub[prev_col] > 80) | (sub[new_col] > 80)
    else:
        bad |= (sub[prev_col] < 360) | (sub[prev_col] > 1200)
        bad |= (sub[new_col] < 360) | (sub[new_col] > 1200)
    sub = sub[~bad].reset_index(drop=True)

    dropped = sorted(set(d["row"]) - set(sub["row"]))
    print(f"{label}: using {len(sub)} responses "
          f"(dropped spreadsheet rows {dropped})")

    X = sub[["age", prev_col, "months", "train_days", "adherence"]]
    y = sub[new_col] - sub[prev_col]  # the CHANGE between the two IPPTs
    print(f"   average actual change: {y.mean():+.1f}")

    models = {
        "No change": None,
        "Average change": DummyRegressor(strategy="mean"),
        "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=5.0)),
        "Random Forest": RandomForestRegressor(
            n_estimators=200, min_samples_leaf=3, random_state=42),
    }
    result = {"target": label}
    for name, model in models.items():
        if model is None:
            pred = np.zeros(len(y))
        else:
            pred = cross_val_predict(model, X, y, cv=LeaveOneOut())
        result[name] = mean_absolute_error(y, pred)
    rows.append(result)
    fitted[label] = (X, y)

results = pd.DataFrame(rows).set_index("target").round(2)
print()
print("Average error (MAE) when predicting each person's change:")
print(results)
print()
print("A model is only useful if it beats 'No change' and 'Average change'.")

# ---------------------------------------------------------
# 5. What the simple model learned (fit on all usable rows)
# ---------------------------------------------------------
print()
for label, (X, y) in fitted.items():
    model = make_pipeline(StandardScaler(), Ridge(alpha=5.0)).fit(X, y)
    coefs = {k: round(float(v), 2) for k, v in zip(X.columns, model[-1].coef_)}
    print(f"{label}: {coefs}")
