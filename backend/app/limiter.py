from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter


def user_rate_limit_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return str(user_id)
    return "anonymous"


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    _ = request
    return JSONResponse(status_code=429, content={"detail": str(exc.detail)})


limiter = Limiter(key_func=user_rate_limit_key)
