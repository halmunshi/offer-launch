from datetime import datetime
import uuid

from app.models.enums import ExportType
from app.schemas.common import UUIDSchema


class ExportResponse(UUIDSchema):
    funnel_id: uuid.UUID
    offer_id: uuid.UUID
    user_id: uuid.UUID
    export_type: ExportType
    destination: str | None = None
    exported_at: datetime
