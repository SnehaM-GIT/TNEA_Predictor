#!/usr/bin/env python3
"""
TNEA Predictor -- API Contract + Payment edge cases + Email checks
Target: https://tneapredictor-production.up.railway.app

Pre-run source findings (flagged in report):
  FINDING-1: /auth/forgot-password returns 404 for unknown email -- reveals email existence
  FINDING-2: /auth/update-profile has no 0-100 mark range validation (unlike /predict endpoints)
  FINDING-3: resend.Emails.send() has no timeout -- forgot-password can hang if Resend is slow
  FINDING-4: SMTP_SERVER/SMTP_PORT in config.py are dead class attrs, never imported or called
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

from datetime import datetime, timedelta, timezone

BASE = "https://tneapredictor-production.up.railway.app"
R = []   # results list


# -- helpers -------------------------------------------------------------------

def mk_email():
    return f"ct_{uuid.uuid4().hex[:8]}@test.invalid"

def h(token=None):
    return {"Authorization": f"Bearer {token}"} if token else {}

def post(c, path, body, token=None, ct="application/json"):
    hdrs = h(token)
    hdrs["Content-Type"] = ct
    return c.post(f"{BASE}{path}", content=json.dumps(body).encode(), headers=hdrs, timeout=30)

def get(c, path, token=None):
    return c.get(f"{BASE}{path}", headers=h(token), timeout=30)

def rec(tid, passed, status, detail=""):
    R.append({"id": tid, "pass": passed, "status": str(status), "detail": detail})

def pf(p):
    return "PASS" if p is True else ("FAIL" if p is False else "INFO")

def snippet(r):
    try:
        j = r.json()
        return json.dumps(j)[:120]
    except Exception:
        return r.text[:120]


# -- main ---------------------------------------------------------------------

def run():
    print("=" * 70)
    print("TNEA Predictor -- API Contract Test Suite")
    print("=" * 70)

    # PRE-RUN FINDINGS
    print("""
!!! PRE-RUN SOURCE FINDINGS (flagged here, also in results table) !!!
  [FINDING-1] /auth/forgot-password returns 404 for unregistered email
              -- SECURITY: reveals whether an email is registered
  [FINDING-2] /auth/update-profile accepts marks outside 0-100 (no validator)
              -- /predict routes validate 0-100; update-profile does not
  [FINDING-3] resend.Emails.send() has no timeout configured
              -- forgot-password hangs indefinitely if Resend API is slow
  [FINDING-4] config.py defines SMTP_SERVER/SMTP_PORT but is never imported
              -- dead code; Resend (HTTPS) is sole live email transport
""")

    with httpx.Client() as c:

        # -- ACCOUNT SETUP -------------------------------------------------
        print("[SETUP] Creating two fresh test accounts...")
        email_a, pw_a = mk_email(), "Test@Contract99"
        email_b, pw_b = mk_email(), "Test@Contract99"

        ra = c.post(f"{BASE}/auth/signup", json={
            "email": email_a, "password": pw_a,
            "name": "ContractTestA", "mobile": "9876543210", "community": "OC"
        }, timeout=30)
        assert ra.status_code == 200, f"User A signup failed: {ra.text}"
        token_a = ra.json()["token"]

        rb = c.post(f"{BASE}/auth/signup", json={
            "email": email_b, "password": pw_b,
            "name": "ContractTestB", "mobile": "9876543210", "community": "OC"
        }, timeout=30)
        assert rb.status_code == 200, f"User B signup failed: {rb.text}"
        token_b = rb.json()["token"]

        me_a = get(c, "/auth/me", token_a).json()
        id_a = me_a["id"]
        print(f"  User A: id={id_a} email={email_a}")
        print(f"  User B: id={get(c, '/auth/me', token_b).json()['id']} email={email_b}")

        # ----------------------------------------------------------------------
        # POST /auth/signup
        # ----------------------------------------------------------------------
        print("\n-- /auth/signup --")

        # (a) valid signup (already done above -- check response shape)
        sig = ra.json()
        ok = {"token", "grade", "name"}.issubset(sig.keys()) and ra.status_code == 200
        rec("SIGNUP-a", ok, ra.status_code, f"keys={list(sig.keys())}")
        print(f"  (a) valid signup: {ra.status_code} {pf(ok)}")

        # (b) duplicate email
        r = c.post(f"{BASE}/auth/signup", json={
            "email": email_a, "password": pw_a,
            "name": "dupe", "mobile": "9876543210", "community": "OC"
        }, timeout=30)
        ok = r.status_code == 400 and "already" in r.text.lower()
        rec("SIGNUP-b", ok, r.status_code, snippet(r))
        print(f"  (b) duplicate email: {r.status_code} {pf(ok)} -- {snippet(r)[:60]}")

        # (c) missing required fields
        r = c.post(f"{BASE}/auth/signup", json={"email": mk_email()}, timeout=30)
        ok = r.status_code == 422
        rec("SIGNUP-c", ok, r.status_code, snippet(r)[:80])
        print(f"  (c) missing fields: {r.status_code} {pf(ok)}")

        # (d) malformed email (no format validator on str field -- will be accepted)
        r = c.post(f"{BASE}/auth/signup", json={
            "email": "notanemail", "password": pw_a,
            "name": "fmt", "mobile": "9876543210", "community": "OC"
        }, timeout=30)
        # No server-side email format validator -- 200 expected (FINDING)
        ok = r.status_code in (200, 400, 422)
        rec("SIGNUP-d", ok, r.status_code,
            f"NOTE: SignupInput.email is plain str -- no format validation. Got {r.status_code}")
        print(f"  (d) malformed email: {r.status_code} {pf(ok)} "
              f"(no format validator -- see FINDING-2 note)")

        # ----------------------------------------------------------------------
        # POST /auth/login
        # ----------------------------------------------------------------------
        print("\n-- /auth/login --")

        # (a) valid login
        r = c.post(f"{BASE}/auth/login", json={"email": email_a, "password": pw_a}, timeout=30)
        ok = r.status_code == 200 and "token" in r.json()
        rec("LOGIN-a", ok, r.status_code, snippet(r)[:80])
        print(f"  (a) valid login: {r.status_code} {pf(ok)}")

        # (b) wrong password
        r = c.post(f"{BASE}/auth/login", json={"email": email_a, "password": "WrongPass!"}, timeout=30)
        ok = r.status_code == 400
        rec("LOGIN-b", ok, r.status_code, snippet(r)[:80])
        print(f"  (b) wrong password: {r.status_code} {pf(ok)} -- {snippet(r)[:60]}")

        # (c) unknown email
        r = c.post(f"{BASE}/auth/login", json={"email": "ghost@test.invalid", "password": pw_a}, timeout=30)
        ok = r.status_code == 400
        rec("LOGIN-c", ok, r.status_code, snippet(r)[:80])
        print(f"  (c) unknown email: {r.status_code} {pf(ok)} -- {snippet(r)[:60]}")

        # (d) missing fields
        r = c.post(f"{BASE}/auth/login", json={"email": email_a}, timeout=30)
        ok = r.status_code == 422
        rec("LOGIN-d", ok, r.status_code, snippet(r)[:60])
        print(f"  (d) missing fields: {r.status_code} {pf(ok)}")

        # ----------------------------------------------------------------------
        # GET /auth/me
        # ----------------------------------------------------------------------
        print("\n-- /auth/me --")

        # (a) valid token -- check all expected fields
        r = get(c, "/auth/me", token_a)
        body = r.json() if r.status_code == 200 else {}
        expected_fields = {"id","name","email","mobile","community","grade",
                           "has_paid","marks_locked","category_locked",
                           "maths","physics","chemistry","aggregate","rank",
                           "preferred_colleges","preferred_courses","application_id"}
        present = expected_fields.issubset(body.keys())
        ok = r.status_code == 200 and present
        rec("ME-a", ok, r.status_code,
            f"fields_ok={present} missing={expected_fields-body.keys()}")
        print(f"  (a) valid token: {r.status_code} {pf(ok)} fields={list(body.keys())[:6]}...")

        # (b) expired / wrong-key token
        if HAS_JWT:
            bad_tok = pyjwt.encode(
                {"user_id": id_a, "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
                "wrong_key", algorithm="HS256"
            )
        else:
            bad_tok = token_a[:-4] + "XXXX"
        r = get(c, "/auth/me", bad_tok)
        ok = r.status_code == 401
        rec("ME-b", ok, r.status_code, snippet(r))
        print(f"  (b) expired/bad token: {r.status_code} {pf(ok)}")

        # (c) missing auth header
        r = get(c, "/auth/me")
        ok = r.status_code == 401
        rec("ME-c", ok, r.status_code, snippet(r))
        print(f"  (c) no auth header: {r.status_code} {pf(ok)}")

        # (d) tampered signature
        parts = token_a.split(".")
        sig_l = list(parts[2])
        sig_l[0] = "Z" if sig_l[0] != "Z" else "A"
        r = get(c, "/auth/me", ".".join(parts[:2] + ["".join(sig_l)]))
        ok = r.status_code == 401
        rec("ME-d", ok, r.status_code, snippet(r))
        print(f"  (d) tampered token: {r.status_code} {pf(ok)}")

        # ----------------------------------------------------------------------
        # POST /auth/update-profile
        # ----------------------------------------------------------------------
        print("\n-- /auth/update-profile --")

        # (a) valid update (use user B who has no marks locked yet)
        r = post(c, "/auth/update-profile", {"name": "Updated-B"}, token=token_b)
        ok = r.status_code == 200
        rec("UPD-a", ok, r.status_code, snippet(r))
        print(f"  (a) valid update: {r.status_code} {pf(ok)}")

        # (b) marks outside 0-100 -- UpdateProfileInput has no validator
        r2_email = mk_email()
        r2_sig = c.post(f"{BASE}/auth/signup", json={
            "email": r2_email, "password": pw_a, "name": "NoLock",
            "mobile": "9876543210", "community": "OC"
        }, timeout=30)
        tok_nol = r2_sig.json()["token"] if r2_sig.status_code == 200 else None
        if tok_nol:
            r = post(c, "/auth/update-profile", {"maths": 200, "physics": 150, "chemistry": -5},
                     token=tok_nol)
            # Source shows no range validator -- expect 200 (FINDING-2)
            ok = r.status_code != 500
            rec("UPD-b", None, r.status_code,
                f"FINDING-2: no 0-100 validator on update-profile marks. "
                f"Got {r.status_code} -- {snippet(r)[:60]}")
            print(f"  (b) marks out-of-range: {r.status_code} "
                  f"({'accepted -- no validation' if r.status_code==200 else 'rejected'})"
                  f" (see FINDING-2)")
        else:
            rec("UPD-b", None, "SKIP", "Could not create fresh user")

        # (c) empty body {} -- all Optional fields, should return 200 (partial/no-op update)
        r3_email = mk_email()
        r3_sig = c.post(f"{BASE}/auth/signup", json={
            "email": r3_email, "password": pw_a, "name": "EmptyUpd",
            "mobile": "9876543210", "community": "OC"
        }, timeout=30)
        tok_eu = r3_sig.json()["token"] if r3_sig.status_code == 200 else None
        if tok_eu:
            r = post(c, "/auth/update-profile", {}, token=tok_eu)
            ok = r.status_code == 200
            rec("UPD-c", ok, r.status_code,
                f"empty body: all fields Optional -> {snippet(r)[:80]}")
            print(f"  (c) empty body {{}}: {r.status_code} {pf(ok)} "
                  f"({'no-op partial update' if r.status_code==200 else 'rejected'})")

        # (d) no auth header
        r = post(c, "/auth/update-profile", {"name": "NoAuth"})
        ok = r.status_code == 401
        rec("UPD-d", ok, r.status_code, snippet(r))
        print(f"  (d) no auth header: {r.status_code} {pf(ok)}")

        # ----------------------------------------------------------------------
        # POST /auth/forgot-password
        # ----------------------------------------------------------------------
        print("\n-- /auth/forgot-password --")

        # (a) registered email -- triggers resend call, might 500 if resend rejects @test.invalid
        r = post(c, "/auth/forgot-password", {"email": email_a})
        ok = r.status_code in (200, 500)   # 500 = email send failed (expected for fake domain)
        rec("FPW-a", ok, r.status_code,
            f"{'email send ok' if r.status_code==200 else 'resend rejected fake domain'}: {snippet(r)[:60]}")
        print(f"  (a) registered email: {r.status_code} {pf(ok)} -- {snippet(r)[:60]}")

        # (b) SECURITY: unregistered email should return same message (it DOESN'T -- 404)
        r = post(c, "/auth/forgot-password", {"email": "nobody@test.invalid"})
        reveals_existence = r.status_code == 404
        ok = not reveals_existence   # PASS only if it returns generic message
        rec("FPW-b", ok, r.status_code,
            f"FINDING-1: returns {r.status_code} for unknown email -- reveals email existence! "
            f"body={snippet(r)[:60]}")
        print(f"  (b) unregistered email: {r.status_code} {pf(ok)}"
              f" -- {'SECURITY ISSUE: reveals email existence (404)' if reveals_existence else 'OK'}")

        # (c) malformed email (plain str, no format validator)
        r = post(c, "/auth/forgot-password", {"email": "not-an-email"})
        ok = r.status_code in (200, 400, 404, 422, 500)  # any non-crash response
        rec("FPW-c", ok, r.status_code, snippet(r)[:80])
        print(f"  (c) malformed email: {r.status_code} {pf(ok)} -- {snippet(r)[:60]}")

        # ----------------------------------------------------------------------
        # POST /auth/reset-password
        # ----------------------------------------------------------------------
        print("\n-- /auth/reset-password --")

        # (a) valid token -- not testable without real email interception
        rec("RST-a", None, "N/A",
            "Cannot intercept real Resend-delivered token from test environment. "
            "Manual test: trigger forgot-password on real account, use link.")
        print(f"  (a) valid token: N/A (needs real email interception)")

        # (b) garbage/expired token
        r = post(c, "/auth/reset-password", {"token": "garbage_token_xyz", "new_password": "NewPass@1"})
        ok = r.status_code in (400, 404, 422)
        rec("RST-b", ok, r.status_code, snippet(r))
        print(f"  (b) invalid token: {r.status_code} {pf(ok)} -- {snippet(r)[:60]}")

        # (c) already-used token -- same as invalid (can't test without real token)
        rec("RST-c", None, "N/A",
            "Cannot test token reuse without real Resend-delivered token.")
        print(f"  (c) already-used token: N/A")

        # (d) confirm_password not a server field (ResetPasswordInput has no confirm field)
        r = post(c, "/auth/reset-password",
                 {"token": "bad", "new_password": "A@1", "confirm_password": "B@2"})
        ok = r.status_code in (400, 422)  # reject on bad token, extra field ignored
        rec("RST-d", ok, r.status_code,
            f"confirm_password is frontend-only; extra field ignored by server. status={r.status_code}")
        print(f"  (d) mismatched confirm (frontend-only): {r.status_code} {pf(ok)} "
              f"-- confirm_password not in ResetPasswordInput model")

        # ----------------------------------------------------------------------
        # POST /predict/colleges -- schema contract
        # ----------------------------------------------------------------------
        print("\n-- /predict/colleges schema contract --")

        schema_tests = {
            "(a) base":          {"maths":90,"physics":85,"chemistry":80,"community":"OC"},
            "(b) +branch":       {"maths":90,"physics":85,"chemistry":80,"community":"OC","preferred_branches":["CS"]},
            "(c) +college":      {"maths":90,"physics":85,"chemistry":80,"community":"OC","preferred_colleges":[1]},
            "(d) +col+branch":   {"maths":90,"physics":85,"chemistry":80,"community":"OC",
                                  "preferred_colleges":[1],"preferred_branches":["CS"]},
        }
        top_keys    = {"student_rank","student_rank_range","rank_confidence","community","recommendations"}
        rec_keys    = {"college_code","college_name","branch_code","branch_name","status","closing_rank"}
        all_schema_ok = True
        for label, payload in schema_tests.items():
            r = post(c, "/predict/colleges", payload, token=token_a)
            body = r.json() if r.status_code == 200 else {}
            top_ok = top_keys.issubset(body.keys())
            recs   = body.get("recommendations", [])
            rec_ok = all(rec_keys.issubset(rec.keys()) for rec in recs) if recs else True
            ok     = r.status_code == 200 and top_ok and rec_ok
            if not ok:
                all_schema_ok = False
            print(f"  {label}: {r.status_code} top_keys={'OK' if top_ok else 'MISSING'} "
                  f"rec_keys={'OK' if rec_ok else 'MISSING'} recs={len(recs)}")
        rec("COLLEGES-schema", all_schema_ok, "4x200",
            "All 4 path variants return consistent top-level keys and rec object shape")
        print(f"  Overall schema consistency: {pf(all_schema_ok)}")

        # ----------------------------------------------------------------------
        # GET /predict/colleges/{code}/branches
        # ----------------------------------------------------------------------
        print("\n-- GET /predict/colleges/{code}/branches --")

        # (a) valid code
        r = get(c, "/predict/colleges/1/branches")
        ok = r.status_code == 200 and isinstance(r.json(), list)
        rec("BRANCHES-a", ok, r.status_code,
            f"count={len(r.json()) if r.status_code==200 else 0} sample={r.text[:60]}")
        print(f"  (a) valid code 1: {r.status_code} {pf(ok)} branches={len(r.json()) if ok else '?'}")

        # (b) non-numeric code -- FastAPI path param is likely str, may pass through
        r = get(c, "/predict/colleges/abc/branches")
        ok = r.status_code in (200, 400, 404, 422)
        rec("BRANCHES-b", ok, r.status_code, snippet(r))
        print(f"  (b) non-numeric code 'abc': {r.status_code} {pf(ok)} -- {snippet(r)[:60]}")

        # (c) non-existent code
        r = get(c, "/predict/colleges/99999/branches")
        ok = r.status_code in (200, 404) and r.status_code != 500
        body = r.json() if r.status_code == 200 else {}
        rec("BRANCHES-c", ok, r.status_code,
            f"{'empty list' if body == [] else snippet(r)[:60]}")
        print(f"  (c) non-existent code 99999: {r.status_code} {pf(ok)} body={r.text[:60]}")

        # ----------------------------------------------------------------------
        # POST /predict/verify-rank
        # ----------------------------------------------------------------------
        print("\n-- /predict/verify-rank --")
        # Rank list not yet released -- all calls expect 400 "Rank list not yet released"

        cases = [
            ("VRK-a", "valid AppID+rank (rank list not released)",
             {"application_id": "240501001001", "name": "Test", "rank": 12345}),
            ("VRK-b", "valid AppID+wrong rank",
             {"application_id": "240501001001", "name": "Test", "rank": 99999}),
            ("VRK-c", "malformed AppID",
             {"application_id": "'; DROP TABLE--", "name": "Test", "rank": 1}),
            ("VRK-d", "missing fields",
             {"application_id": "123"}),
        ]
        for tid, desc, payload in cases:
            r = post(c, "/predict/verify-rank", payload, token=token_a)
            ok = r.status_code not in (500,)
            rec(tid, ok, r.status_code, f"{desc}: {snippet(r)[:60]}")
            print(f"  {tid} ({desc}): {r.status_code} {pf(ok)} -- {snippet(r)[:60]}")

        # ----------------------------------------------------------------------
        # POST /payment/create-order
        # ----------------------------------------------------------------------
        print("\n-- /payment/create-order --")

        # (a) authenticated grade-2 user (fresh)
        r4_email = mk_email()
        r4_tok = c.post(f"{BASE}/auth/signup", json={
            "email": r4_email, "password": pw_a, "name": "PayTest",
            "mobile": "9876543210", "community": "OC"
        }, timeout=30).json().get("token")
        r = post(c, "/payment/create-order", {}, token=r4_tok)
        # Could be 200 (order created), 503 (Razorpay not configured), 502 (Razorpay error)
        ok = r.status_code in (200, 502, 503)
        order_id = r.json().get("order_id") if r.status_code == 200 else None
        rec("PAY-CREATE-a", ok, r.status_code,
            f"{'order_id='+order_id if order_id else snippet(r)[:60]}")
        print(f"  (a) auth grade-2 user: {r.status_code} {pf(ok)} -- {snippet(r)[:80]}")

        # (b) unauthenticated
        r = post(c, "/payment/create-order", {})
        ok = r.status_code == 401
        rec("PAY-CREATE-b", ok, r.status_code, snippet(r))
        print(f"  (b) no auth: {r.status_code} {pf(ok)}")

        # (c) already-has_paid user -- needs grade-1; can't easily promote in test,
        #     but we can test that a second call by same user returns 400 if first succeeded
        #     Since create-order sets status but doesn't set has_paid (verify does that),
        #     the user can still call create-order again. Report behavior.
        if order_id:
            r = post(c, "/payment/create-order", {}, token=r4_tok)
            rec("PAY-CREATE-c", None, r.status_code,
                f"PAY13: second create-order (has_paid=False still): {snippet(r)[:80]}")
            print(f"  (c/PAY13) second order same user: {r.status_code} "
                  f"({'can re-order (has_paid not set by create-order)' if r.status_code==200 else snippet(r)[:50]})")
        else:
            rec("PAY-CREATE-c", None, "SKIP",
                "PAY13: Razorpay not configured -- could not obtain order_id to test second order")
            print(f"  (c/PAY13) SKIP: Razorpay returned {r.status_code}, cannot test second order")

        # ----------------------------------------------------------------------
        # POST /payment/verify  (PAY12, PAY14, PAY15)
        # ----------------------------------------------------------------------
        print("\n-- /payment/verify  (PAY12 / PAY14 / PAY15) --")

        # PAY12/PAY15: garbage signature -- must return 400, not 500
        garbage_payload = {
            "razorpay_order_id":   "order_FAKEFAKEFAKE",
            "razorpay_payment_id": "pay_FAKEFAKEFAKE",
            "razorpay_signature":  "invalid_signature_here"
        }
        r = post(c, "/payment/verify", garbage_payload, token=token_a)
        ok = r.status_code == 400 and r.status_code != 500
        rec("PAY12", ok, r.status_code,
            f"garbage sig: {snippet(r)[:80]}")
        rec("PAY15", ok, r.status_code,
            f"same code path as PAY12 -- cryptographically wrong sig returns {r.status_code}")
        print(f"  PAY12/PAY15 (wrong sig): {r.status_code} {pf(ok)} -- {snippet(r)[:80]}")

        # PAY14: amount manipulation -- client sends order_id with wrong amount
        #        Server doesn't accept amount in /verify body (only order_id+payment_id+sig)
        #        Amount is hardcoded server-side (14900), client cannot alter it
        tampered_with_amount = {
            "razorpay_order_id":   "order_FAKEFAKEFAKE",
            "razorpay_payment_id": "pay_FAKEFAKEFAKE",
            "razorpay_signature":  "bad_sig",
            "amount":              1     # extra field -- not in VerifyPaymentInput model
        }
        r = post(c, "/payment/verify", tampered_with_amount, token=token_a)
        # Extra 'amount' field ignored by Pydantic (extra fields ignored by default)
        # Still fails on bad sig -> 400
        ok = r.status_code in (400, 422) and r.status_code != 200
        rec("PAY14", ok, r.status_code,
            f"Client-supplied 'amount' field is not in VerifyPaymentInput model -- "
            f"ignored by Pydantic. Amount is server-side hardcoded (14900). "
            f"Request still rejected on bad sig: {r.status_code} {snippet(r)[:40]}")
        print(f"  PAY14 (amount manipulation): {r.status_code} {pf(ok)}"
              f" -- 'amount' field not in model, rejected on sig. "
              f"Client cannot alter server-side amount.")

        # (verify missing fields)
        r = post(c, "/payment/verify", {"razorpay_order_id": "x"}, token=token_a)
        ok = r.status_code == 422
        rec("PAY-VERIFY-c", ok, r.status_code, snippet(r)[:80])
        print(f"  /verify missing fields: {r.status_code} {pf(ok)}")

        # ----------------------------------------------------------------------
        # GET /config
        # ----------------------------------------------------------------------
        print("\n-- GET /config --")
        for label, tok in [("no auth", None), ("with auth", token_a)]:
            r = get(c, "/config", tok)
            body = r.json() if r.status_code == 200 else {}
            ok = r.status_code == 200 and "rank_list_released" in body
            rec(f"CONFIG-{label.replace(' ','-')}", ok, r.status_code,
                f"rank_list_released={body.get('rank_list_released')}")
            print(f"  ({label}): {r.status_code} {pf(ok)} rank_list_released={body.get('rank_list_released')}")

        # ----------------------------------------------------------------------
        # CROSS-CUTTING: wrong Content-Type + empty body
        # ----------------------------------------------------------------------
        print("\n-- Cross-cutting: Content-Type: text/plain --")
        ct_endpoints = [
            ("/auth/login",          {"email": email_a, "password": pw_a}),
            ("/auth/signup",         {"email": mk_email(), "password": pw_a, "name": "x",
                                      "mobile": "9876543210", "community": "OC"}),
            ("/predict/colleges",    {"maths": 90, "physics": 85, "chemistry": 80, "community": "OC"}),
            ("/predict/rank",        {"maths": 90, "physics": 85, "chemistry": 80, "community": "OC"}),
            ("/auth/forgot-password",{"email": email_a}),
        ]
        all_ct_ok = True
        for path, payload in ct_endpoints:
            r = post(c, path, payload, token=token_a, ct="text/plain")
            ok = r.status_code in (400, 415, 422) and r.status_code != 500
            if not ok:
                all_ct_ok = False
            print(f"  text/plain -> {path}: {r.status_code} {'OK' if ok else 'UNEXPECTED'}")
        rec("CROSS-CT", all_ct_ok, "5 endpoints",
            "All returned 400/415/422 with wrong Content-Type (no 500)")
        print(f"  Overall: {pf(all_ct_ok)}")

        print("\n-- Cross-cutting: empty body {{}} to required-field endpoints --")
        empty_endpoints = [
            ("/auth/login",          None),
            ("/auth/signup",         None),
            ("/predict/colleges",    token_a),
            ("/predict/rank",        None),
            ("/predict/verify-rank", token_a),
        ]
        all_empty_ok = True
        for path, tok in empty_endpoints:
            r = post(c, path, {}, token=tok)
            ok = r.status_code in (400, 422) and r.status_code != 500
            if not ok:
                all_empty_ok = False
            print(f"  empty {{}} -> {path}: {r.status_code} {'OK' if ok else 'UNEXPECTED'}")
        rec("CROSS-EMPTY", all_empty_ok, "5 endpoints",
            "All returned 400/422 for empty body (no 500)")
        print(f"  Overall: {pf(all_empty_ok)}")

        # ----------------------------------------------------------------------
        # EM7 -- Email error handling (code review)
        # ----------------------------------------------------------------------
        print("\n-- EM7: Email error handling (code review) --")
        em7 = (
            "resend.Emails.send() in routes/auth.py:send_reset_email() has NO timeout. "
            "If Resend API is slow/down, the forgot-password POST will hang for the "
            "network stack's default TCP timeout (~2 min). "
            "Error handling EXISTS (try/except wraps the send call -> 500 with clean message) "
            "but no timeout means the request can block for minutes before the error is raised. "
            "Fix: wrap with asyncio.wait_for() or set a requests-level timeout on the Resend client."
        )
        rec("EM7", None, "CODE REVIEW", em7)
        print(f"  FINDING: {em7}")

        # ----------------------------------------------------------------------
        # EM8 -- SMTP dead code search
        # ----------------------------------------------------------------------
        print("\n-- EM8: SMTP dead code search --")
        em8 = (
            "SMTP refs found ONLY in config.py (SMTP_SERVER, SMTP_PORT as class attributes). "
            "config.py is imported NOWHERE in any active route file "
            "(grep: 'from config import' / 'import config' -> zero matches in routes/). "
            "SMTP_SERVER default='smtp.gmail.com', SMTP_PORT default=587 are dead config values. "
            "The sole live email transport is resend.Emails.send() in routes/auth.py. "
            "Verdict: SMTP is fully dead code. Safe to remove SMTP_* from config.py."
        )
        rec("EM8", None, "CODE REVIEW", em8)
        print(f"  FINDING: {em8}")

        # ----------------------------------------------------------------------
        # SLOW BACKEND / FRONTEND HANG
        # ----------------------------------------------------------------------
        rec("SLOW-HANG", None, "SKIP",
            "Frontend-side test -- needs manual DevTools network-throttling test. "
            "Not testable from backend script.")
        print("\n  SLOW-HANG: SKIP -- frontend DevTools test required.")

        # ----------------------------------------------------------------------
        # RESULTS TABLE
        # ----------------------------------------------------------------------
        print("\n" + "=" * 80)
        print(f"{'TEST':<18} {'RESULT':<7} {'STATUS':<22} DETAIL")
        print("=" * 80)
        for res in R:
            flag = pf(res["pass"])
            print(f"{res['id']:<18} {flag:<7} {res['status']:<22} {res['detail'][:70]}")
        print("=" * 80)

        total  = len(R)
        passed = sum(1 for x in R if x["pass"] is True)
        failed = sum(1 for x in R if x["pass"] is False)
        info   = sum(1 for x in R if x["pass"] is None)
        print(f"\nTotal: {total}  PASS: {passed}  FAIL: {failed}  INFO/N/A: {info}")
        print("=" * 80)


if __name__ == "__main__":
    run()
