from datetime import datetime
import uuid

from pydantic import Field

from app.models.enums import IntegrationProvider
from app.schemas.common import BaseSchema, UUIDSchema


class IntegrationCreate(BaseSchema):
    provider: IntegrationProvider
    access_token: str = Field(
        min_length=1,
        max_length=2000,
        description="Plaintext token — encrypted before DB write",
    )
    refresh_token: str | None = None
    account_id: str | None = None
    metadata: dict | None = None


class IntegrationResponse(UUIDSchema):
    user_id: uuid.UUID
    provider: IntegrationProvider
    account_id: str | None = None
    token_expires_at: datetime | None = None
    connected_at: datetime
    updated_at: datetime
