import uuid
from uuid import uuid4
from sqlalchemy import Text, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import OfferStatus


class Offer(Base):
    """
    Top-level container for all agent outputs.
    Everything the agents produce belongs to an Offer.
    intake_data drives every agent via build_agent_context().
    Never mutate intake_data after creation.
    """

    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # v2 — agency plan. null = personal offer.
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    industry: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Denormalised from intake_data for fast filtering and agent context building"
    )
    status: Mapped[OfferStatus] = mapped_column(
        SAEnum(OfferStatus, name="offer_status", create_type=True),
        nullable=False,
        server_default="active",
    )
    intake_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Full 19-step wizard answers. Pydantic IntakeData schema. Never mutated after creation."
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_offers_user_id", "user_id"),
        Index("idx_offers_user_status", "user_id", "status"),
        Index("idx_offers_user_created", "user_id", "created_at"),
    )