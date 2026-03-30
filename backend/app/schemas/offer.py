from typing import Literal
from datetime import datetime
import uuid

from pydantic import Field, model_validator

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
    selected_pages: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_selected_pages(self) -> "IntakeData":
        allowed_pages = {
            "presell",
            "vsl",
            "order",
            "thank_you",
            "upsell",
            "downsell",
            "opt_in",
            "bridge",
            "offer",
        }
        minimum_pages_by_funnel = {
            "vsl": ["vsl", "order", "thank_you"],
            "lead_magnet": ["opt_in", "thank_you"],
        }

        cleaned: list[str] = []
        seen: set[str] = set()
        for page in self.selected_pages:
            normalized = str(page).strip().lower().replace("-", "_").replace(" ", "_")
            if not normalized:
                continue
            if normalized not in allowed_pages:
                raise ValueError(f"Unsupported page in selected_pages: {normalized}")
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(normalized)

        required = minimum_pages_by_funnel[self.funnel_type]

        if not cleaned:
            cleaned = list(required)

        missing_required = [page for page in required if page not in cleaned]
        if missing_required:
            raise ValueError(
                "selected_pages is missing required pages for "
                f"{self.funnel_type}: {', '.join(missing_required)}"
            )

        self.selected_pages = cleaned
        return self


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
