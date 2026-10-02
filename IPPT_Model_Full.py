import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

np.random.seed(42)

n_samples = 500

age = np.random.randint(18, 40, n_samples)
current_pushups = np.random.randint(10, 60, n_samples)
current_situps = np.random.randint(20, 70, n_samples)
current_runtime = np.random.randint(600, 900, n_samples)
training_frequency = np.random.randint(0, 7, n_samples)
training_duration = np.random.randint(0, 13, n_samples)
adherence_pct = np.random.randint(30, 101, n_samples)

adherence_multiplier = adherence_pct / 100

future_pushups = (
    current_pushups
    + training_frequency * training_duration * 0.30 * adherence_multiplier
    - 0.05 * current_pushups
    - 0.10 * (age - 18)
    + np.random.normal(0, 3, n_samples)
)
future_pushups = np.clip(future_pushups, 0, None)

future_situps = (
    current_situps
    + training_frequency * training_duration * 0.25 * adherence_multiplier
    - 0.04 * current_situps
    - 0.08 * (age - 18)
    + np.random.normal(0, 3, n_samples)
)
future_situps = np.clip(future_situps, 0, None)

future_runtime = (
    current_runtime
    - training_frequency * training_duration * 1.2 * adherence_multiplier
    + 0.5 * (age - 18)
    + np.random.normal(0, 10, n_samples)
)
future_runtime = np.clip(future_runtime, 300, None)

df = pd.DataFrame({
    "age": age,
    "current_pushups": current_pushups,
    "current_situps": current_situps,
    "current_runtime": current_runtime,
    "training_frequency": training_frequency,
    "training_duration": training_duration,
    "adherence_pct": adherence_pct,
    "future_pushups": future_pushups,
    "future_situps": future_situps,
    "future_runtime": future_runtime,
})

df.head()

feature_cols = ["age", "current_pushups", "current_situps",
                "current_runtime", "training_frequency", "training_duration",
                "adherence_pct"]

X = df[feature_cols]
targets = {
    "pushups": df["future_pushups"],
    "situps": df["future_situps"],
    "runtime": df["future_runtime"],
}

models = {}
results = {}

for name, y in targets.items():
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LinearRegression()
    model.fit(X_train, y_train)
    models[name] = model

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    cv_mae = -cross_val_score(model, X, y, cv=5, scoring="neg_mean_absolute_error")

    results[name] = {
        "MAE": mae, "RMSE": rmse, "R2": r2,
        "CV_MAE_mean": cv_mae.mean(), "CV_MAE_per_fold": cv_mae
    }

    print(f"=== {name.upper()} ===")
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R^2:  {r2:.3f}")
    print(f"5-fold CV MAE: {cv_mae.mean():.2f}  (per fold: {np.round(cv_mae, 2)})")
    print()

for name, model in models.items():
    print(f"=== {name.upper()} coefficients ===")
    for feature, coef in zip(feature_cols, model.coef_):
        print(f"  {feature}: {coef:.3f}")
    print(f"  intercept: {model.intercept_:.3f}")
    print()

example_user = pd.DataFrame({
    "age": [22],
    "current_pushups": [30],
    "current_situps": [35],
    "current_runtime": [720],
    "training_frequency": [4],
    "training_duration": [6],
    "adherence_pct": [90],
})

pred_pushups = models["pushups"].predict(example_user)[0]
pred_situps = models["situps"].predict(example_user)[0]
pred_runtime = models["runtime"].predict(example_user)[0]

mins, secs = divmod(int(pred_runtime), 60)

print("A 22-year-old with 30 push-ups, 35 sit-ups, 12:00 run,")
print("PLANNING 4x/week for 6 weeks, at 90% adherence, is predicted to reach:")
print(f"  Push-ups: {pred_pushups:.1f}")
print(f"  Sit-ups:  {pred_situps:.1f}")
print(f"  Run time: {mins}:{secs:02d}")

example_user_low_adherence = example_user.copy()
example_user_low_adherence["adherence_pct"] = [50]

pred_pushups_low = models["pushups"].predict(example_user_low_adherence)[0]
pred_situps_low = models["situps"].predict(example_user_low_adherence)[0]
pred_runtime_low = models["runtime"].predict(example_user_low_adherence)[0]

mins_low, secs_low = divmod(int(pred_runtime_low), 60)

print("Same plan, but only 50% adherence:")
print(f"  Push-ups: {pred_pushups_low:.1f}  (vs {pred_pushups:.1f} at 90% adherence)")
print(f"  Sit-ups:  {pred_situps_low:.1f}  (vs {pred_situps:.1f} at 90% adherence)")
print(f"  Run time: {mins_low}:{secs_low:02d}  (vs {mins}:{secs:02d} at 90% adherence)")

from sklearn.ensemble import RandomForestRegressor

rf_models = {}
rf_results = {}

for name, y in targets.items():
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    rf_model = RandomForestRegressor(n_estimators=200, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_models[name] = rf_model

    y_pred = rf_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    cv_mae = -cross_val_score(rf_model, X, y, cv=5, scoring="neg_mean_absolute_error")

    rf_results[name] = {
        "MAE": mae, "RMSE": rmse, "R2": r2, "CV_MAE_mean": cv_mae.mean()
    }

    print(f"=== {name.upper()} (Random Forest) ===")
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R^2:  {r2:.3f}")
    print(f"5-fold CV MAE: {cv_mae.mean():.2f}")
    print()

comparison_rows = []
for name in targets.keys():
    comparison_rows.append({
        "target": name,
        "LinearRegression_MAE": results[name]["MAE"],
        "RandomForest_MAE": rf_results[name]["MAE"],
        "LinearRegression_R2": results[name]["R2"],
        "RandomForest_R2": rf_results[name]["R2"],
    })

comparison_df = pd.DataFrame(comparison_rows)
comparison_df

import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for ax, name in zip(axes, targets.keys()):
    importances = rf_models[name].feature_importances_
    imp_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": importances
    }).sort_values("importance", ascending=True)

    ax.barh(imp_df["feature"], imp_df["importance"])
    ax.set_title(f"Feature importance: {name}")
    ax.set_xlabel("Importance")

plt.tight_layout()
plt.show()
