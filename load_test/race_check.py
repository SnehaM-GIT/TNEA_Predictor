"""
Targeted manual check for Fix 3: does /predict/colleges ever read a
"dirty"/stale marks value affected by concurrent /auth/update-profile calls?

Uses a non-premium loadtest account (marks not locked, so update-profile
writes actually succeed) and runs two threads for 60s:
  A: hammers /auth/update-profile with random marks (logged).
  B: hammers /predict/colleges with a FIXED, known marks payload (95/90/90)
     and logs the predicted_rank / rank range returned each time.

Since /predict/colleges computes its prediction from the request body's own
maths/physics/chemistry (not a DB read of the user row), thread B's fixed
input should produce the exact same predicted_rank on every call, regardless
of what thread A is concurrently writing. Any variance for the same fixed
input would indicate real shared-state leakage.
"""
import threading
import time
import requests

BASE = "https://tneapredictor-production.up.railway.app"
ACCOUNT = {"email": "loadtest_user_050@pickmyseat.in", "password": "LoadTest@2026"}
DURATION = 60

r = requests.post(f"{BASE}/auth/login", json=ACCOUNT, timeout=15)
token = r.json().get("token", "")
headers = {"Authorization": f"Bearer {token}"}
print("login status:", r.status_code, "token len:", len(token))

profile_log = []
predict_log = []
stop_at = time.time() + DURATION

FIXED_MARKS = {"maths": 95, "physics": 90, "chemistry": 90, "community": "OC", "top_n": 5}

import random


def writer():
    while time.time() < stop_at:
        m = {
            "maths": random.randint(50, 100),
            "physics": random.randint(50, 100),
            "chemistry": random.randint(50, 100),
        }
        t0 = time.time()
        try:
            r = requests.post(f"{BASE}/auth/update-profile", json=m, headers=headers, timeout=10)
            profile_log.append((t0, m, r.status_code))
        except Exception as e:
            profile_log.append((t0, m, f"ERR:{e}"))


def reader():
    while time.time() < stop_at:
        t0 = time.time()
        try:
            r = requests.post(f"{BASE}/predict/colleges", json=FIXED_MARKS, headers=headers, timeout=10)
            if r.status_code == 200:
                body = r.json()
                predict_log.append((t0, r.status_code, body.get("student_rank"), body.get("student_rank_range")))
            else:
                predict_log.append((t0, r.status_code, None, None))
        except Exception as e:
            predict_log.append((t0, f"ERR:{e}", None, None))


tw = threading.Thread(target=writer)
tr = threading.Thread(target=reader)
tw.start()
tr.start()
tw.join()
tr.join()

print(f"\nprofile writes: {len(profile_log)}, predict reads: {len(predict_log)}")

status_counts = {}
for _, _, s in profile_log:
    status_counts[s] = status_counts.get(s, 0) + 1
print("update-profile status counts:", status_counts)

ranks = [(s, rank, rng) for _, s, rank, rng in predict_log]
status_counts2 = {}
distinct_ranks = set()
for s, rank, rng in ranks:
    status_counts2[s] = status_counts2.get(s, 0) + 1
    if s == 200:
        distinct_ranks.add((rank, tuple(rng) if rng else None))

print("predict/colleges status counts:", status_counts2)
print("distinct (student_rank, range) values seen for the FIXED input:", distinct_ranks)
if len(distinct_ranks) <= 1:
    print("RESULT: no variance for fixed input -> no dirty-read race observed")
else:
    print("RESULT: VARIANCE DETECTED for fixed input -> possible shared-state race")
