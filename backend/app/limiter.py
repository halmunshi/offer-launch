from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def user_rate_limit_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return str(user_id)
    return get_remote_address(request)


limiter = Limiter(key_func=user_rate_limit_key)
