---
name: predict-colleges-500-root-cause
description: The "Data unavailable" / "Failed to fetch" bug was one POST 500, not CORS
metadata:
  type: project
---

"Data unavailable" combo cards + browser "Failed to fetch"/TypeError on POST `/predict/colleges` traced to **one uncaught 500**, NOT CORS and NOT slowapi.

Proven facts (don't re-investigate):
- OPTIONS `/predict/colleges` returns **200** with correct CORS headers, including with slowapi **0.1.9** active. slowapi `_default_limits == []` — it never limits OPTIONS. The explicit catch-all OPTIONS handler is `backend/main.py`.
- A raw 500 from Starlette carries **no `Access-Control-Allow-Origin`**, so the browser reports it as "Failed to fetch" — which masquerades as a CORS/preflight failure. Fixed by a global `@app.exception_handler(Exception)` in `main.py` that reflects the origin on 500s.
- Local repro of `get_college_predictions_filtered(...)` returns 200; `cutoff_lookup_2026.csv` has 0 NaN. The bug only reproduces in prod for **logged-in users** (auth + DB path).
- The `db.commit()` persistence block in `backend/routes/predict.py` is wrapped in try/except + rollback — but that was NOT the cause.
- **CONFIRMED cause** (via debug_trace in the 500 response): `ValueError: Out of range float values are not JSON compliant`. `college_codes.csv` has 77 rows with a blank `district` → pandas float NaN. The rec inserted `info["district"]` raw, so a preferred college among those 77 put NaN in the response and crashed FastAPI's strict JSON encoder. Fixed by recursive `_json_safe()` wrapping all 3 return paths in `ml_service.py` (commit 19e9a62). Underlying data issue remains: 77 colleges still have no district in the CSV — fill them for a proper fix.

**How to apply:** when a fix premise contradicts local evidence, prove it locally before editing; reproduce, don't trust the stated root cause. Get the real traceback via [[deploy-and-railway-access]] before the next fix.
