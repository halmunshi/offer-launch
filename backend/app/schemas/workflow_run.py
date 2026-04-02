from datetime import datetime
import uuid

from app.models.enums import WorkflowStatus, WorkflowType
from app.schemas.common import BaseSchema, UUIDSchema


class WorkflowRunCreate(BaseSchema):
    offer_id: uuid.UUID


class WorkflowRunResponse(UUIDSchema):
    offer_id: uuid.UUID
    user_id: uuid.UUID
    funnel_id: uuid.UUID
    job_ids: list[uuid.UUID]
    workflow_type: WorkflowType
    active_agents: list[str]
    status: WorkflowStatus
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
