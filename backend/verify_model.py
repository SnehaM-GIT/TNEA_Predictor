import pandas as pd
import numpy as np
import pickle
from scipy import stats

# ─────────────────────────────────────────────
# LOAD MODELS + DATA
# ─────────────────────────────────────────────
with open('data/rank_model.pkl',       'rb') as f: rank_model = pickle.load(f)
with open('data/rank_model_meta.pkl',  'rb') as f: rank_meta  = pickle.load(f)
with open('data/cutoff_model_meta.pkl','rb') as f: cutoff_meta= pickle.load(f)

le_community  = rank_meta['le_community']
feature_cols  = rank_meta['feature_cols']
predictions   = cutoff_meta['predictions_df']   # pre-computed 2026 cutoffs
if 'allotted_category' in predictions.columns and 'community' not in predictions.columns:
    predictions = predictions.rename(columns={'allotted_category': 'community'})

cutoffs  = pd.read_csv('data/cutoffs.csv')
colleges = pd.read_csv('data/college_codes.csv')
courses  = pd.read_csv('data/course_codes.csv')

# ─────────────────────────────────────────────
# STEP 1: PREDICT RANK FROM MARKS
# (only called when rank not provided)
# ─────────────────────────────────────────────
def predict_rank_from_marks(aggregate_mark: float, community: str) -> int:
    try:
        comm_enc = le_community.transform([community])[0]
    except ValueError:
        print(f"[!] Invalid community '{community}'. Valid: {list(le_community.classes_)}")
        return None

    yr_mean  = rank_meta['latest_yr_mean']
    yr_std   = rank_meta['latest_yr_std']
    yr_total = rank_meta['latest_yr_total']

    mark_norm     = (aggregate_mark - yr_mean) / (yr_std + 1e-6)
    percentile_y  = stats.norm.cdf(mark_norm)
    percentile_yc = rank_meta['comm_pct_proxy'].get(community, percentile_y)

    features = pd.DataFrame([{
        'aggregate_mark' : aggregate_mark,
        'mark_sq'        : aggregate_mark ** 2,
        'mark_norm'      : mark_norm,
        'community_encoded': comm_enc,
        'percentile_yc'  : percentile_yc,
        'percentile_y'   : percentile_y,
        'yr_total'       : yr_total,
        'yr_mean'        : yr_mean,
        'yr_std'         : yr_std,
    }])[feature_cols]

    return max(1, int(rank_model.predict(features)[0]))


# ─────────────────────────────────────────────
# STEP 2: PROBABILITY CALCULATION
# ─────────────────────────────────────────────
def compute_probability(student_rank, predicted_closing, std_hist,
                        college_code, branch_code, community) -> float:
    std = max(std_hist, 100)
    gap = predicted_closing - student_rank
    ml_prob = 1 / (1 + np.exp(-gap / std))

    hist = cutoffs[
        (cutoffs['college_code']      == college_code) &
        (cutoffs['branch_code']       == branch_code)  &
        (cutoffs['allotted_category'] == community)
    ]
    hist_prob = (hist['closing_rank'] >= student_rank).sum() / len(hist) if len(hist) > 0 else ml_prob

    return round((0.6 * ml_prob + 0.4 * hist_prob) * 100, 1)


def enrich(df):
    df = df.merge(
        colleges[['college_code','college_name_full','college_name_short','college_type','district']],
        on='college_code', how='left'
    )
    df = df.merge(courses[['branch_code','branch_name']], on='branch_code', how='left')
    return df


# ─────────────────────────────────────────────
# MAIN PREDICTION FUNCTION
# ─────────────────────────────────────────────
def predict(
    aggregate_mark : float,
    community      : str,
    rank           : int   = None,   # optional — if not given, predicted from marks
    college_code   : int   = None,   # optional
    branch_code    : str   = None,   # optional
    top_n          : int   = 5,
):
    """
    Predict colleges / courses for a TNEA student.

    Required : aggregate_mark, community
    Optional : rank (uses marks to predict if not given)
               college_code, branch_code

    Paths:
      A. Neither college nor branch  → Top N best combos
      B. branch_code only            → Top N colleges for that branch
      C. college_code only           → Top N branches at that college
      D. Both                        → Single probability %
    """
    print(f"\n{'='*65}")
    print(f"  Marks : {aggregate_mark} | Community: {community}", end="")
    if rank:         print(f" | Rank: {rank} (given)", end="")
    if college_code: print(f" | College: {college_code}", end="")
    if branch_code:  print(f" | Branch: {branch_code}", end="")
    print(f"\n{'='*65}")

    # ── Resolve rank ───────────────────────────
    if rank:
        use_rank = rank
        print(f"\n  Rank    : {use_rank} (provided directly)")
    else:
        use_rank = predict_rank_from_marks(aggregate_mark, community)
        if use_rank is None: return
        print(f"\n  Rank    : {use_rank} (predicted from marks {aggregate_mark})")
        print(f"  Range   : {max(1, use_rank - 500)} - {use_rank + 500}")

    # ── Filter predictions by community ────────
    pool = predictions[predictions['community'] == community].copy()
    if pool.empty:
        print(f"[!] No data for community '{community}'")
        return

    pool = enrich(pool)

    # ── Path D: both given ─────────────────────
    if college_code and branch_code:
        row = pool[(pool['college_code'] == college_code) & (pool['branch_code'] == branch_code)]
        if row.empty:
            print("[!] No data found for that college + branch + community combo")
            return
        r    = row.iloc[0]
        prob = compute_probability(use_rank, r['predicted_closing_2026'], r['std_closing_hist'],
                                   college_code, branch_code, community)
        print(f"\n  College  : {r.get('college_name_full','N/A')}")
        print(f"  Branch   : {r.get('branch_name','N/A')} ({branch_code})")
        print(f"  2026 Predicted Cutoff : {int(r['predicted_closing_2026'])}")
        print(f"  Your Rank             : {use_rank}")
        print(f"\n  >> Probability: {prob}%")
        return

    # ── Path C: college only ───────────────────
    if college_code:
        pool  = pool[pool['college_code'] == college_code]
        label = f"Top {top_n} branches at College {college_code}"

    # ── Path B: branch only ────────────────────
    elif branch_code:
        pool  = pool[pool['branch_code'] == branch_code]
        label = f"Top {top_n} colleges for branch '{branch_code}'"

    # ── Path A: neither ────────────────────────
    else:
        label = f"Top {top_n} college + branch combos"

    if pool.empty:
        print("[!] No data found for given inputs")
        return

    # Compute probability for all rows
    pool = pool.copy()
    pool['probability'] = pool.apply(
        lambda r: compute_probability(
            use_rank, r['predicted_closing_2026'], r['std_closing_hist'],
            r['college_code'], r['branch_code'], community
        ), axis=1
    )

    pool = pool[pool['probability'] > 0].sort_values(
        ['probability','predicted_closing_2026'], ascending=[False, True]
    ).head(top_n)

    if pool.empty:
        print(f"[!] No reachable colleges found for rank {use_rank}")
        return

    print(f"\n  {label}:")
    print(f"{'-'*65}")

    for i, (_, row) in enumerate(pool.iterrows(), 1):
        print(f"\n  {i}. [{row['probability']}%]  {row.get('college_name_full','N/A')}")
        print(f"     Branch  : {row.get('branch_name','N/A')} ({row['branch_code']})")
        print(f"     Type    : {row.get('college_type','N/A')} | {row.get('district','N/A')}")
        print(f"     2026 Predicted Cutoff : {int(row['predicted_closing_2026'])}")
        print(f"     Your Rank             : {use_rank}")

    print(f"\n{'='*65}")


# ─────────────────────────────────────────────
# TEST ALL PATHS
# ─────────────────────────────────────────────
if __name__ == '__main__':

    # Path A — marks only, rank predicted automatically
    predict(aggregate_mark=198, community='OC')

    # Path A — marks + rank given directly
    predict(aggregate_mark=198, community='OC', rank=785)

    # Path B — marks only + branch preference
    predict(aggregate_mark=160, community='BC', branch_code='CS')

    # Path C — marks only + college preference
    predict(aggregate_mark=160, community='BC', college_code=1)

    # Path D — marks + specific college + branch → probability
    predict(aggregate_mark=198, community='OC', college_code=1, branch_code='CS')

    # Path D — with rank given directly
    predict(aggregate_mark=198, community='OC', rank=785, college_code=1, branch_code='CS')