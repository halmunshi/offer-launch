from datetime import datetime
import uuid

from app.models.enums import FunnelStatus, FunnelType
from app.schemas.common import TimestampSchema, UUIDSchema


class FunnelResponse(UUIDSchema, TimestampSchema):
    offer_id: uuid.UUID
    workflow_run_id: uuid.UUID | None = None
    user_id: uuid.UUID
    name: str
    funnel_type: FunnelType
    style: str
    integrations: dict
    theme: str
    status: FunnelStatus
    published_url: str | None = None
    published_at: datetime | None = None
