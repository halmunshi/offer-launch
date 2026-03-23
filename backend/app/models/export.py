import uuid
from uuid import uuid4
from sqlalchemy import Text, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import ExportType


class Export(Base):
    """
    Audit trail for every export action.
    One row per export — users can export the same funnel multiple times.
    No functional role in the generation pipeline — pure audit log.

    destination examples:
        github: https://github.com/username/my-fitness-funnel
        zip:    null (file served directly, no permanent destination)
        v2 cloudflare_pages: https://my-fitness-funnel.pages.dev
    """

    __tablename__ = "exports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    funnel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("funnels.id", ondelete="CASCADE"),
        nullable=False,
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
        comment="Denormalised for offer-level export queries"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    export_type: Mapped[ExportType] = mapped_column(
        SAEnum(ExportType, name="export_type", create_type=True),
        nullable=False,
    )
    destination: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="GitHub repo URL for github exports. null for zip."
    )
    exported_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_exports_funnel_id", "funnel_id"),
        Index("idx_exports_offer_id", "offer_id"),
        Index("idx_exports_user_id", "user_id"),
        Index("idx_exports_user_type", "user_id", "export_type"),
    )