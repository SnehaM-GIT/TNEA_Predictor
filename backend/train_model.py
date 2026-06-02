import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

data_dir   = 'data'
model_file = os.path.join(data_dir, 'rank_model.pkl')
meta_file  = os.path.join(data_dir, 'rank_model_meta.pkl')

# ─────────────────────────────────────────────
# 1. LOAD
# ─────────────────────────────────────────────
print("Loading ranks data...")
df = pd.read_csv(os.path.join(data_dir, 'ranks.csv'), low_memory=False)
df = df[['aggregate_mark', 'community', 'year', 'rank']].dropna()
df['aggregate_mark'] = pd.to_numeric(df['aggregate_mark'], errors='coerce')
df['rank']           = pd.to_numeric(df['rank'], errors='coerce')
df['year']           = pd.to_numeric(df['year'], errors='coerce')
df = df.dropna()
print(f"Shape: {df.shape}")

# ─────────────────────────────────────────────
# 2. ENCODE
# ─────────────────────────────────────────────
le = LabelEncoder()
df['community_encoded'] = le.fit_transform(df['community'])
print(f"Community mapping: {dict(zip(le.classes_, le.transform(le.classes_)))}")

# ─────────────────────────────────────────────
# 3. FEATURE ENGINEERING
# (year used internally, NOT exposed to user)
# ─────────────────────────────────────────────
print("\nEngineering features...")

# Percentile within year + community (strongest signal)
df['percentile_yc'] = df.groupby(['year', 'community'])['aggregate_mark'].rank(pct=True)
df['percentile_y']  = df.groupby('year')['aggregate_mark'].rank(pct=True)

# Year stats for normalisation
ys = df.groupby('year')['aggregate_mark'].agg(['mean','std']).reset_index()
ys.columns = ['year','yr_mean','yr_std']
df = df.merge(ys, on='year', how='left')
df['mark_norm']    = (df['aggregate_mark'] - df['yr_mean']) / (df['yr_std'] + 1e-6)
df['mark_sq']      = df['aggregate_mark'] ** 2

# Total students per year (competition level)
yc = df.groupby('year').size().reset_index(name='yr_total')
df = df.merge(yc, on='year', how='left')

# ─────────────────────────────────────────────
# 4. FEATURES (year used here but NOT a user input)
# ─────────────────────────────────────────────
feature_cols = [
    'aggregate_mark',
    'mark_sq',
    'mark_norm',
    'community_encoded',
    'percentile_yc',
    'percentile_y',
    'yr_total',
    'yr_mean',
    'yr_std',
]

X = df[feature_cols]
y = df['rank']

# ─────────────────────────────────────────────
# 5. SPLIT BY YEAR (realistic: train on past, test on latest)
# ─────────────────────────────────────────────
latest = df['year'].max()
X_train, y_train = X[df['year'] != latest], y[df['year'] != latest]
X_test,  y_test  = X[df['year'] == latest], y[df['year'] == latest]
print(f"Train: {len(X_train)} | Test: {len(X_test)}")

# ─────────────────────────────────────────────
# 6. TRAIN
# ─────────────────────────────────────────────
print("\nTraining rank model...")
model = xgb.XGBRegressor(
    n_estimators=500, max_depth=8, learning_rate=0.05,
    subsample=0.85, colsample_bytree=0.85,
    min_child_weight=5, gamma=0.1,
    reg_alpha=0.1, reg_lambda=1.0,
    random_state=42, early_stopping_rounds=30,
    eval_metric='rmse', n_jobs=-1,
)
model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

# ─────────────────────────────────────────────
# 7. EVALUATE
# ─────────────────────────────────────────────
y_pred = model.predict(X_test)
rmse   = np.sqrt(mean_squared_error(y_test, y_pred))
mae    = mean_absolute_error(y_test, y_pred)
r2     = r2_score(y_test, y_pred)
w500   = np.mean(np.abs(y_test - y_pred) <= 500)  * 100
w1000  = np.mean(np.abs(y_test - y_pred) <= 1000) * 100

print(f"\n{'='*45}")
print(f"Rank Model Performance:")
print(f"  RMSE             : {rmse:.2f}")
print(f"  MAE              : {mae:.2f}")
print(f"  R²               : {r2:.4f}")
print(f"  Within ±500 ranks: {w500:.1f}%")
print(f"  Within ±1000     : {w1000:.1f}%")
print(f"{'='*45}")

# ─────────────────────────────────────────────
# 8. SAVE (with latest year stats as default for 2026 inference)
# ─────────────────────────────────────────────
latest_stats = ys[ys['year'] == latest].iloc[0]
latest_total = yc[yc['year'] == latest].iloc[0]['yr_total']

# Community-level percentile proxy: avg percentile per community for latest yr
comm_pct = df[df['year'] == latest].groupby('community')['percentile_y'].mean().to_dict()

meta = {
    'le_community'  : le,
    'feature_cols'  : feature_cols,
    'latest_yr_mean': float(latest_stats['yr_mean']),
    'latest_yr_std' : float(latest_stats['yr_std']),
    'latest_yr_total': int(latest_total),
    'comm_pct_proxy': comm_pct,   # used to estimate percentile when year unknown
}

with open(model_file, 'wb') as f: pickle.dump(model, f)
with open(meta_file,  'wb') as f: pickle.dump(meta, f)

print(f"\nrank_model.pkl saved")
print(f"rank_model_meta.pkl saved")
print("Done!")