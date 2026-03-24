from datetime import datetime
import uuid

from app.models.enums import AgentType, JobStatus
from app.schemas.common import BaseSchema, UUIDSchema


class ProgressEvent(BaseSchema):
    stage: str
    message: str
    ts: str
    done: bool


class JobResponse(UUIDSchema):
    workflow_run_id: uuid.UUID
    offer_id: uuid.UUID
    user_id: uuid.UUID
    agent_type: AgentType
    status: JobStatus
    progress: list[ProgressEvent]
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
