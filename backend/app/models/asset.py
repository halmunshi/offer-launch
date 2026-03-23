import uuid
from uuid import uuid4
from sqlalchemy import Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func
from app.database import Base


class Asset(Base):
    """
    v2 only — not used in MVP.
    Generated binary assets: images, videos, audio files.
    R2 stores the binary. This table stores metadata and the R2 pointer.

    r2_key pattern: assets/{offer_id}/{asset_type}/{uuid}.{ext}
    public_url: constructed from r2_key at upload time using R2_PUBLIC_URL setting.
    """

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_type: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="image | video | audio"
    )
    r2_key: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="R2 object key. Pattern: assets/{offer_id}/{asset_type}/{uuid}.{ext}"
    )
    public_url: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="R2 public URL constructed from r2_key at upload time."
    )
    provider: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Which service generated this. nano-banana | dalle | kling | runwayml | elevenlabs"
    )
    generation_params: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Prompt + params used for generation. Enables regeneration with same settings."
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_assets_workflow_run_id", "workflow_run_id"),
        Index("idx_assets_offer_id", "offer_id"),
        Index("idx_assets_user_id", "user_id"),
        Index("idx_assets_offer_type", "offer_id", "asset_type"),
    )