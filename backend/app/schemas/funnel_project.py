from datetime import datetime
import uuid

from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema, UUIDSchema


class FilePatchRequest(BaseSchema):
    path: str = Field(
        min_length=1,
        max_length=500,
        description="File path e.g. /src/pages/VSL.tsx",
    )
    content: str = Field(
        max_length=500_000,
        description="Full file content. Max 500KB per file.",
    )


class FunnelProjectResponse(UUIDSchema, TimestampSchema):
    funnel_id: uuid.UUID
    user_id: uuid.UUID
    files: dict
    session_summary: str | None = None
    boilerplate_version: str


class FilePatchResponse(BaseSchema):
    path: str
    updated_at: datetime
