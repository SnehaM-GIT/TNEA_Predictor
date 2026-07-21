"""
seat_adjustment.py — post-hoc adjustment layer on top of cutoff_predictor.pkl's
output (cutoff_lookup_2026.csv). Does NOT retrain or touch the model.

Seat matrix source: data/raw/GENERAL_ACADEMIC_SEAT_MATRIX_BEFORE_SPECIAL_
RESERVATION_COUNSELLING_2026.pdf, parsed by extract_seat_matrix.py into
data/cleaned/seat_matrix_2026.csv (college_code, college_name, branch_code,
branch_name, OC, BC, BCM, MBC, SC, SCA, ST, TOTAL).

The seat matrix has a BCM column separate from BC, but cutoffs.csv (2022-2025)
and the rest of the prediction pipeline only ever use a merged "BC" community
(BCM is collapsed into BC upstream, before cutoffs.csv was cleaned — no BCM
rows exist there at all). To keep the adjustment comparable to the historical
baseline it's dividing against, BC+BCM 2026 seats are summed into one "BC"
figure here.

For each (college_code, branch_code, community) combo:
  seat_adjustment_factor = clip(seats_2026 / historical_avg_seats, 0.5, 2.0)

historical_avg_seats = mean of yearly seats_filled totals, 2022-2025
(cutoffs.csv). If a combo has no historical rows (new branch/college),
falls back to the mean historical seat count for that branch_code across
colleges of the same tier (TIER_RANK, from college_type) that do have data;
if even that is empty, falls back to the branch-wide mean across all tiers.
Either fallback sets limited_data=True. If no seat data exists anywhere for
the branch, factor defaults to 1.0 (neutral) with limited_data=True.

sample_years_count = how many of the 4 years (2022-2025) had a nonzero seat
count for THIS EXACT combo (not the fallback pools). A combo with only 1
observed year (often a single seat filled once) produces a historical_avg
based on one data point — dividing seats_2026 by that is noise, not signal
(e.g. hist_avg=1.00 from one lucky seat vs seats_2026=30 -> raw ratio 30x).
If sample_years_count < MIN_SAMPLE_YEARS, seat_adjustment_factor is forced
to 1.0 (neutral, no adjustment) regardless of what the ratio would have
been, and limited_data is set True.

Combos in the 2026 seat matrix with no cutoff_lookup_2026.csv row at all
(brand-new offering) get a base closing rank imputed the same way: mean
predicted_closing_rank_2026 for that branch_code among same-tier colleges
that do have a model prediction (limited_data=True).
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"

SEAT_MATRIX_PATH = DATA_DIR / "seat_matrix_2026.csv"
CUTOFFS_PATH = DATA_DIR / "cutoffs.csv"
COLLEGE_CODES_PATH = DATA_DIR / "college_codes.csv"

SEAT_DATA_SOURCE = "2026 Official Seat Matrix"

HIST_YEARS = [2022, 2023, 2024, 2025]
FACTOR_MIN, FACTOR_MAX = 0.5, 2.0
MIN_SAMPLE_YEARS = 2  # below this, the ratio is noise -> factor forced to 1.0

# college_type -> tier rank (lower = more prestigious). Single source of
# truth — predict_colleges.py imports this rather than redefining it.
TIER_RANK = {
    "University Departments": 0,
    "Constituent Colleges": 1,
    "Government Colleges": 2,
    "Government Aided Colleges": 3,
    "Cecri And Cipet": 4,
    "Self Financing Engineering Colleges": 5,
}

_CACHE = {}


def _melt_seat_matrix(sm):
    """Wide seat matrix (one row per college+branch, one column per
    community) -> long form (college_code, branch_code, community, seats),
    with BC+BCM merged into a single "BC" figure."""
    sm = sm.copy()
    sm["BC"] = sm["BC"] + sm["BCM"]
    long_cols = ["OC", "BC", "MBC", "SC", "SCA", "ST"]
    long = sm.melt(
        id_vars=["college_code", "branch_code"],
        value_vars=long_cols,
        var_name="community",
        value_name="seats_2026",
    )
    return long


def _load():
    if _CACHE:
        return _CACHE

    sm = pd.read_csv(SEAT_MATRIX_PATH, dtype={"college_code": int, "branch_code": str})
    combos_2026 = set(zip(sm["college_code"], sm["branch_code"]))
    seats_long = _melt_seat_matrix(sm)
    seats_2026 = {
        (r.college_code, r.branch_code, r.community): int(r.seats_2026)
        for r in seats_long.itertuples()
    }

    cutoffs = pd.read_csv(CUTOFFS_PATH, dtype={"branch_code": str})
    cutoffs = cutoffs[cutoffs["year"].isin(HIST_YEARS)].copy()
    cutoffs["community"] = cutoffs["community"].replace("BCM", "BC")
    per_year = (cutoffs.groupby(["college_code", "branch_code", "community", "year"])
                       ["seats_filled"].sum().reset_index())
    hist_avg_df = (per_year.groupby(["college_code", "branch_code", "community"])
                            ["seats_filled"].mean().reset_index())
    historical_avg_seats = {
        (r.college_code, r.branch_code, r.community): float(r.seats_filled)
        for r in hist_avg_df.itertuples()
    }
    sample_years_df = (per_year.groupby(["college_code", "branch_code", "community"])
                               ["year"].nunique().reset_index())
    sample_years_count = {
        (r.college_code, r.branch_code, r.community): int(r.year)
        for r in sample_years_df.itertuples()
    }

    colleges = pd.read_csv(COLLEGE_CODES_PATH)
    tier_of_college = {
        int(r.college_code): TIER_RANK.get(r.college_type, 9)
        for r in colleges.itertuples()
    }

    def tier_of(college_code):
        return tier_of_college.get(college_code, 9)

    # branch+tier average seats (fallback when a combo has no direct history)
    hist_avg_df["tier"] = hist_avg_df["college_code"].map(tier_of)
    branch_tier_avg = (hist_avg_df.groupby(["branch_code", "tier", "community"])
                                  ["seats_filled"].mean().to_dict())
    branch_only_avg = (hist_avg_df.groupby(["branch_code", "community"])
                                  ["seats_filled"].mean().to_dict())

    _CACHE.update({
        "combos_2026": combos_2026,
        "seats_2026": seats_2026,
        "historical_avg_seats": historical_avg_seats,
        "sample_years_count": sample_years_count,
        "tier_of": tier_of,
        "branch_tier_avg": branch_tier_avg,
        "branch_only_avg": branch_only_avg,
    })
    return _CACHE


def in_2026_matrix(college_code, branch_code):
    c = _load()
    return (int(college_code), str(branch_code)) in c["combos_2026"]


def get_seat_adjustment(college_code, branch_code, community):
    """Returns None if the combo is not in the 2026 seat matrix at all
    (caller should exclude it). Otherwise a dict with:
      seat_adjustment_factor, seats_2026, historical_avg_seats,
      sample_years_count, limited_data
    """
    c = _load()
    college_code = int(college_code)
    branch_code = str(branch_code)
    community = "BC" if community == "BCM" else community

    if (college_code, branch_code) not in c["combos_2026"]:
        return None

    key = (college_code, branch_code, community)
    seats = c["seats_2026"].get(key)
    if seats is None:
        seats = 0

    sample_years = c["sample_years_count"].get(key, 0)
    thin_sample = sample_years < MIN_SAMPLE_YEARS

    limited_data = thin_sample
    hist = c["historical_avg_seats"].get(key)
    if hist is None or hist <= 0:
        tier = c["tier_of"](college_code)
        hist = c["branch_tier_avg"].get((branch_code, tier, community))
        limited_data = True
    if hist is None or hist <= 0:
        hist = c["branch_only_avg"].get((branch_code, community))
        limited_data = True
    hist = float(hist) if hist is not None else None

    if hist is None or hist <= 0 or seats <= 0 or thin_sample:
        factor = 1.0
        limited_data = True
    else:
        factor = seats / hist
        factor = max(FACTOR_MIN, min(FACTOR_MAX, factor))

    return {
        "seat_adjustment_factor": round(float(factor), 4),
        "seats_2026": int(seats),
        "historical_avg_seats": round(hist, 2) if hist else None,
        "sample_years_count": int(sample_years),
        "limited_data": bool(limited_data),
    }


def fallback_closing_rank(branch_code, community, tier, lookup_df):
    """Mean predicted_closing_rank_2026 for branch_code+community among
    colleges of the same tier that DO have a model prediction. Falls back
    to all tiers if the same-tier slice is empty. Returns None if no data
    at all exists for that branch+community."""
    c = _load()
    branch_code = str(branch_code)
    community = "BC" if community == "BCM" else community

    sub = lookup_df[(lookup_df["branch_code"] == branch_code)
                    & (lookup_df["community"] == community)]
    if sub.empty:
        return None

    sub = sub.copy()
    sub["tier"] = sub["college_code"].map(c["tier_of"])
    same_tier = sub[sub["tier"] == tier]
    pool = same_tier if not same_tier.empty else sub
    return float(pool["predicted_closing_rank_2026"].mean())
