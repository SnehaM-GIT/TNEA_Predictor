"""
train_rank_model_hybrid.py

HYBRID RANK PREDICTION MODEL for TNEA

Combines:
1. Mark-wise analysis (75-200): avg/median/min/max/std ranks per mark per year
2. Community-wise analysis: how each community shifts predictions
3. Trend modeling: year-over-year changes with recent year weighting
4. Hybrid prediction: combined mark + community + trend
5. Range predictions: confidence intervals based on historical variance

Train: 2022-2024
Test:  2025 (validation)
Output: Rank + Range + Confidence + Historical cases used

Run from project root:
    python backend/scripts/train_rank_model_hybrid.py
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import interpolate
from sklearn.metrics import mean_absolute_error, median_absolute_error

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"

COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]

print("=" * 80)
print("TRAIN HYBRID RANK PREDICTION MODEL")
print("=" * 80)

# ── Load data ────────────────────────────────────────────────────────────────
print("\nLoading ranks.csv …")
ranks_df = pd.read_csv(DATA_DIR / "ranks.csv")

# Normalize community: BCM → BC
ranks_df["community"] = ranks_df["community"].replace("BCM", "BC")

train_df = ranks_df[ranks_df["year"] <= 2024].copy()
test_df  = ranks_df[ranks_df["year"] == 2025].copy()

print(f"Train (2022-2024): {len(train_df):,} rows")
print(f"Test (2025):       {len(test_df):,} rows")

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 1: MARK-WISE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("COMPONENT 1: MARK-WISE ANALYSIS (75-200)")
print("=" * 80)

# Round marks to 0.5 for grouping (to handle decimals)
train_df["mark_group"] = (train_df["aggregate_mark"] * 2).round() / 2

mark_analysis = {}
mark_range = np.arange(75, 200.5, 0.5)

print(f"Analyzing {len(mark_range)} mark points …")

for mark in mark_range:
    mark_students = train_df[train_df["mark_group"] == mark]
    
    if len(mark_students) < 5:  # Need minimum samples
        continue
    
    mark_analysis[mark] = {
        "total": len(mark_students),
        "avg_rank": mark_students["rank"].mean(),
        "median_rank": mark_students["rank"].median(),
        "min_rank": mark_students["rank"].min(),
        "max_rank": mark_students["rank"].max(),
        "std_rank": mark_students["rank"].std(),
        "year_dist": mark_students.groupby("year")["rank"].agg(["mean", "count"]).to_dict(),
    }

print(f"  Analyzed {len(mark_analysis)} mark points with sufficient data")

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 2: COMMUNITY-WISE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("COMPONENT 2: COMMUNITY-WISE ANALYSIS")
print("=" * 80)

community_analysis = {}

for community in COMMUNITIES:
    comm_data = train_df[train_df["community"] == community]
    
    if len(comm_data) < 100:
        print(f"  {community}: ⚠️  Only {len(comm_data)} rows — skipping")
        continue
    
    # For this community, calculate mark → rank relationship
    comm_data_grouped = comm_data.copy()
    comm_data_grouped["mark_group"] = (comm_data["aggregate_mark"] * 2).round() / 2
    
    comm_mark_stats = {}
    for mark in comm_data_grouped["mark_group"].unique():
        mark_comm_students = comm_data_grouped[comm_data_grouped["mark_group"] == mark]
        if len(mark_comm_students) >= 3:
            comm_mark_stats[mark] = {
                "avg_rank": mark_comm_students["rank"].mean(),
                "count": len(mark_comm_students),
                "std": mark_comm_students["rank"].std(),
            }
    
    # Calculate community multiplier (how much do ranks differ from overall avg)
    overall_avg_rank = train_df["rank"].mean()
    comm_avg_rank = comm_data["rank"].mean()
    community_multiplier = comm_avg_rank / overall_avg_rank if overall_avg_rank > 0 else 1.0
    
    community_analysis[community] = {
        "count": len(comm_data),
        "avg_rank": comm_avg_rank,
        "multiplier": community_multiplier,
        "mark_stats": comm_mark_stats,
        "year_dist": comm_data.groupby("year")["rank"].mean().to_dict(),
    }
    
    print(f"  {community}: {len(comm_data):,} students, "
          f"avg_rank={comm_avg_rank:.0f}, multiplier={community_multiplier:.3f}")

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 3: TREND MODELING
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("COMPONENT 3: TREND MODELING (Year-over-Year)")
print("=" * 80)

trend_model = {}
year_weights = {2022: 1.0, 2023: 2.0, 2024: 3.0}  # Recent years weighted more

for community in community_analysis.keys():
    year_dist = community_analysis[community]["year_dist"]
    
    years_sorted = sorted(year_dist.keys())
    
    if len(years_sorted) >= 2:
        # Calculate trend
        trend = "stable"
        if len(years_sorted) >= 3:
            change_23_24 = year_dist[2024] - year_dist[2023]
            change_22_23 = year_dist[2023] - year_dist[2022]
            
            if abs(change_23_24) > 100:  # Significant change
                trend = "improving" if change_23_24 < 0 else "worsening"
        
        trend_model[community] = {
            "trend": trend,
            "year_dist": year_dist,
            "weights": year_weights,
        }
        
        print(f"  {community}: {trend}")
        for yr in years_sorted:
            print(f"    {yr}: avg_rank = {year_dist[yr]:.0f}")

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 4: INTERPOLATION FOR SPARSE DATA
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("COMPONENT 4: MARK INTERPOLATION (handling sparse data)")
print("=" * 80)

# Create smoothed curves for each community
interpolators = {}

for community in community_analysis.keys():
    comm_marks = sorted(community_analysis[community]["mark_stats"].keys())
    comm_ranks = [community_analysis[community]["mark_stats"][m]["avg_rank"] for m in comm_marks]
    
    if len(comm_marks) >= 3:
        # Create interpolator (cubic spline)
        try:
            f = interpolate.interp1d(comm_marks, comm_ranks, kind="cubic", fill_value="extrapolate")
            interpolators[community] = f
            print(f"  {community}: Created interpolator for {len(comm_marks)} mark points")
        except:
            print(f"  {community}: ⚠️  Interpolation failed")

# ══════════════════════════════════════════════════════════════════════════════
# HYBRID PREDICTION FUNCTION
# ══════════════════════════════════════════════════════════════════════════════
def predict_rank_hybrid(aggregate_mark, community, mark_analysis, community_analysis, 
                       interpolators, trend_model, confidence_width=100):
    """
    Predict rank using hybrid approach.
    
    Returns:
      rank: predicted rank
      rank_range: (min, max) confidence range
      confidence: confidence score 0-100
      components: dict of component contributions
    """
    
    components = {}
    
    # ── Component 1: Mark-based prediction ──────────────────────────────────
    mark_rounded = round(aggregate_mark * 2) / 2
    
    if mark_rounded in mark_analysis:
        mark_pred = mark_analysis[mark_rounded]["avg_rank"]
        mark_std = mark_analysis[mark_rounded]["std_rank"]
        mark_confidence = min(mark_analysis[mark_rounded]["total"] / 50, 1.0)  # More samples = higher confidence
        components["mark_pred"] = mark_pred
        components["mark_std"] = mark_std
    else:
        # Use interpolation if available
        if community in interpolators:
            try:
                mark_pred = float(interpolators[community](aggregate_mark))
                mark_std = 500  # Conservative estimate for interpolated values
                mark_confidence = 0.5
                components["mark_pred"] = mark_pred
                components["mark_std"] = mark_std
                components["method"] = "interpolated"
            except:
                return None
        else:
            return None
    
    # ── Component 2: Community adjustment ──────────────────────────────────
    if community in community_analysis:
        comm_multiplier = community_analysis[community]["multiplier"]
        components["community_multiplier"] = comm_multiplier
        community_adjusted = mark_pred * comm_multiplier
    else:
        community_adjusted = mark_pred
    
    # ── Component 3: Trend adjustment ──────────────────────────────────────
    trend_adjustment = 1.0
    if community in trend_model:
        trend_info = trend_model[community]
        # Apply weighted trend
        if trend_info["trend"] == "improving":
            trend_adjustment = 0.98  # Slight improvement
        elif trend_info["trend"] == "worsening":
            trend_adjustment = 1.02  # Slight worsening
        components["trend"] = trend_info["trend"]
        components["trend_adjustment"] = trend_adjustment
    
    # ── Final prediction ───────────────────────────────────────────────────
    final_pred = community_adjusted * trend_adjustment
    final_pred = max(1, int(final_pred))
    
    # ── Confidence interval ────────────────────────────────────────────────
    # Use historical std dev, adjusted by confidence
    confidence_interval = max(50, min(200, mark_std * (1 - mark_confidence)))
    
    rank_min = max(1, int(final_pred - confidence_interval / 2))
    rank_max = int(final_pred + confidence_interval / 2)
    
    # Confidence score
    confidence_pct = int(mark_confidence * 100)
    
    return {
        "rank": final_pred,
        "rank_min": rank_min,
        "rank_max": rank_max,
        "confidence": confidence_pct,
        "components": components,
    }

# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION ON 2025 DATA
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("VALIDATION ON 2025 DATA")
print("=" * 80)

predictions = []
errors = []

for idx, row in test_df.iterrows():
    pred = predict_rank_hybrid(
        row["aggregate_mark"],
        row["community"],
        mark_analysis,
        community_analysis,
        interpolators,
        trend_model
    )
    
    if pred:
        predictions.append(pred)
        error = abs(pred["rank"] - row["rank"])
        errors.append(error)

errors = np.array(errors)

print(f"\nTested {len(predictions):,} out of {len(test_df):,} 2025 students")
print(f"  MAE  : {errors.mean():.1f} ranks")
print(f"  RMSE : {np.sqrt((errors**2).mean()):.1f} ranks")
print(f"  Median AE: {np.median(errors):.1f} ranks")
print(f"  Std Dev   : {errors.std():.1f} ranks")

# Per-community breakdown
print(f"\nPer-community accuracy:")
for community in sorted(test_df["community"].unique()):
    comm_test = test_df[test_df["community"] == community]
    comm_errors = []
    
    for idx, row in comm_test.iterrows():
        pred = predict_rank_hybrid(
            row["aggregate_mark"],
            row["community"],
            mark_analysis,
            community_analysis,
            interpolators,
            trend_model
        )
        if pred:
            comm_errors.append(abs(pred["rank"] - row["rank"]))
    
    if comm_errors:
        mae = np.mean(comm_errors)
        print(f"  {community}: MAE={mae:.0f} ({len(comm_errors)} samples)")

# ══════════════════════════════════════════════════════════════════════════════
# SAVE MODEL
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("SAVING MODEL")
print("=" * 80)

model_data = {
    "mark_analysis": mark_analysis,
    "community_analysis": community_analysis,
    "interpolators": interpolators,
    "trend_model": trend_model,
    "train_years": [2022, 2023, 2024],
    "test_year": 2025,
    "val_mae": errors.mean(),
    "val_rmse": np.sqrt((errors**2).mean()),
    "val_median_ae": np.median(errors),
}

with open(DATA_DIR / "rank_model_hybrid.pkl", "wb") as f:
    pickle.dump(model_data, f)
print("  Saved: rank_model_hybrid.pkl")

print("\n✅ Model training complete!")
print(f"\nValidation Results:")
print(f"  MAE: {errors.mean():.1f} ranks")
print(f"  Confidence: This model explains rank distributions based on historical patterns")
print(f"  Next: Test with predict_rank_hybrid() function")