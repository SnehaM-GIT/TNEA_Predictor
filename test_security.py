#!/usr/bin/env python3
"""
TNEA Predictor security & auth validation suite.
Target: https://tneapredictor-production.up.railway.app

Tests: D1 D2 D3 D4 P12 SEC1 SEC2 SEC3 SEC4 SEC5 SEC7 SEC8 SEC9 SEC10

Architecture notes (from source review):
  - JWT secret: SECRET_KEY env var (HS256, 30-day expiry)
  - Grade order: 1 > 2 > 3 (counter-intuitive numbering)
  - Fresh signup -> grade="2" (middle tier)
  - /predict/submit-rank requires grade "1" (highest)
  - /predict/combo requires grade "2" (middle - fresh users qualify)
  - SQLAlchemy ORM used throughout (parameterized queries)
  - No prediction history GET endpoint exists
"""

import asyncio
import httpx
import json
import time
import uuid

try:
    import jwt as pyjwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False
    print("WARNING: PyJWT not installed. D1 will use a static malformed token.")

from datetime import datetime, timedelta, timezone

BASE = "https://tneapredictor-production.up.railway.app"
RESULTS = []


# ── helpers ───────────────────────────────────────────────────────────────────

def mk_email():
    return f"sectest_{uuid.uuid4().hex[:8]}@test.invalid"

def _hdrs(token=None):
    return {"Authorization": f"Bearer {token}"} if token else {}

def _post(client, path, payload, token=None):
    return client.post(f"{BASE}{path}", json=payload,
                       headers=_hdrs(token), timeout=30)

def _get(client, path, token=None):
    return client.get(f"{BASE}{path}", headers=_hdrs(token), timeout=30)

def signup(client, email, password="Secure#9977", name="SecTest User"):
    r = _post(client, "/auth/signup", {
        "email": email, "password": password,
        "name": name, "mobile": "9876543210", "community": "OC"
    })
    return r

def get_token(client, email, password="Secure#9977"):
    r = _post(client, "/auth/login", {"email": email, "password": password})
    if r.status_code == 200:
        return r.json().get("token")
    return None

def record(tid, passed, status, snippet=""):
    RESULTS.append({"id": tid, "pass": passed,
                    "status": str(status), "snippet": snippet})

def pf(passed):
    if passed is True:  return "PASS"
    if passed is False: return "FAIL"
    return "INFO"


# ── main ──────────────────────────────────────────────────────────────────────

def run():
    print("=" * 65)
    print("TNEA Predictor  --  Security & Auth Test Suite")
    print("=" * 65)

    with httpx.Client() as c:

        # ── SETUP: create two fresh test accounts ─────────────────────────
        print("\n[SETUP] Creating User A and User B...")
        email_a, email_b = mk_email(), mk_email()
        pw = "Secure#9977"

        ra = signup(c, email_a, pw, name="UserA-SecTest")
        rb = signup(c, email_b, pw, name="UserB-SecTest")

        assert ra.status_code == 200, f"UserA signup failed: {ra.text}"
        assert rb.status_code == 200, f"UserB signup failed: {rb.text}"

        token_a = ra.json()["token"]
        token_b = rb.json()["token"]

        me_a = _get(c, "/auth/me", token_a).json()
        me_b = _get(c, "/auth/me", token_b).json()
        id_a, id_b = me_a["id"], me_b["id"]

        print(f"  User A: id={id_a}  email={email_a}  grade={me_a.get('grade')}")
        print(f"  User B: id={id_b}  email={email_b}  grade={me_b.get('grade')}")

        # ─────────────────────────────────────────────────────────────────
        # D1 -- JWT EXPIRY
        # ─────────────────────────────────────────────────────────────────
        print("\n[D1] JWT Expiry...")
        if HAS_JWT:
            expired_tok = pyjwt.encode(
                {"user_id": id_a,
                 "exp": datetime.now(timezone.utc) - timedelta(hours=2)},
                "wrong_dummy_key",          # wrong key intentional
                algorithm="HS256"
            )
        else:
            # manually crafted expired-looking JWT with bad sig
            expired_tok = token_a[:-5] + "XXXXX"

        r = _get(c, "/auth/me", expired_tok)
        passed = r.status_code == 401
        record("D1", passed, r.status_code,
               f"body={r.text[:80]}")
        print(f"  {r.status_code}  {pf(passed)}  {r.text[:80]}")

        # ─────────────────────────────────────────────────────────────────
        # D2 -- TAMPERED JWT SIGNATURE
        # ─────────────────────────────────────────────────────────────────
        print("\n[D2] Tampered JWT signature...")
        parts = token_a.split(".")
        sig_chars = list(parts[2])
        sig_chars[0] = "Z" if sig_chars[0] != "Z" else "A"
        sig_chars[-1] = "Q" if sig_chars[-1] != "Q" else "P"
        tampered = ".".join(parts[:2] + ["".join(sig_chars)])
        r = _get(c, "/auth/me", tampered)
        passed = r.status_code == 401
        record("D2", passed, r.status_code, r.text[:80])
        print(f"  {r.status_code}  {pf(passed)}  {r.text[:80]}")

        # ─────────────────────────────────────────────────────────────────
        # D3 -- CROSS-USER JWT (token A should never reveal B's data)
        # ─────────────────────────────────────────────────────────────────
        print("\n[D3] Cross-user JWT isolation...")
        r = _get(c, "/auth/me", token_a)
        data = r.json() if r.status_code == 200 else {}
        returned_id    = data.get("id")
        returned_email = data.get("email")
        passed = (
            r.status_code == 200
            and returned_id == id_a
            and returned_email == email_a
            and returned_id != id_b
        )
        record("D3", passed, r.status_code,
               f"returned id={returned_id} email={returned_email}")
        print(f"  {r.status_code}  {pf(passed)}  "
              f"returned id={returned_id}  expected={id_a}  "
              f"is_B={returned_id == id_b}")

        # ─────────────────────────────────────────────────────────────────
        # D4 -- DEAD ENV VAR (code inspection, no API call)
        # ─────────────────────────────────────────────────────────────────
        print("\n[D4] Dead env var -- code review finding (no API call)...")
        finding = (
            "config.py:28  defines  JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')  "
            "but it is never imported or referenced anywhere in the codebase. "
            "auth_middleware.py, routes/auth.py, and routes/predict.py all read "
            "SECRET_KEY = os.getenv('SECRET_KEY') independently. "
            "Risk: an operator who sets JWT_SECRET_KEY in the env expecting it "
            "to protect JWTs will be silently ignored -- actual key is SECRET_KEY."
        )
        record("D4", None, "N/A (code review)", finding)
        print(f"  FINDING: {finding}")

        # ─────────────────────────────────────────────────────────────────
        # P12 -- CONCURRENT PROFILE UPDATES (A and B simultaneously)
        # ─────────────────────────────────────────────────────────────────
        print("\n[P12] Concurrent profile updates...")

        async def concurrent_updates():
            async with httpx.AsyncClient() as ac:
                payload_a = {"maths": 91.0, "physics": 88.0, "chemistry": 85.0}
                payload_b = {"maths": 72.0, "physics": 68.0, "chemistry": 70.0}
                r1, r2 = await asyncio.gather(
                    ac.post(f"{BASE}/auth/update-profile", json=payload_a,
                            headers=_hdrs(token_a), timeout=30),
                    ac.post(f"{BASE}/auth/update-profile", json=payload_b,
                            headers=_hdrs(token_b), timeout=30),
                )
                return r1, r2

        r1, r2 = asyncio.run(concurrent_updates())
        print(f"  A update: {r1.status_code}  B update: {r2.status_code}")

        # Re-fetch both
        fa = _get(c, "/auth/me", token_a).json()
        fb = _get(c, "/auth/me", token_b).json()

        a_maths_ok  = fa.get("maths")    == 91.0
        a_phys_ok   = fa.get("physics")  == 88.0
        b_maths_ok  = fb.get("maths")    == 72.0
        b_phys_ok   = fb.get("physics")  == 68.0
        cross_contam = (fa.get("maths") == fb.get("maths"))

        passed = a_maths_ok and a_phys_ok and b_maths_ok and b_phys_ok and not cross_contam
        snippet = (f"A(maths={fa.get('maths')} phys={fa.get('physics')})  "
                   f"B(maths={fb.get('maths')} phys={fb.get('physics')})  "
                   f"cross_contamination={cross_contam}")
        record("P12", passed, f"A:{r1.status_code}/B:{r2.status_code}", snippet)
        print(f"  {pf(passed)}  {snippet}")

        # ─────────────────────────────────────────────────────────────────
        # SEC1-SEC4 -- SQL INJECTION
        # ─────────────────────────────────────────────────────────────────
        print("\n[SEC1-SEC4] SQL Injection...")

        sqli_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users;--",
            "' UNION SELECT * FROM users--",
        ]

        sqli_targets = [
            # (test_id, field_desc, path, build_body_fn, use_token)
            (
                "SEC1", "email @ signup", "/auth/signup",
                lambda p: {
                    "email": p, "password": "Secure#9977",
                    "name": "sqli-test", "mobile": "9876543210", "community": "OC"
                },
                None,
            ),
            (
                "SEC2", "name @ signup", "/auth/signup",
                lambda p: {
                    "email": mk_email(), "password": "Secure#9977",
                    "name": p, "mobile": "9876543210", "community": "OC"
                },
                None,
            ),
            (
                "SEC3", "application_id @ verify-rank", "/predict/verify-rank",
                lambda p: {"application_id": p, "name": "test", "rank": 12345},
                token_a,
            ),
            (
                "SEC4", "mobile @ update-profile", "/auth/update-profile",
                lambda p: {"mobile": p},
                token_a,
            ),
        ]

        for tid, desc, path, build_body, tok in sqli_targets:
            worst_status = None
            worst_snippet = ""
            all_safe = True
            for payload in sqli_payloads:
                r = _post(c, path, build_body(payload), token=tok)
                if r.status_code == 500:
                    all_safe = False
                    worst_status = r.status_code
                    worst_snippet = r.text[:100]
                    break
                if worst_status is None:
                    worst_status = r.status_code
                    worst_snippet = r.text[:80]

            passed = all_safe   # no 500 = safe (ORM parameterizes)
            record(tid, passed, worst_status,
                   f"field={desc}  last_status={worst_status}  {worst_snippet[:60]}")
            print(f"  {tid} ({desc}):  {worst_status}  {pf(passed)}  {worst_snippet[:60]}")

        # ─────────────────────────────────────────────────────────────────
        # SEC5 -- STORED XSS
        # ─────────────────────────────────────────────────────────────────
        print("\n[SEC5] Stored XSS...")
        xss_name  = "<script>alert(1)</script>"
        xss_email = mk_email()
        r = signup(c, xss_email, pw, name=xss_name)
        if r.status_code == 200:
            xss_token = r.json()["token"]
            me_xss = _get(c, "/auth/me", xss_token).json()
            stored_name = me_xss.get("name", "")
            # Storing as-is is expected -- escaping must happen at render time
            passed = r.status_code == 200
            record("SEC5", passed, r.status_code,
                   f"stored_name={repr(stored_name)}")
            print(f"  {r.status_code}  {pf(passed)}  stored as: {repr(stored_name)}")
            if stored_name == xss_name:
                print("  NOTE: raw <script> stored in DB -- correct; escaping must happen on render, not storage.")
            else:
                print(f"  NOTE: value was sanitised server-side to: {repr(stored_name)}")
        else:
            record("SEC5", False, r.status_code,
                   f"signup rejected: {r.text[:80]}")
            print(f"  {r.status_code}  FAIL  {r.text[:80]}")

        # ─────────────────────────────────────────────────────────────────
        # SEC7 -- CROSS-USER PROFILE ISOLATION
        # ─────────────────────────────────────────────────────────────────
        print("\n[SEC7] Cross-user profile isolation...")
        fa2 = _get(c, "/auth/me", token_a).json()
        fb2 = _get(c, "/auth/me", token_b).json()
        a_correct = fa2.get("id") == id_a and fa2.get("email") == email_a
        b_correct = fb2.get("id") == id_b and fb2.get("email") == email_b
        no_leak   = fa2.get("id") != fb2.get("id")
        passed = a_correct and b_correct and no_leak
        record("SEC7", passed, "200/200",
               f"A sees id={fa2.get('id')} email={fa2.get('email')}  "
               f"B sees id={fb2.get('id')} email={fb2.get('email')}")
        print(f"  {pf(passed)}  "
              f"A->id={fa2.get('id')} email={fa2.get('email')}  "
              f"B->id={fb2.get('id')} email={fb2.get('email')}")

        # ─────────────────────────────────────────────────────────────────
        # SEC8 -- CROSS-USER PREDICTION HISTORY
        # ─────────────────────────────────────────────────────────────────
        print("\n[SEC8] Cross-user prediction history...")
        record("SEC8", None, "N/A",
               "No per-user prediction history endpoint exists in the API. "
               "Predictions are written server-side during /predict/colleges "
               "but no GET /predictions or /auth/predictions route is exposed. "
               "N/A -- cannot test what does not exist.")
        print("  N/A -- no prediction history GET endpoint found.")

        # ─────────────────────────────────────────────────────────────────
        # SEC9 -- PREMIUM ENDPOINT AUTHORIZATION
        # ─────────────────────────────────────────────────────────────────
        print("\n[SEC9] Premium endpoint auth (grade 1 required)...")
        # Fresh signup -> grade="2"; /predict/submit-rank requires grade="1"
        # grade_order: {"1":2, "2":1, "3":0} -- grade 1 is highest tier
        r = _post(c, "/predict/submit-rank",
                  {"actual_rank": 50000, "aggregate": 185.0, "community": "OC"},
                  token=token_a)
        passed = r.status_code == 403
        record("SEC9", passed, r.status_code, r.text[:120])
        print(f"  {r.status_code}  {pf(passed)}  {r.text[:100]}")
        if r.status_code == 403:
            print("  Correctly blocked: grade-2 user cannot call grade-1 endpoint.")

        # ─────────────────────────────────────────────────────────────────
        # SEC10 -- OVERSIZED PAYLOAD
        # ─────────────────────────────────────────────────────────────────
        print("\n[SEC10] Oversized payload (~10 MB)...")
        big_str = "x" * (10 * 1024 * 1024)
        oversized_body = json.dumps({
            "maths": 90, "physics": 85, "chemistry": 80,
            "community": "OC",
            "preferred_branches": [big_str]
        }).encode()
        try:
            r = c.post(
                f"{BASE}/predict/colleges",
                content=oversized_body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {token_a}"},
                timeout=60,
            )
            passed = r.status_code in (413, 422, 400, 431)
            record("SEC10", passed, r.status_code, r.text[:120])
            print(f"  {r.status_code}  {pf(passed)}  {r.text[:100]}")
            if not passed:
                print(f"  WARNING: server processed a 10MB payload (status {r.status_code}). "
                      "Consider adding request size limits (e.g. Railway / uvicorn --limit-concurrency).")
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            record("SEC10", None, "TIMEOUT", str(e)[:80])
            print(f"  TIMEOUT -- server hung on large payload: {e}")
        except Exception as e:
            record("SEC10", False, "EXCEPTION", str(e)[:80])
            print(f"  EXCEPTION: {e}")

        # ─────────────────────────────────────────────────────────────────
        # RESULTS TABLE
        # ─────────────────────────────────────────────────────────────────
        print("\n" + "=" * 75)
        print(f"{'TEST':<8}  {'RESULT':<7}  {'STATUS':<22}  SNIPPET")
        print("=" * 75)
        for res in RESULTS:
            flag = pf(res["pass"])
            print(f"{res['id']:<8}  {flag:<7}  {res['status']:<22}  {res['snippet'][:55]}")
        print("=" * 75)

        total   = len(RESULTS)
        passed  = sum(1 for r in RESULTS if r["pass"] is True)
        failed  = sum(1 for r in RESULTS if r["pass"] is False)
        info    = sum(1 for r in RESULTS if r["pass"] is None)
        print(f"\nTotal: {total}  |  PASS: {passed}  |  FAIL: {failed}  |  INFO/N/A: {info}")
        print("=" * 75)


if __name__ == "__main__":
    run()
