import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from rate_limiter import limiter
from routes import predict, auth, payment

app = FastAPI(title="PickMySeat API")


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1_000_000:  # 1 MB
            return Response("Payload too large", status_code=413)
        return await call_next(request)

ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1",
    "null",
    "https://pickymyseat.vercel.app",
    "https://pickmyseat.in",
    "https://www.pickmyseat.in",
]

app.add_middleware(MaxBodySizeMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Uncaught exceptions otherwise produce a raw 500 with no CORS header, which
# the browser surfaces as "Failed to fetch" instead of the real error. Reflect
# the origin so the frontend can actually read the 500 and we can debug it.
@app.exception_handler(Exception)
async def cors_aware_500(request: Request, exc: Exception):
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in ALLOWED_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    import traceback
    print(f"Unhandled error on {request.method} {request.url.path}: {exc!r}\n"
          f"{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )

app.include_router(auth.router, prefix="/auth")
app.include_router(predict.router, prefix="/predict")
app.include_router(payment.router, prefix="/payment")

@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.on_event("startup")
async def startup_checks():
    import anyio
    anyio.to_thread.current_default_thread_limiter().total_tokens = 20

    missing = []
    for var in ["RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "SECRET_KEY", "DATABASE_URL",
                "RESEND_API_KEY"]:
        if not os.getenv(var):
            missing.append(var)
    if missing:
        print(f"⚠️  WARNING: Missing environment variables: {', '.join(missing)}")
    else:
        print("✅ All required environment variables are set.")
    print(f"📧 Email: RESEND_API_KEY={'SET' if os.getenv('RESEND_API_KEY') else 'MISSING'} "
          f"reset_base={os.getenv('RESET_BASE_URL', 'https://pickmyseat.in')}")

@app.get("/")
def root():
    return {"status": "PickMySeat API is running"}

@app.get("/config")
def get_config():
    return {
        "rank_list_released": os.getenv("RANK_LIST_RELEASED", "false").lower() == "true"
    }

# ============================================================
# VISITOR COUNT — IP-based unique visitor tracking
# Starts at 300, increments only for new IPs (resets on restart)
# ============================================================
_visitor_ips: set = set()
_visitor_count: int = 300

@app.get("/visitor-count")
async def visitor_count(request: Request):
    global _visitor_count, _visitor_ips
    # Respect X-Forwarded-For header from proxies (Railway, Vercel, etc.)
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    if ip not in _visitor_ips:
        _visitor_ips.add(ip)
        _visitor_count += 1
    return {"count": _visitor_count}

@app.get("/health")
def health():
    return {"status": "ok"}