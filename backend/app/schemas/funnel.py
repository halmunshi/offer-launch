from datetime import datetime
import uuid

from app.models.enums import FunnelStatus, FunnelType, StepStatus, StepType
from app.schemas.common import TimestampSchema, UUIDSchema


class FunnelStepResponse(UUIDSchema):
    funnel_id: uuid.UUID
    step_order: int
    step_type: StepType
    custom_step_name: str | None = None
    status: StepStatus
    slug: str
    created_at: datetime
    updated_at: datetime


class FunnelResponse(UUIDSchema, TimestampSchema):
    offer_id: uuid.UUID
    workflow_run_id: uuid.UUID | None = None
    user_id: uuid.UUID
    name: str
    funnel_type: FunnelType
    theme: str
    status: FunnelStatus
    published_url: str | None = None
    published_at: datetime | None = None
    steps: list[FunnelStepResponse] = []
