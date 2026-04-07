from app.models.enums import UserPlan
from app.schemas.common import BaseSchema, TimestampSchema, UUIDSchema


class UserResponse(UUIDSchema, TimestampSchema):
    clerk_id: str
    email: str
    full_name: str | None = None
    business_type: str | None = None
    industry: str | None = None
    avatar_url: str | None = None
    plan: UserPlan


class UsageResponse(BaseSchema):
    funnel_count: int
    offer_count: int
    runs_this_month: int
