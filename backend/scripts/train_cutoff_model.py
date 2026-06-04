"""
train_cutoff_model.py

Trains a single global XGBoost cutoff-prediction model.

Train  : 2021-2024 (cutoffs.csv — after 2021 has been appended)
Validate: 2025     (cutoffs.csv)

Output (saved to backend/data/2.cleaned/):
    cutoff_model.pkl
    cutoff_model_meta.pkl
    label_encoders.pkl

Run from project root:
    python backend/scripts/train_cutoff_model.py
"""

import pickle
import pandas as pd
import numpy as np
import xgboost as xgb
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent.parent
DATA_DIR     = BASE_DIR / "data" / "cleaned"
CUTOFFS_CSV  = DATA_DIR / "cutoffs.csv"

# ── Load ──────────────────────────────────────────────────────────────────────
print("=" * 55)
print("CUTOFF MODEL TRAINING")
print("=" * 55)

df = pd.read_csv(CUTOFFS_CSV)
print(f"Loaded cutoffs.csv : {len(df):,} rows")
print(f"Years present      : {sorted(df['year'].unique())}")

if 2021 not in df["year"].values:
    print("\n[WARN] 2021 data not found in cutoffs.csv.")
    print("       Run extract_2021_allotment.py first, then re-run this script.")
    raise SystemExit(1)

# ── Historical features ───────────────────────────────────────────────────────
# Built from all rows except 2025 (no leakage)
hist = (
    df[df["year"] < 2025]
    .groupby(["college_code", "branch_code", "community"])
    .agg(
        hist_avg_closing = ("closing_rank", "mean"),
        hist_std_closing = ("closing_rank", "std"),
        hist_min_closing = ("closing_rank", "min"),
        hist_max_closing = ("closing_rank", "max"),
        hist_years       = ("closing_rank", "count"),
    )
    .reset_index()
    .fillna(0)
)

df = df.merge(
    hist, on=["college_code", "branch_code", "community"], how="left"
).fillna(0)

# ── Encode categoricals ───────────────────────────────────────────────────────
label_encoders = {}
for col in ["college_code", "branch_code", "community"]:
    le = LabelEncoder()
    df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# ── Temporal split ────────────────────────────────────────────────────────────
train_df = df[df["year"] <= 2024].copy()
val_df   = df[df["year"] == 2025].copy()

print(f"\nTrain (2021-2024) : {len(train_df):,}")
print(f"Validate (2025)   : {len(val_df):,}")

FEATURES = [
    "college_code_enc",
    "branch_code_enc",
    "community_enc",
    "year",
    "opening_rank",
    "seats_filled",
    "hist_avg_closing",
    "hist_std_closing",
    "hist_min_closing",
    "hist_max_closing",
    "hist_years",
]

X_train = train_df[FEATURES].values
y_train = train_df["closing_rank"].values.astype(float)
X_val   = val_df[FEATURES].values
y_val   = val_df["closing_rank"].values.astype(float)

# ── Sample weights: upweight sparse combos ────────────────────────────────────
# Sparse = seats_filled < 10 (not enough data, risk of poor prediction)
# We triple their weight instead of synthesizing fake data
sparse_mask    = train_df["seats_filled"] < 10
sample_weights = np.where(sparse_mask, 3.0, 1.0)

print(f"\nSparse combos (<10 seats): "
      f"{sparse_mask.sum():,} / {len(train_df):,} "
      f"({sparse_mask.mean()*100:.1f}%)")

# ── Train ─────────────────────────────────────────────────────────────────────
print("\nTraining …")

model = xgb.XGBRegressor(
    n_estimators          = 800,
    max_depth             = 8,
    learning_rate         = 0.05,
    subsample             = 0.8,
    colsample_bytree      = 0.8,
    min_child_weight      = 3,
    gamma                 = 0.1,
    random_state          = 42,
    early_stopping_rounds = 30,
    eval_metric           = "mae",
    verbosity             = 0,
)
model.fit(
    X_train, y_train,
    sample_weight = sample_weights,
    eval_set      = [(X_val, y_val)],
    verbose       = False,
)

# ── Evaluate ──────────────────────────────────────────────────────────────────
pred = model.predict(X_val)
r2   = r2_score(y_val, pred)
mae  = mean_absolute_error(y_val, pred)

print(f"\nVal R²  : {r2:.4f}")
print(f"Val MAE : {mae:.1f} closing rank")

# Per-community breakdown
print("\nMAE per community:")
for comm in sorted(val_df["community"].unique()):
    mask  = val_df["community"].values == comm
    mae_c = mean_absolute_error(y_val[mask], pred[mask])
    count = mask.sum()
    print(f"  {comm:<6}: {mae_c:>7.1f}   ({count:,} val rows)")

# Top-college accuracy (closing_rank < 1000)
top_mask = y_val < 1000
if top_mask.sum() > 0:
    mae_top = mean_absolute_error(y_val[top_mask], pred[top_mask])
    print(f"\nMAE for top colleges (closing_rank < 1000): {mae_top:.1f}")

# ── Save ──────────────────────────────────────────────────────────────────────
print("\nSaving …")

with open(DATA_DIR / "cutoff_model.pkl", "wb") as f:
    pickle.dump(model, f)
print("  Saved: cutoff_model.pkl")

with open(DATA_DIR / "label_encoders.pkl", "wb") as f:
    pickle.dump(label_encoders, f)
print("  Saved: label_encoders.pkl")

meta = {
    "train_years"    : sorted(train_df["year"].unique().tolist()),
    "val_year"       : 2025,
    "features"       : FEATURES,
    "target"         : "closing_rank",
    "val_r2"         : round(r2, 4),
    "val_mae"        : round(mae, 1),
    "sparse_weight"  : 3.0,
    "sparse_cutoff"  : 10,
}
with open(DATA_DIR / "cutoff_model_meta.pkl", "wb") as f:
    pickle.dump(meta, f)
print("  Saved: cutoff_model_meta.pkl")

print("\n[OK] Cutoff model training complete!")
