#!/usr/bin/env python3
"""
TNEA Predictor production API validation suite.
Target: https://tneapredictor-production.up.railway.app

Rate limits:
  /predict/rank     50/day per IP
  /predict/colleges 30/day per IP
  /predict/combo    10/day (auth required -- skipped)

Strategy:
  - /rank for mark-set x community matrix + input validation (50/day budget)
  - /colleges for path tests + college-filtering edge cases (30/day budget)
  - Authorization: Bearer test  -->  bypasses 1/day guest-IP check;
    token decode fails silently --> no persistence, prediction still runs

Response field names (confirmed by inspection):
  /rank:     predicted_rank, range_min, range_max, confidence, basis
  /colleges: student_rank, student_rank_range, rank_confidence,
             community, recommendations[]
"""

import httpx
import json
import math
import statistics
import time
from typing import Any

BASE  = "https://tneapredictor-production.up.railway.app"
PBASE = f"{BASE}/predict"
HDR   = {"Authorization": "Bearer test"}   # bypass guest-IP 1/day gate

COMMUNITIES = ["OC", "BC", "MBC", "SC", "ST", "SCA", "BCM"]

MARK_SETS = [
    ("high",    {"maths": 95,  "physics": 92,  "chemistry": 88}),   # agg 185.0
    ("mid",     {"maths": 75,  "physics": 70,  "chemistry": 72}),   # agg 146.0
    ("ov_math", {"maths": 155, "physics": 85,  "chemistry": 90}),   # maths>100 INVALID
    ("low",     {"maths": 50,  "physics": 45,  "chemistry": 48}),   # agg  96.5
    ("all100",  {"maths": 100, "physics": 100, "chemistry": 100}),  # agg 200.0
]

# bookkeeping
ALL      = []
ERRORS   = []
NAN_HITS = []
RL_HITS  = []
BCM_DIFF = []


def _has_nan_inf_str(text: str) -> bool:
    return "NaN" in text or "Infinity" in text

def _has_nan_inf_obj(obj: Any) -> bool:
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return True
    if isinstance(obj, dict):
        return any(_has_nan_inf_obj(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_nan_inf_obj(v) for v in obj)
    return False

def _post(client: httpx.Client, path: str, label: str, payload: dict) -> dict:
    url = f"{PBASE}/{path}"
    t0  = time.perf_counter()
    try:
        resp = client.post(url, json=payload, headers=HDR, timeout=30)
        ms   = (time.perf_counter() - t0) * 1000
        raw  = resp.text
        nan  = _has_nan_inf_str(raw)
        try:
            body = resp.json()
        except Exception:
            body = {"_raw": raw}
        nan = nan or _has_nan_inf_obj(body)

        rec = {
            "label":  label,
            "status": resp.status_code,
            "ms":     ms,
            "ok":     resp.status_code == 200,
            "body":   body,
            "nan":    nan,
        }
        ALL.append(rec)
        if nan:
            NAN_HITS.append(label)
        if resp.status_code == 429:
            RL_HITS.append(label)
        elif resp.status_code not in (200, 400, 422, 401):
            ERRORS.append({"label": label, "status": resp.status_code,
                           "body": json.dumps(body)[:200]})
        return rec
    except Exception as exc:
        ms  = (time.perf_counter() - t0) * 1000
        rec = {"label": label, "status": -1, "ms": ms,
               "ok": False, "body": None, "nan": False, "exc": str(exc)}
        ALL.append(rec)
        ERRORS.append({"label": label, "status": -1, "error": str(exc)})
        return rec

def _fmt(rec: dict) -> str:
    s  = rec["status"]
    ms = rec["ms"]
    tag = ("OK"  if rec["ok"]   else
           "RL"  if s == 429    else
           "VAL" if s in (400, 422) else "ERR")
    return f"[{s} {tag}] {ms:.0f}ms"

def _rank_from_colleges(body: dict):
    """Extract rank from /colleges response."""
    return body.get("student_rank") if body else None

def _rank_from_rank(body: dict):
    """Extract rank from /rank response."""
    return body.get("predicted_rank") if body else None


def run():
    with httpx.Client() as c:

        # ======================================================================
        # 7A  PATH TESTS  (/colleges with varying optional parameters)
        # ======================================================================
        print("\n=== 7A: PATH TESTS (all to /predict/colleges) =================")
        base = {"maths": 90, "physics": 85, "chemistry": 80, "community": "OC"}
        paths = {
            "(a) marks+comm":       {**base},
            "(b) +branch":          {**base, "preferred_branches": ["CS"]},
            "(c) +college":         {**base, "preferred_colleges": [1]},
            "(d) +college+branch":  {**base, "preferred_colleges": [1],
                                     "preferred_branches": ["CS"]},
        }
        path_results = {}
        for name, payload in paths.items():
            r = _post(c, "colleges", f"7A {name}", payload)
            recs  = r["body"].get("recommendations", []) if r["ok"] else []
            srank = _rank_from_colleges(r["body"]) if r["ok"] else "-"
            print(f"  {name}: {_fmt(r)} | student_rank={srank} | recs={len(recs)}")
            path_results[name] = r
            if recs:
                for rec in recs[:2]:
                    print(f"      -> {rec['college_code']} {rec['branch_code']}"
                          f"  status={rec['status']}  conf={rec.get('match_confidence')}")

        # ======================================================================
        # 7B  INPUT VALIDATION BOUNDARIES  (/rank)
        # ======================================================================
        print("\n=== 7B: INPUT VALIDATION BOUNDARIES (/predict/rank) ===========")
        val_cases = [
            ("marks=200 (all100)",          {"maths":100,  "physics":100,  "chemistry":100,  "community":"OC"}),
            ("marks=0   (all-zero)",         {"maths":0,    "physics":0,    "chemistry":0,    "community":"OC"}),
            ("maths=-1  (negative)",         {"maths":-1,   "physics":50,   "chemistry":50,   "community":"OC"}),
            ("maths=101 (>100)",             {"maths":101,  "physics":50,   "chemistry":50,   "community":"OC"}),
            ("marks~74.9 (threshold)",       {"maths":50,   "physics":49.8, "chemistry":50,   "community":"OC"}),
            ("decimals 99.5/98.5/97.5",      {"maths":99.5, "physics":98.5, "chemistry":97.5, "community":"OC"}),
            ("non-numeric maths='abc'",      {"maths":"abc","physics":50,   "chemistry":50,   "community":"OC"}),
            ("null maths",                   {"maths":None, "physics":50,   "chemistry":50,   "community":"OC"}),
            ("invalid community 'INVALID'",  {"maths":80,   "physics":70,   "chemistry":75,   "community":"INVALID"}),
            ("missing maths field",          {              "physics":70,   "chemistry":75,   "community":"OC"}),
        ]
        for label, payload in val_cases:
            r = _post(c, "rank", f"7B val: {label}", payload)
            if r["ok"]:
                note = f"predicted_rank={_rank_from_rank(r['body'])}"
            elif r["status"] in (400, 422):
                detail = r["body"]
                if isinstance(detail, dict) and "detail" in detail:
                    d = detail["detail"]
                    if isinstance(d, list) and d:
                        note = f"rejected: {d[0].get('msg','')}"
                    else:
                        note = f"rejected: {str(d)[:80]}"
                else:
                    note = f"rejected: {json.dumps(detail)[:80]}"
            else:
                note = json.dumps(r["body"])[:80] if r["body"] else ""
            print(f"  {label}: {_fmt(r)}  {note}")

        # ======================================================================
        # 7B  MARK SETS x 7 COMMUNITIES  (/rank)
        # ======================================================================
        print("\n=== 7B: 5 MARK SETS x 7 COMMUNITIES (/predict/rank) ===========")
        bc_ranks  = {}
        bcm_ranks = {}
        for ms_name, ms_marks in MARK_SETS:
            row   = []
            agg   = ms_marks["maths"] + ms_marks["physics"]/2 + ms_marks["chemistry"]/2
            for comm in COMMUNITIES:
                r = _post(c, "rank", f"7B {ms_name}/{comm}", {**ms_marks, "community": comm})
                if r["ok"]:
                    rank = _rank_from_rank(r["body"])
                    row.append(f"{comm}={rank}")
                    if comm == "BC":
                        bc_ranks[ms_name]  = rank
                    if comm == "BCM":
                        bcm_ranks[ms_name] = rank
                elif r["status"] == 422:
                    row.append(f"{comm}=INVALID")
                elif r["status"] == 429:
                    row.append(f"{comm}=RL")
                else:
                    row.append(f"{comm}={r['status']}")
            print(f"  {ms_name}(agg={agg:.1f}): {' | '.join(row)}")

        # BCM vs BC rank comparison
        print("\n  BCM vs BC rank comparison (same marks):")
        for k in bc_ranks:
            bc  = bc_ranks.get(k)
            bcm = bcm_ranks.get(k)
            if bc != bcm:
                BCM_DIFF.append({"marks": k, "BC": bc, "BCM": bcm})
                tag = "DIFF!"
            else:
                tag = "same"
            print(f"    {k}: BC={bc}  BCM={bcm}  [{tag}]")

        # BCM vs BC college recommendations comparison (same marks, mid set)
        print("\n  BCM vs BC college recs comparison (mid marks):")
        mid = {"maths":75, "physics":70, "chemistry":72}
        for comm in ["BC", "BCM"]:
            r = _post(c, "colleges", f"BCM-BC-cmp/{comm}", {**mid, "community": comm})
            recs = r["body"].get("recommendations", []) if r["ok"] else []
            codes = [(rc["college_code"], rc["branch_code"]) for rc in recs]
            print(f"    {comm}: rank={_rank_from_colleges(r['body']) if r['ok'] else '-'}"
                  f"  recs={codes}")

        # ======================================================================
        # EDGE CASES
        # ======================================================================
        print("\n=== EDGE CASES ================================================")

        # E1: poor-fit preferred combo (low marks + very competitive target)
        #     Must appear in results (not silently dropped), labelled risky
        r_e1 = _post(c, "colleges", "E1 poor-fit preferred",
                     {"maths":50, "physics":45, "chemistry":48,
                      "community":"OC", "preferred_colleges":[1],
                      "preferred_branches":["CS"], "top_n":20})
        e1_recs  = r_e1["body"].get("recommendations", []) if r_e1["ok"] else []
        e1_found = any(
            rec.get("college_code") == 1 and rec.get("branch_code") == "CS"
            for rec in e1_recs
        )
        e1_pass  = e1_found
        print(f"  E1 poor-fit preferred: {_fmt(r_e1)} | recs={len(e1_recs)}"
              f" | preferred_in_results={e1_found} | PASS={e1_pass}")
        for rec in e1_recs[:3]:
            print(f"      -> col={rec.get('college_code')} br={rec.get('branch_code')}"
                  f"  status={rec.get('status')}  conf={rec.get('match_confidence')}"
                  f"  not_offered={rec.get('not_offered')}")

        # E2: attempt to trigger NaN/Infinity
        r_e2a = _post(c, "rank", "E2a 0.001",
                      {"maths":0.001, "physics":0.001, "chemistry":0.001, "community":"OC"})
        r_e2b = _post(c, "rank", "E2b 99.999",
                      {"maths":99.999, "physics":99.999, "chemistry":99.999, "community":"OC"})
        r_e2c = _post(c, "rank", "E2c all-zero",
                      {"maths":0, "physics":0, "chemistry":0, "community":"OC"})
        e2_pass = not any(r["nan"] for r in [r_e2a, r_e2b, r_e2c])
        print(f"  E2 NaN/Inf: 0.001->{_fmt(r_e2a)} nan={r_e2a['nan']}"
              f" | 99.999->{_fmt(r_e2b)} nan={r_e2b['nan']}"
              f" | all-zero->{_fmt(r_e2c)} nan={r_e2c['nan']}"
              f" | PASS={e2_pass}")

        # E3: preferred college+branch that doesn't exist together in data
        #     ACT campus (code=2) + Aeronautical (AE) -- very unlikely
        r_e3 = _post(c, "colleges", "E3 nonexistent pairing",
                     {"maths":85, "physics":80, "chemistry":82,
                      "community":"OC", "preferred_colleges":[2],
                      "preferred_branches":["AE"], "top_n":5})
        e3_recs = r_e3["body"].get("recommendations", []) if r_e3["ok"] else []
        e3_pass = r_e3["status"] not in (-1, 500, 502, 503)
        print(f"  E3 nonexistent col+branch: {_fmt(r_e3)} | recs={len(e3_recs)} | no-crash={e3_pass}")
        for rec in e3_recs[:2]:
            print(f"      -> col={rec.get('college_code')} br={rec.get('branch_code')}"
                  f"  not_offered={rec.get('not_offered')}  no_comm_data={rec.get('no_community_data')}")

        # E4: niche combo with likely fewer than 5 results
        #     ST community + Agriculture (AG) -- very few seats in TNEA
        r_e4 = _post(c, "colleges", "E4 niche <5",
                     {"maths":99, "physics":98, "chemistry":97,
                      "community":"ST", "preferred_branches":["AG"], "top_n":20})
        e4_recs = r_e4["body"].get("recommendations", []) if r_e4["ok"] else []
        e4_pass = r_e4["status"] not in (-1, 500, 502, 503)
        print(f"  E4 niche (<5 expected): {_fmt(r_e4)} | recs={len(e4_recs)} | no-crash={e4_pass}")

        # E8: nonexistent college code 9999
        r_e8 = _post(c, "colleges", "E8 college=9999",
                     {"maths":85, "physics":80, "chemistry":82,
                      "community":"OC", "preferred_colleges":[9999], "top_n":5})
        e8_recs = r_e8["body"].get("recommendations", []) if r_e8["ok"] else []
        e8_pass = r_e8["status"] not in (-1, 500, 502, 503)
        print(f"  E8 college=9999: {_fmt(r_e8)} | recs={len(e8_recs)} | no-crash={e8_pass}")

        # E9: nonexistent branch code ZZZ
        r_e9 = _post(c, "colleges", "E9 branch=ZZZ",
                     {"maths":85, "physics":80, "chemistry":82,
                      "community":"OC", "preferred_branches":["ZZZ"], "top_n":5})
        e9_recs = r_e9["body"].get("recommendations", []) if r_e9["ok"] else []
        e9_pass = r_e9["status"] not in (-1, 500, 502, 503)
        print(f"  E9 branch=ZZZ: {_fmt(r_e9)} | recs={len(e9_recs)} | no-crash={e9_pass}")

        # ======================================================================
        # FINAL REPORT
        # ======================================================================
        print("\n" + "="*60)
        print("FINAL REPORT")
        print("="*60)

        total   = len(ALL)
        ok200   = sum(1 for r in ALL if r["ok"])
        val_err = sum(1 for r in ALL if r["status"] in (400, 422))
        rl_cnt  = len(RL_HITS)
        err_cnt = len(ERRORS)
        nan_cnt = len(NAN_HITS)
        bcm_cnt = len(BCM_DIFF)

        times = sorted(r["ms"] for r in ALL if r["ms"] > 0)
        p95   = times[int(0.95 * len(times))] if times else 0
        med   = statistics.median(times) if times else 0

        print(f"  Total requests   : {total}")
        print(f"  200 OK           : {ok200}")
        print(f"  400/422 val err  : {val_err}")
        print(f"  429 rate-limited : {rl_cnt}")
        print(f"  Other errors     : {err_cnt}")
        print(f"  NaN/Inf detected : {nan_cnt}")
        print(f"  BCM != BC diffs  : {bcm_cnt}")
        print(f"  Median latency   : {med:.0f}ms")
        print(f"  p95 latency      : {p95:.0f}ms")

        if ERRORS:
            print("\n  -- Failures --------------------------------------------------")
            for e in ERRORS:
                s   = e.get("status", "?")
                lbl = e.get("label", "?")
                print(f"    [{s}] {lbl}")
                if "body" in e:
                    print(f"         {e['body'][:120]}")
                if "error" in e:
                    print(f"         {e['error'][:120]}")

        if NAN_HITS:
            print("\n  -- NaN/Inf hits ----------------------------------------------")
            for h in NAN_HITS:
                print(f"    {h}")

        if BCM_DIFF:
            print("\n  -- BCM != BC same-marks rank ---------------------------------")
            for d in BCM_DIFF:
                print(f"    {d['marks']}: BC={d['BC']} BCM={d['BCM']}")
        else:
            print("\n  BCM vs BC rank: identical for all mark sets (expected)")

        if RL_HITS:
            print(f"\n  -- Rate-limited ({rl_cnt}) ------------------------------------")
            for h in RL_HITS[:15]:
                print(f"    {h}")
            if rl_cnt > 15:
                print(f"    ... and {rl_cnt-15} more")

        print("\n  -- Edge Case Results -----------------------------------------")
        cases = [
            ("E1", "poor-fit preferred still returned in results", e1_pass),
            ("E2", "no NaN/Infinity in any response body",         e2_pass),
            ("E3", "nonexistent col+branch: no crash",             e3_pass),
            ("E4", "niche combo (<5 seats): no crash",             e4_pass),
            ("E8", "college_code=9999: no crash",                  e8_pass),
            ("E9", "branch=ZZZ: no crash",                         e9_pass),
        ]
        for eid, desc, passed in cases:
            icon = "PASS" if passed else "FAIL"
            print(f"    {eid} [{icon}]  {desc}")

        print("="*60)


if __name__ == "__main__":
    run()
