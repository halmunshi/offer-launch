import uuid
from uuid import uuid4
from sqlalchemy import Text, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func, text
from app.database import Base
from app.models.enums import FunnelType, FunnelStatus


class Funnel(Base):
    """
    Metadata record for a generated funnel.
    Source files are stored in funnel_projects.files JSONB — not here.
    One offer can have multiple funnels (different types or themes).
    published_url and published_at are v2 (Cloudflare Pages hosting).
    """

    __tablename__ = "funnels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
    )
    # SET NULL on delete — funnel outlives its workflow run
    workflow_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
        comment="Which run generated this funnel. null = manually created (v2)."
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Denormalised for O(1) ownership checks"
    )
    name: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="e.g. 90-Day Body Transformation — VSL Funnel"
    )
    funnel_type: Mapped[FunnelType] = mapped_column(
        SAEnum(FunnelType, name="funnel_type", create_type=True),
        nullable=False,
        server_default="lead_generation",
    )
    style: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="high_converting",
        comment="Selected funnel style direction from setup wizard.",
    )
    integrations: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Normalized integration payload captured during funnel setup.",
    )
    theme: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="bold-dark",
        comment="Theme slug. bold-dark | clean-pro | warm-story | power-red | trust-blue | minimal"
    )
    status: Mapped[FunnelStatus] = mapped_column(
        SAEnum(FunnelStatus, name="funnel_status", create_type=True),
        nullable=False,
        server_default="draft",
    )
    # v2 — Cloudflare Pages hosted URL
    published_url: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="v2 — Cloudflare Pages live URL after deployment. null in MVP."
    )
    published_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="v2 — timestamp of last Cloudflare Pages deployment."
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_funnels_offer_id", "offer_id"),
        Index("idx_funnels_user_id", "user_id"),
        Index("idx_funnels_user_status", "user_id", "status"),
        Index("idx_funnels_workflow_run_id", "workflow_run_id"),
    )
