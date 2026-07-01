"""
TNEA Predictor edge-case load test — targeted abuse/edge patterns not covered
by the standard locustfile.py.

Written against the ACTUAL backend contract (backend/routes/predict.py,
payment.py, auth.py), not a hypothetical one. Notable deltas from a naive
spec that assumes a generic REST shape:

  - There is no "simulate-allotment" endpoint / choice-list allotment engine.
    Scenario 1 is adapted to /predict/combo, which is the real endpoint that
    takes a flat `preferred_colleges: List[int]` + `preferred_branches: List[str]`
    and — when BOTH are supplied — computes the full CARTESIAN PRODUCT of the
    two lists (see ml_service.get_college_predictions_filtered PATH 1). So
    35 colleges x 6 branches = 210 real combos computed server-side per call,
    which is a faithful analog of "200+ choices" against real code.
  - /predict/combo requires grade >= "2" (require_grade), i.e. a paid user.
    None of the generic loadtest_user_NNN accounts are known to be premium,
    so this scenario logs in with a supplied real premium account. All
    HeavySimUser instances share that one account/token — fine, since JWTs
    are stateless and this only stresses the compute path, not per-user state.
  - /predict/combo, /predict/colleges, /predict/rank are all rate-limited via
    slowapi keyed on remote IP (10/day, 30/day, 50/day respectively) — NOT
    per-user. Running this whole file from one machine means the WHOLE
    scenario 1 population shares a 10-request/day budget on that route, and
    scenario 2 + scenario 3's mid-cycle predictions share a 30-request/day
    budget on /predict/colleges. Expect most requests past that budget to
    come back 429, by design — that's a real constraint of the deployed
    app, not a bug in this test file. Treat 429 as a distinct outcome from
    5xx/timeout when reporting.
  - Login response body key is "token", not "access_token"
    (backend/routes/auth.py:203).
  - /payment/create-order-marks takes NO JSON body (amount is hardcoded
    server-side at 2500 paise) and requires user.has_paid == True, else 403.
  - Unlike /payment/create-order (which reuses any pending order within a
    15-minute TTL to avoid duplicate Razorpay calls/DB rows),
    /payment/create-order-marks has NO such dedup/reuse guard — every call
    hits Razorpay and inserts a new Payment row. That asymmetry is exactly
    what Scenario 3 is probing.
  - /auth/update-profile 403s on marks fields once user.marks_locked is True
    (set True on successful /payment/verify). A premium account is normally
    marks-locked, so rapid marks-churn there is expected to 403 consistently
    under load — the thing being tested is that the guard holds up under
    concurrency, not that the update succeeds.

Accounts:
  - Generic pool: loadtest_user_001..100 @pickmyseat.in / LoadTest@2026
    (used for Scenario 2 — no premium requirement for /predict/colleges).
  - Premium account (required for Scenario 1 and Scenario 3): set via
    PREMIUM_EMAIL / PREMIUM_PASSWORD below.
"""

import random
from locust import HttpUser, task, between

BASE_URL = "https://tneapredictor-production.up.railway.app"

TEST_ACCOUNTS = [
    {"email": f"loadtest_user_{i:03d}@pickmyseat.in", "password": "LoadTest@2026"}
    for i in range(1, 101)
]

# Real premium (has_paid=True) test account — required for /predict/combo
# (grade>=2 gate) and /payment/create-order-marks (has_paid gate).
PREMIUM_ACCOUNT = {
    "email": "charanjagan2004@gmail.com",
    "password": "charanjagan",
}

VALID_COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "ST", "SCA"]

# Real branch codes confirmed present in backend/data/cleaned/course_codes.csv
BRANCHES = ["CS", "EC", "ME", "CE", "IT", "EE"]

# Real college codes confirmed present in backend/data/cleaned/college_codes.csv
# (codes are NOT contiguous integers — using the actual values, not a zfill'd
# range guess, since /predict/combo's preferred_colleges is List[int]).
REAL_COLLEGE_CODES = [
    1, 2, 3, 4, 5, 1013, 1014, 1015, 1026, 1101, 1106, 1107, 1110, 1112, 1113,
    1114, 1115, 1116, 1118, 1120, 1122, 1123, 1124, 1125, 1126, 1127, 1128,
    1129, 1130, 1132, 1133, 1134, 1135, 1137,
]  # 34 real colleges x 6 branches = 204 combos computed server-side per call


def _login(client, creds):
    r = client.post("/auth/login", json=creds, name="/auth/login")
    token = r.json().get("token", "") if r.status_code == 200 else ""
    return {"Authorization": f"Bearer {token}"} if token else {}


class HeavySimUser(HttpUser):
    """
    Scenario 1 — large combo payload.

    Real analog of "200+ choices": /predict/combo with a full
    preferred_colleges x preferred_branches cartesian product (34 x 6 = 204
    combos), which is exactly what ml_service.get_college_predictions_filtered
    PATH 1 computes when both filter lists are non-empty. Tests whether the
    prediction/rank-lookup path degrades or crashes under a genuinely heavy
    per-request combo count, and whether it's fast enough to not blow past
    the 30s client timeout.

    Requires grade >= "2" (paid), so all instances share PREMIUM_ACCOUNT.
    /predict/combo is capped at 10 requests/day per source IP server-side —
    with a single test-runner IP, expect most of this scenario's traffic to
    legitimately 429 after the first few hits.
    """
    weight = 3
    wait_time = between(5, 10)
    host = BASE_URL

    def on_start(self):
        self.headers = _login(self.client, PREMIUM_ACCOUNT)

    @task
    def simulate_with_large_choicelist(self):
        payload = {
            "maths": random.uniform(60, 100),
            "physics": random.uniform(60, 100),
            "chemistry": random.uniform(60, 100),
            "community": random.choice(VALID_COMMUNITIES),
            "top_n": 20,  # server clamps top_n to max 20 regardless of request
            "preferred_colleges": REAL_COLLEGE_CODES,
            "preferred_branches": BRANCHES,
        }
        with self.client.post(
            "/predict/combo",
            json=payload,
            headers=self.headers,
            name="/predict/combo [200+ choices]",
            timeout=30,
            catch_response=True,
        ) as r:
            # 403 = grade gate, 429 = daily IP rate limit — both expected/acceptable
            if r.status_code in (200, 403, 429):
                r.success()
            elif r.status_code == 500:
                r.failure(f"500 internal error: {r.text[:120]}")


class SameMarksCrowd(HttpUser):
    """
    Scenario 2 — mass identical-marks prediction.

    Simulates a large group of students clustered around a common aggregate
    (maths=95, physics=90, chemistry=90 -> aggregate 185.0), hitting
    /predict/colleges concurrently. Tests whether repeated identical inputs
    are handled gracefully (consistent results, no queue buildup) vs.
    recomputed from scratch every time, and probes the cache boundary with a
    +/-1 mark variation on chemistry.

    /predict/colleges is rate-limited to 30/day per source IP — shared with
    MarksUpdateAbuser's mid-cycle predictions in a combined run.
    """
    weight = 5
    wait_time = between(1, 4)
    host = BASE_URL

    def on_start(self):
        self.headers = _login(self.client, random.choice(TEST_ACCOUNTS))

    @task(4)
    def predict_same_marks(self):
        payload = {
            "maths": 95,
            "physics": 90,
            "chemistry": 90,
            "community": random.choice(["OC", "BC", "MBC"]),
            "top_n": 20,
        }
        with self.client.post(
            "/predict/colleges",
            json=payload,
            headers=self.headers,
            name="/predict/colleges [same marks cluster]",
            catch_response=True,
        ) as r:
            if r.status_code in (200, 429):
                r.success()
            elif r.status_code == 500:
                r.failure(f"500 internal error: {r.text[:120]}")

    @task(1)
    def predict_slight_variation(self):
        payload = {
            "maths": 95,
            "physics": 90,
            "chemistry": random.choice([89, 90, 91]),
            "community": "OC",
            "top_n": 20,
        }
        with self.client.post(
            "/predict/colleges",
            json=payload,
            headers=self.headers,
            name="/predict/colleges [near-identical marks]",
            catch_response=True,
        ) as r:
            if r.status_code in (200, 429):
                r.success()
            elif r.status_code == 500:
                r.failure(f"500 internal error: {r.text[:120]}")


class MarksUpdateAbuser(HttpUser):
    """
    Scenario 3 — repeat marks-update payment-order abuse.

    Uses a single fixed premium (has_paid=True) account to simulate one
    abusive user hammering /payment/create-order-marks. Unlike
    /payment/create-order, this endpoint has NO pending-order reuse/TTL
    guard — every call is expected to hit Razorpay and insert a fresh
    Payment row, so this is a direct probe of whether that's actually
    unbounded in production.

    Also fires rapid /auth/update-profile marks changes (expected to 403
    since a paid account is marks-locked — the check under test is that the
    lock guard holds under concurrency) and interleaves /predict/colleges
    calls to probe for any race between a marks write and a read of those
    same marks.
    """
    weight = 1
    wait_time = between(0.5, 2)
    host = BASE_URL

    def on_start(self):
        self.headers = _login(self.client, PREMIUM_ACCOUNT)

    @task(3)
    def spam_marks_update_order(self):
        with self.client.post(
            "/payment/create-order-marks",
            headers=self.headers,
            name="/payment/create-order-marks [spam]",
            catch_response=True,
        ) as r:
            # 200=order created, 403=not premium, 503=Razorpay down -- all acceptable
            if r.status_code in (200, 403, 503):
                r.success()
            elif r.status_code == 500:
                r.failure(f"500 internal error: {r.text[:120]}")

    @task(2)
    def update_marks_rapidly(self):
        with self.client.post(
            "/auth/update-profile",
            json={
                "maths": random.randint(50, 100),
                "physics": random.randint(50, 100),
                "chemistry": random.randint(50, 100),
            },
            headers=self.headers,
            name="/auth/update-profile [rapid changes]",
            catch_response=True,
        ) as r:
            # 403 expected/acceptable once marks_locked is True
            if r.status_code in (200, 403):
                r.success()
            elif r.status_code == 500:
                r.failure(f"500 internal error: {r.text[:120]}")

    @task(1)
    def trigger_prediction_mid_cycle(self):
        with self.client.post(
            "/predict/colleges",
            json={
                "maths": random.randint(50, 100),
                "physics": random.randint(50, 100),
                "chemistry": random.randint(50, 100),
                "community": "OC",
                "top_n": 10,
            },
            headers=self.headers,
            name="/predict/colleges [during marks churn]",
            catch_response=True,
        ) as r:
            if r.status_code in (200, 429):
                r.success()
            elif r.status_code == 500:
                r.failure(f"500 internal error: {r.text[:120]}")


# === HOW TO RUN ===
#
# locust -f load_test/locustfile_edge_cases.py \
#   --host=https://tneapredictor-production.up.railway.app \
#   --headless -u 200 -r 20 --run-time 10m \
#   --csv=results_edge_cases
#
# NOTE: /predict/combo (10/day), /predict/colleges (30/day) are rate-limited
# per source IP server-side. Running 200 users from one machine means these
# routes' daily budget is exhausted almost immediately — the traffic beyond
# that legitimately gets 429, which this file treats as a success/expected
# outcome (not a failure) so it doesn't pollute the failure count. Report
# 429 rate separately from actual 5xx/timeout/connection-error rates.
#
# === WHAT TO REPORT (per scenario, not just aggregate) ===
#
# 1. /predict/combo [200+ choices]:
#    - Valid result vs crash/timeout vs 429 (rate-limited) breakdown.
#    - Response time for the 200-status requests specifically (429s will
#      distort the aggregate if not filtered out).
#    - Any 5xx or connection errors.
#    - Do other concurrent users' standard-endpoint response times degrade
#      while this scenario's heavy combo requests are in flight?
#
# 2. /predict/colleges [same marks cluster] / [near-identical marks]:
#    - Do identical-marks requests return identical results?
#    - Any evidence of caching (faster p50 after the first hit vs cold)?
#    - Queue buildup under the volume of identical computations (excluding
#      429-rate-limited requests from the timing analysis)?
#
# 3. /payment/create-order-marks [spam] + /auth/update-profile [rapid changes]:
#    - Any rate-limiting/throttling on create-order-marks specifically, or
#      does every call create a fresh order + DB row (no dedup guard exists
#      in the code as of this writing)?
#    - Orphaned payment row count for the abuser account:
#        SELECT COUNT(*) FROM payments WHERE user_id = <abuser's user id>
#        AND status = 'created';
#    - Does this one account's activity measurably degrade /auth/me or
#      /config response times for other concurrent users vs. the SOAK
#      baseline?
#    - Any inconsistent prediction results/errors indicating a race between
#      a marks write and a concurrent read of those same marks?
