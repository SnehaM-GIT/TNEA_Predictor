---
name: deploy-and-railway-access
description: How TNEA_Predictor deploys and the hard limit that Claude cannot read Railway logs
metadata:
  type: project
---

Deploy = `git push origin main` (remote: github.com/SnehaM-GIT/TNEA_Predictor). Backend auto-deploys to **Railway**; frontend to **Vercel** at `https://pickymyseat.vercel.app` (this exact origin is in `backend/main.py` ALLOWED_ORIGINS).

**Hard limit:** this Claude session has **no access to the Railway dashboard or logs** — no Railway MCP, no creds. Do NOT promise to "check Railway logs." To get a production traceback, either ask the user to paste it, or make the error self-report via the HTTP response body (temporary `debug_error`/`debug_trace` in the global exception handler in `main.py`) and read it from the browser Network tab.

**Why:** user repeatedly asked me to fetch Railway logs across many turns; I cannot. The self-reporting-response approach unblocked it. See [[predict-colleges-500-root-cause]].
