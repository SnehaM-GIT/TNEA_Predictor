import os
import jwt
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_limit_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ")[1]
        try:
            # NOTE: token[:20] used to be the key here. That slice is just the
            # fixed HS256 JWT header ("eyJhbGciOiJIUzI1NiIs...") which is
            # IDENTICAL for every token this app issues — every logged-in user
            # was sharing one global rate-limit bucket per endpoint. Decode the
            # payload and key on the actual user_id instead.
            payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
            user_id = payload.get("user_id")
            if user_id is not None:
                return f"user:{user_id}"
        except jwt.InvalidTokenError:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key)
