from typing import Literal
from datetime import datetime
import uuid

from pydantic import Field

from app.models.enums import OfferStatus
from app.schemas.common import BaseSchema, TimestampSchema, UUIDSchema


class IntakeData(BaseSchema):
    role: str = Field(max_length=50)
    industry: str = Field(max_length=100)
    brand_name: str = Field(max_length=100)
    credibility: str = Field(max_length=2000)
    offer_name: str = Field(max_length=100)
    offer_one_liner: str = Field(max_length=300)
    price_point: str = Field(max_length=50)
    whats_included: str = Field(max_length=3000)
    unique_mechanism: str = Field(max_length=2000)
    transformation: str = Field(max_length=2000)
    ideal_client: str = Field(max_length=2000)
    age_ranges: list[str] = Field(default=[], max_length=5)
    pain_point: str = Field(max_length=2000)
    awareness_level: str = Field(max_length=50)
    has_testimonials: bool = False
    testimonials: list[str] = Field(default=[], max_length=3)
    assets: list[str] = Field(default=[])
    has_guarantee: bool = False
    guarantee_type: str = Field(default="", max_length=100)
    guarantee_duration: str = Field(default="", max_length=50)
    copy_style: str = Field(max_length=50)
    funnel_type: Literal["vsl", "lead_magnet"]
    theme: str = Field(max_length=50)


class OfferCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    intake_data: IntakeData


class OfferResponse(UUIDSchema, TimestampSchema):
    user_id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    name: str
    industry: str
    status: OfferStatus
    intake_data: dict
