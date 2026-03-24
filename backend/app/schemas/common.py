from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UUIDSchema(BaseSchema):
    id: uuid.UUID


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime
