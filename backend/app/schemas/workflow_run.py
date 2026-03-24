from datetime import datetime
import uuid

from pydantic import Field

from app.models.enums import FunnelType, WorkflowStatus, WorkflowType
from app.schemas.common import BaseSchema, UUIDSchema


class WorkflowRunCreate(BaseSchema):
    offer_id: uuid.UUID
    workflow_type: WorkflowType = WorkflowType.funnel_only
    funnel_type: FunnelType = FunnelType.vsl
    theme: str = Field(default="bold-dark", max_length=50)


class WorkflowRunResponse(UUIDSchema):
    offer_id: uuid.UUID
    user_id: uuid.UUID
    workflow_type: WorkflowType
    active_agents: list[str]
    status: WorkflowStatus
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
