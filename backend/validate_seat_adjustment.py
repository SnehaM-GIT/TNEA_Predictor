"""
validate_seat_adjustment.py — spot-check the seat-matrix post-hoc adjustment.

Picks 10 known (college_code, branch_code, community) combos spanning the
range of seat_adjustment_factor (big increase, big decrease, ~unchanged,
and a couple of limited_data/new-offering cases), and prints OLD (base
cutoff_predictor.pkl output, i.e. closing_rank_unadjusted) vs NEW (seat-
matrix adjusted) predicted probability for a fixed test student, side by
side. Does not touch or reload the model — reads straight from the same
enriched lookup ml_service.py uses.

Run: python backend/validate_seat_adjustment.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "utils"))

from predict_colleges import _load, _match_confidence, _status  # noqa: E402

# Fixed test student — isolates the adjustment's effect from mark-based
# nudging by omitting student_mark (falls back to the pure rank-ratio curve).
TEST_RANK = 20000
TEST_RANK_CONF = 70

# (college_code, branch_code, community) — chosen to cover: large factor-up,
# large factor-down, ~unchanged, and limited_data/imputed (new 2026 offering).
SPOT_CHECK_COMBOS = [
    (2646, "CS", "OC"),   # seats up a lot vs history
    (2639, "AD", "OC"),
    (2639, "CS", "OC"),
    (2638, "EC", "OC"),   # seats down a lot vs history
    (4933, "CS", "OC"),
    (4917, "AG", "OC"),
    (1013, "CS", "OC"),   # ~unchanged (factor ~1.0)
    (1026, "CS", "OC"),
    (1128, "CA", "OC"),   # imputed_base: brand-new 2026 offering, no model row
    (4957, "BM", "OC"),   # imputed_base: brand-new 2026 offering, no model row
]


def probability_for(closing_rank):
    margin = closing_rank - TEST_RANK
    status = _status(margin)
    return _match_confidence(TEST_RANK_CONF, status, margin, closing_rank)


def main():
    lookup, colleges, branches = _load()

    print(f"{'college':>8} {'branch':>7} {'comm':>5} {'old_rank':>9} {'new_rank':>9} "
          f"{'factor':>7} {'old_prob%':>10} {'new_prob%':>10} {'delta':>7} {'flags':>20}")
    print("-" * 100)

    for ccode, bcode, comm in SPOT_CHECK_COMBOS:
        row = lookup[(lookup["college_code"] == ccode)
                     & (lookup["branch_code"] == bcode)
                     & (lookup["community"] == comm)]
        if row.empty:
            print(f"{ccode:>8} {bcode:>7} {comm:>5}  -- combo not in 2026 seat matrix / no data --")
            continue
        row = row.iloc[0]

        old_rank = int(row["closing_rank_unadjusted"])
        new_rank = int(row["predicted_closing_rank_2026"])
        factor = float(row["seat_adjustment_factor"])

        old_prob = probability_for(old_rank)
        new_prob = probability_for(new_rank)

        flags = []
        if row["imputed_base"]:
            flags.append("NEW_OFFERING(no baseline)")
        elif row["limited_data"]:
            flags.append("limited_data")
        flags = ",".join(flags) or "-"

        print(f"{ccode:>8} {bcode:>7} {comm:>5} {old_rank:>9} {new_rank:>9} "
              f"{factor:>7.3f} {old_prob:>10} {new_prob:>10} {new_prob - old_prob:>+7} {flags:>20}")

    print("-" * 100)
    print(f"Test student: fixed rank={TEST_RANK}, rank_confidence={TEST_RANK_CONF}% "
          f"(no marks - isolates the seat-adjustment effect from mark-based nudging)")
    print("old_rank  = closing_rank_unadjusted (cutoff_predictor.pkl output, untouched)")
    print("new_rank  = predicted_closing_rank_2026 (post-hoc adjusted by 2026 seat matrix)")
    print("NEW_OFFERING rows have no old_rank baseline - old_rank/old_prob shown are the")
    print("same-tier branch-average fallback used to impute a base prediction, not a real")
    print("pre-adjustment model output.")


if __name__ == "__main__":
    main()
