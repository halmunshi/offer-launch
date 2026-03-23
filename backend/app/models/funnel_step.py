import uuid
from uuid import uuid4
from sqlalchemy import Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import StepType, StepStatus


class FunnelStep(Base):
    """
    One row per page within a funnel.
    Metadata and status tracking only — no source file storage here.
    Source files live in funnel_projects.files JSONB.

    The React component for this step lives at:
        /src/pages/{step_type}.tsx
    inside the funnel_projects.files object.

    custom_step_name is v2 only — when step_type = custom, the assembler
    prompts the funnel builder agent with the user's description.
    """

    __tablename__ = "funnel_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    funnel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("funnels.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="1-based. Determines page sequence in the funnel."
    )
    step_type: Mapped[StepType] = mapped_column(
        SAEnum(StepType, name="step_type", create_type=True),
        nullable=False,
    )
    custom_step_name: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="v2 — only populated when step_type = custom. User-defined label."
    )
    status: Mapped[StepStatus] = mapped_column(
        SAEnum(StepStatus, name="step_status", create_type=True),
        nullable=False,
        server_default="pending",
        comment="Updated independently per step as assembler generates each page component."
    )
    slug: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="URL-safe route slug. e.g. vsl-page → /vsl-page in React Router."
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_funnel_steps_funnel_id", "funnel_id"),
        Index("idx_funnel_steps_order", "funnel_id", "step_order"),
        Index(
            "idx_funnel_steps_type_unique",
            "funnel_id", "step_type",
            unique=True,
        ),
    )
