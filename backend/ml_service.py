import sys
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).resolve().parent / "utils"))

import math

from predict_colleges import predict_colleges
from ml_utils import predict_rank
from seat_adjustment import SEAT_DATA_SOURCE


def _json_safe(obj):
    """Recursively replace NaN/inf floats with None so the response is JSON
    compliant. Source: blank cells in college_codes.csv (e.g. district) load
    as float NaN and land raw in the response, crashing FastAPI's encoder."""
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def get_rank_prediction(marks: float, community: str):
    result = predict_rank(marks, community)
    if "error" in result:
        raise ValueError(result["error"])
    return result


# Lazy caches built from cutoff_lookup_2026.csv (the per-combo model output,
# post-hoc adjusted by seat_adjustment.py against the 2026 seat matrix;
# cutoff_model_meta.pkl holds only training metadata, not combos).
_OFFERED_COMBOS = None   # set of (college_code, branch_code) offered at all
_COMBO_CLOSING  = None   # dict (college_code, branch_code) -> {community: adjusted closing rank}
_COMBO_META     = None   # dict (college_code, branch_code) -> {community: seat-adjustment meta}


def _load_combo_caches():
    global _OFFERED_COMBOS, _COMBO_CLOSING, _COMBO_META
    if _OFFERED_COMBOS is None:
        import math
        try:
            from predict_colleges import _load
            lookup, _, _ = _load()
            _OFFERED_COMBOS = set(zip(
                lookup["college_code"].astype(int),
                lookup["branch_code"].astype(str)))
            _COMBO_CLOSING = {}
            _COMBO_META = {}
            for r in lookup.itertuples():
                try:
                    closing = r.predicted_closing_rank_2026
                    if closing is None or (isinstance(closing, float)
                       and math.isnan(closing)):
                        continue
                    key = (int(r.college_code), str(r.branch_code))
                    comm = str(r.community)
                    _COMBO_CLOSING.setdefault(key, {})[comm] = int(closing)
                    _COMBO_META.setdefault(key, {})[comm] = {
                        "closing_rank_unadjusted": int(r.closing_rank_unadjusted),
                        "seat_adjustment_factor":  float(r.seat_adjustment_factor),
                        "seats_2026":              r.seats_2026,
                        "historical_avg_seats":    r.historical_avg_seats,
                        "sample_years_count":      int(r.sample_years_count),
                        "limited_data":            bool(r.limited_data),
                    }
                except (ValueError, TypeError):
                    continue
        except Exception as e:
            print(f"_load_combo_caches error: {e}")
            _OFFERED_COMBOS = set()
            _COMBO_CLOSING = {}
            _COMBO_META = {}
    return _OFFERED_COMBOS, _COMBO_CLOSING, _COMBO_META


def get_college_predictions_filtered(
    marks: float,
    community: str,
    top_n: int = 5,
    preferred_colleges: Optional[List[int]] = None,
    preferred_branches: Optional[List[str]] = None,
    forced_rank: Optional[int] = None,
):
    # ------------------------------------------------------------------ #
    # PATH 1 — Both preferred_colleges AND preferred_branches given        #
    # Direct per-combo lookup: every requested pair gets an answer,        #
    # no top-N or attainability filter that can silently drop combos.      #
    # ------------------------------------------------------------------ #
    if preferred_colleges and preferred_branches:
        from predict_colleges import _load, _match_confidence, _status

        if community == "BCM":
            community = "BC"

        if forced_rank is not None:
            pred_rank = forced_rank
            rank_conf = 100
            rmin = rmax = forced_rank
        else:
            rk = predict_rank(marks, community)
            if "error" in rk:
                raise ValueError(rk["error"])
            pred_rank = int(rk["predicted_rank"])
            rank_conf = int(rk["confidence"])
            rmin, rmax = int(rk["range_min"]), int(rk["range_max"])

        _, colleges, branches = _load()
        offered, combo_closing, combo_meta = _load_combo_caches()

        recs = []
        for ccode in preferred_colleges:
            ccode = int(ccode)
            info  = colleges.get(ccode)
            for bcode in preferred_branches:
                bcode = str(bcode)
                rec = {
                    "rank":             len(recs) + 1,
                    "college_code":     ccode,
                    "college_name":     info["college_name_full"] if info else f"College {ccode}",
                    "college_type":     info["college_type"]      if info else "Unknown",
                    "college_district": info["district"]          if info else "Unknown",
                    "branch_code":      bcode,
                    "branch_name":      branches.get(bcode, f"Branch {bcode}"),
                    "rank_band_low":    rmin,
                    "rank_band_high":   rmax,
                }

                # Not offered at all, OR historically offered but absent from
                # the 2026 seat matrix (seat matrix is authoritative for 2026)
                if (ccode, bcode) not in offered:
                    rec.update({
                        "not_offered":      True,
                        "closing_rank":     None,
                        "safety_margin":    None,
                        "status":           "NOT_OFFERED",
                        "match_confidence": None,
                    })
                    recs.append(rec)
                    continue

                per_comm = combo_closing.get((ccode, bcode), {})
                meta_comm = combo_meta.get((ccode, bcode), {})
                closing  = per_comm.get(community)
                meta     = meta_comm.get(community)

                # No cutoff for this specific community — use best available
                if closing is None:
                    fallback_comm = "OC" if per_comm.get("OC") is not None else (
                        min(per_comm, key=per_comm.get) if per_comm else None)
                    if fallback_comm is None:
                        # No data at all for this combo
                        rec.update({
                            "no_community_data": True,
                            "closing_rank":      None,
                            "safety_margin":     None,
                            "status":            "NO_DATA",
                            "match_confidence":  None,
                        })
                        recs.append(rec)
                        continue
                    closing = per_comm[fallback_comm]
                    meta = meta_comm.get(fallback_comm)
                    rec["no_community_data"] = True

                margin = closing - pred_rank
                status = _status(margin)
                rec.update({
                    "closing_rank":     closing,
                    "safety_margin":    margin,
                    "status":           status,
                    "match_confidence": int(_match_confidence(rank_conf, status, margin, closing,
                                                              student_mark=marks, community=community)),
                    "community_closing_ranks": dict(per_comm),
                    "closing_rank_unadjusted": meta["closing_rank_unadjusted"] if meta else None,
                    "seat_adjustment_factor":  meta["seat_adjustment_factor"]  if meta else None,
                    "seats_2026":              meta["seats_2026"]             if meta else None,
                    "historical_avg_seats":    meta["historical_avg_seats"]   if meta else None,
                    "sample_years_count":      meta["sample_years_count"]     if meta else None,
                    "limited_data":            meta["limited_data"]           if meta else True,
                })
                recs.append(rec)

        # Confident combos first; not_offered / no-data sink to the bottom
        recs.sort(key=lambda r: (r["match_confidence"] is None,
                                 -(r["match_confidence"] or 0)))
        for i, r in enumerate(recs, 1):
            r["rank"] = i

        return _json_safe({
            "student_rank":       pred_rank,
            "student_rank_range": [rmin, rmax],
            "rank_confidence":    rank_conf,
            "community":          community,
            "recommendations":    recs,
            "message":            None,
            "verified_rank":      forced_rank is not None,
            "seat_data_source":   SEAT_DATA_SOURCE,
        })

    # ------------------------------------------------------------------ #
    # PATH 2 — Only one of preferred_colleges or preferred_branches given  #
    # Filter path — no attainability filter so results are not silently    #
    # dropped for WONT_GET combos.                                         #
    # ------------------------------------------------------------------ #
    if preferred_colleges or preferred_branches:
        from predict_colleges import _load, _match_confidence, _status

        if community == "BCM":
            community = "BC"

        if forced_rank is not None:
            pred_rank = forced_rank
            rank_conf = 100
            rmin2, rmax2 = forced_rank, forced_rank
        else:
            rk = predict_rank(marks, community)
            if "error" in rk:
                raise ValueError(rk["error"])
            pred_rank = int(rk["predicted_rank"])
            rank_conf = int(rk["confidence"])
            rmin2, rmax2 = int(rk["range_min"]), int(rk["range_max"])

        lookup, colleges, branches = _load()

        df = lookup[lookup["community"] == community].copy()
        # NOTE: attainability filter intentionally removed — show all combos
        # including WONT_GET so the student sees real data for their choices.

        if preferred_colleges:
            df = df[df["college_code"].isin(preferred_colleges)]
        if preferred_branches:
            df = df[df["branch_code"].isin(preferred_branches)]

        df = df.copy()
        df["safety_margin"] = df["predicted_closing_rank_2026"] - pred_rank
        df["status"]        = df["safety_margin"].apply(_status)
        _, combo_closing, combo_meta = _load_combo_caches()

        recs = []
        for _, row in df.iterrows():
            code    = int(row["college_code"])
            info    = colleges.get(code)
            bcode   = str(row["branch_code"])
            margin  = int(row["safety_margin"])
            status  = row["status"]
            closing = int(row["predicted_closing_rank_2026"])
            meta    = combo_meta.get((code, bcode), {}).get(community)
            recs.append({
                "rank":             len(recs) + 1,
                "college_code":     code,
                "college_name":     info["college_name_full"] if info else f"College {code}",
                "college_type":     info["college_type"]      if info else "Unknown",
                "college_district": info["district"]          if info else "Unknown",
                "branch_code":      bcode,
                "branch_name":      branches.get(bcode, f"Branch {bcode}"),
                "closing_rank":     closing,
                "safety_margin":    margin,
                "status":           status,
                "match_confidence": int(_match_confidence(rank_conf, status, margin, closing,
                                                          student_mark=marks, community=community)),
                "community_closing_ranks": combo_closing.get((code, bcode), {}),
                "closing_rank_unadjusted": meta["closing_rank_unadjusted"] if meta else None,
                "seat_adjustment_factor":  meta["seat_adjustment_factor"]  if meta else None,
                "seats_2026":              meta["seats_2026"]             if meta else None,
                "historical_avg_seats":    meta["historical_avg_seats"]   if meta else None,
                "sample_years_count":      meta["sample_years_count"]     if meta else None,
                "limited_data":            meta["limited_data"]           if meta else True,
            })

        recs.sort(key=lambda x: x["match_confidence"], reverse=True)
        recs = recs[:top_n]
        for i, r in enumerate(recs, 1):
            r["rank"] = i

        return _json_safe({
            "student_rank":       pred_rank,
            "student_rank_range": [rmin2, rmax2],
            "rank_confidence":    rank_conf,
            "community":          community,
            "recommendations":    recs,
            "message":            "No matches found. Try broadening your filters." if not recs else None,
            "verified_rank":      forced_rank is not None,
            "seat_data_source":   SEAT_DATA_SOURCE,
        })

    # ------------------------------------------------------------------ #
    # PATH 3 — No preferences — Grade 3 free predict                      #
    # ------------------------------------------------------------------ #
    result = predict_colleges(marks, community, top_n=top_n, forced_rank=forced_rank)
    if "error" in result:
        raise ValueError(result["error"])
    return _json_safe(result)