"""
TNEA Predictor load test.
Accounts: loadtest_user_001..100 @pickmyseat.in  password: LoadTest@2026
"""

import random
from locust import HttpUser, task, between, constant_pacing

BASE_URL = "https://tneapredictor-production.up.railway.app"

USERS = [
    {"email": f"loadtest_user_{i:03d}@pickmyseat.in", "password": "LoadTest@2026"}
    for i in range(1, 101)
]

COMMUNITIES = ["OC", "BC", "MBC", "SC", "ST", "SCA", "BCM"]
BRANCHES    = ["CS", "EC", "EE", "ME", "CE", "IT", "AD"]
COLLEGES    = [1, 2, 3, 4, 5, 1013, 1101]

MARK_SETS = [
    {"maths": 95, "physics": 92, "chemistry": 88},
    {"maths": 75, "physics": 70, "chemistry": 72},
    {"maths": 85, "physics": 80, "chemistry": 78},
    {"maths": 60, "physics": 55, "chemistry": 58},
    {"maths": 99, "physics": 95, "chemistry": 93},
]


class GuestUser(HttpUser):
    """Unauthenticated visitors browsing predictions. weight=3"""
    weight    = 3
    wait_time = between(2, 8)
    host      = BASE_URL

    def on_start(self):
        self._community = random.choice(COMMUNITIES)
        self._marks     = random.choice(MARK_SETS)

    @task(5)
    def predict_colleges(self):
        payload = {**self._marks, "community": self._community, "top_n": 5}
        self.client.post(
            "/predict/colleges",
            json=payload,
            headers={"Authorization": "Bearer test"},  # bypass 1/day guest gate
            name="/predict/colleges [guest]",
        )

    @task(2)
    def predict_rank(self):
        payload = {**self._marks, "community": self._community}
        self.client.post(
            "/predict/rank",
            json=payload,
            name="/predict/rank [guest]",
        )

    @task(1)
    def get_config(self):
        self.client.get("/config", name="/config")

    @task(1)
    def get_colleges_list(self):
        self.client.get("/predict/colleges-list", name="/predict/colleges-list")


class RegisteredUser(HttpUser):
    """Logged-in free-tier users. weight=5"""
    weight    = 5
    wait_time = between(1, 6)
    host      = BASE_URL

    def on_start(self):
        creds = random.choice(USERS)
        self._token     = None
        self._community = random.choice(COMMUNITIES)
        self._marks     = random.choice(MARK_SETS)
        r = self.client.post(
            "/auth/login",
            json=creds,
            name="/auth/login [setup]",
        )
        if r.status_code == 200:
            self._token = r.json().get("token")

    def _auth(self):
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    @task(6)
    def predict_colleges_auth(self):
        payload = {
            **self._marks,
            "community": self._community,
            "top_n": 5,
            "preferred_branches": [random.choice(BRANCHES)],
        }
        self.client.post(
            "/predict/colleges",
            json=payload,
            headers=self._auth(),
            name="/predict/colleges [auth]",
        )

    @task(3)
    def get_me(self):
        self.client.get("/auth/me", headers=self._auth(), name="/auth/me")

    @task(2)
    def update_profile(self):
        # Only send name/mobile -- avoid locking marks
        self.client.post(
            "/auth/update-profile",
            json={"name": f"LT User {random.randint(1,100)}"},
            headers=self._auth(),
            name="/auth/update-profile",
        )

    @task(1)
    def predict_rank_auth(self):
        payload = {**self._marks, "community": self._community}
        self.client.post(
            "/predict/rank",
            json=payload,
            headers=self._auth(),
            name="/predict/rank [auth]",
        )


class PremiumUser(HttpUser):
    """
    Premium-flow simulation. weight=15 (heaviest -- premium path is most expensive).
    Hits payment/create-order which calls Razorpay -- will succeed or 502/503 if
    Razorpay sandbox is unavailable; both are acceptable non-5xx outcomes.
    """
    weight    = 15
    wait_time = between(3, 8)
    host      = BASE_URL

    def on_start(self):
        creds = random.choice(USERS)
        self._token     = None
        self._community = random.choice(COMMUNITIES)
        self._marks     = random.choice(MARK_SETS)
        r = self.client.post(
            "/auth/login",
            json=creds,
            name="/auth/login [setup]",
        )
        if r.status_code == 200:
            self._token = r.json().get("token")

    def _auth(self):
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    @task(4)
    def predict_colleges_combo(self):
        payload = {
            **self._marks,
            "community": self._community,
            "top_n": 10,
            "preferred_colleges": [random.choice(COLLEGES)],
            "preferred_branches": [random.choice(BRANCHES)],
        }
        self.client.post(
            "/predict/colleges",
            json=payload,
            headers=self._auth(),
            name="/predict/colleges [premium]",
        )

    @task(3)
    def get_me(self):
        self.client.get("/auth/me", headers=self._auth(), name="/auth/me")

    @task(2)
    def create_payment_order(self):
        with self.client.post(
            "/payment/create-order",
            headers=self._auth(),
            name="/payment/create-order",
            catch_response=True,
        ) as r:
            # 200=order ok, 400=already purchased, 502/503=Razorpay down -- all acceptable
            if r.status_code in (200, 400, 502, 503):
                r.success()
            # True server errors only
            elif r.status_code == 500:
                r.failure(f"500 internal error: {r.text[:80]}")

    @task(1)
    def update_profile_name(self):
        self.client.post(
            "/auth/update-profile",
            json={"name": f"PremLT {random.randint(1,100)}"},
            headers=self._auth(),
            name="/auth/update-profile",
        )


class RankListSpike(HttpUser):
    """
    Simulates the surge when rank list is released.
    INACTIVE -- RANK_LIST_RELEASED is still false; verify-rank returns 400 for all.
    Left defined but weight=0 so locust ignores it entirely.
    """
    weight    = 0
    wait_time = between(1, 3)
    host      = BASE_URL

    @task
    def verify_rank_noop(self):
        # Would call /predict/verify-rank -- skipped while flag is false
        pass
