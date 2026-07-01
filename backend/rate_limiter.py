from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_limit_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return f"user:{auth.split(' ')[1][:20]}"
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key)
