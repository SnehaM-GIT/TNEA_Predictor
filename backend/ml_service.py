import sys
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).resolve().parent / "utils"))

import math

from predict_colleges import predict_colleges
from ml_utils import predict_rank


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


# Lazy caches built from cutoff_lookup_2026.csv (the per-combo model output;
# cutoff_model_meta.pkl holds only training metadata, not combos).
_OFFERED_COMBOS = None   # set of (college_code, branch_code) offered at all
_COMBO_CLOSING  = None   # dict (college_code, branch_code) -> {community: closing rank}


def _load_combo_caches():
    global _OFFERED_COMBOS, _COMBO_CLOSING
    if _OFFERED_COMBOS is None:
        import math
        try:
            from predict_colleges import _load
            lookup, _, _ = _load()
            _OFFERED_COMBOS = set(zip(
                lookup["college_code"].astype(int),
                lookup["branch_code"].astype(str)))
            _COMBO_CLOSING = {}
            for r in lookup.itertuples():
                try:
                    closing = r.predicted_closing_rank_2026
                    if closing is None or (isinstance(closing, float)
                       and math.isnan(closing)):
                        continue
                    _COMBO_CLOSING.setdefault(
                        (int(r.college_code), str(r.branch_code)), {}
                    )[str(r.community)] = int(closing)
                except (ValueError, TypeError):
                    continue
        except Exception as e:
            print(f"_load_combo_caches error: {e}")
            _OFFERED_COMBOS = set()
            _COMBO_CLOSING = {}
    return _OFFERED_COMBOS, _COMBO_CLOSING


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
        offered, combo_closing = _load_combo_caches()

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

                # College does not offer this branch at all
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
                closing  = per_comm.get(community)

                # No cutoff for this specific community — use best available
                if closing is None:
                    fallback = per_comm.get("OC") or (min(per_comm.values()) if per_comm else None)
                    if fallback is None:
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
                    closing = fallback
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

        recs = []
        for _, row in df.iterrows():
            code    = int(row["college_code"])
            info    = colleges.get(code)
            bcode   = str(row["branch_code"])
            margin  = int(row["safety_margin"])
            status  = row["status"]
            closing = int(row["predicted_closing_rank_2026"])
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
                "community_closing_ranks": _load_combo_caches()[1].get((code, bcode), {}),
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
        })

    # ------------------------------------------------------------------ #
    # PATH 3 — No preferences — Grade 3 free predict                      #
    # ------------------------------------------------------------------ #
    result = predict_colleges(marks, community, top_n=top_n, forced_rank=forced_rank)
    if "error" in result:
        raise ValueError(result["error"])
    return _json_safe(result)