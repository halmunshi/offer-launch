import uuid

from pydantic import Field, model_validator

from app.models.enums import OfferStatus
from app.schemas.common import BaseSchema, TimestampSchema, UUIDSchema


class IntakeData(BaseSchema):
    brand_name: str = Field(max_length=100)
    offer_name: str = Field(max_length=100)
    offer_one_liner: str = Field(max_length=300)
    price_point: str = Field(max_length=50)
    whats_included: str = Field(max_length=3000)
    transformation: str = Field(max_length=2000)
    ideal_client: str = Field(max_length=2000)
    pain_point: str = Field(max_length=2000)

class OfferCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=100, description="Offer display name")
    intake_data: IntakeData


class OfferUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100, description="New offer display name")
    industry: str | None = Field(default=None, min_length=1, max_length=100, description="Offer industry")
    intake_data: IntakeData | None = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "OfferUpdate":
        if self.name is None and self.industry is None and self.intake_data is None:
            raise ValueError("At least one field must be provided for update")
        return self


class OfferResponse(UUIDSchema, TimestampSchema):
    user_id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    name: str
    industry: str
    status: OfferStatus
    intake_data: dict
