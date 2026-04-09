from datetime import datetime
import uuid

from pydantic import Field

from app.models.enums import FunnelType, WorkflowStatus, WorkflowType
from app.schemas.common import BaseSchema, UUIDSchema


class FunnelIntegrations(BaseSchema):
    lead_magnet_type: str | None = None
    lead_magnet_description: str | None = None
    lead_magnet_ready: bool | None = None

    has_vsl: bool | None = None
    vsl_embed: str | None = None
    calendar_provider: str | None = None
    calendar_embed: str | None = None

    payment_processor: str | None = None
    payment_embed: str | None = None
    selected_pages: list[str] | None = None


class WorkflowRunCreate(BaseSchema):
    offer_id: uuid.UUID = Field(description="Offer UUID to generate a funnel for")
    funnel_name: str = Field(min_length=1, max_length=255)
    funnel_type: FunnelType
    funnel_style: str = Field(min_length=1, max_length=100)
    integrations: FunnelIntegrations = Field(default_factory=FunnelIntegrations)


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
