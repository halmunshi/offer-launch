from datetime import datetime

from app.models.enums import UserPlan
from app.schemas.common import TimestampSchema, UUIDSchema


class UserResponse(UUIDSchema, TimestampSchema):
    clerk_id: str
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    plan: UserPlan
    plan_expires_at: datetime | None = None
    stripe_customer_id: str | None = None
    onboarding_completed: bool
