import uuid
from uuid import uuid4
from sqlalchemy import Text, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import IntegrationProvider


class Integration(Base):
    """
    Encrypted OAuth tokens for all external platform connections.
    Separate table so tokens can be encrypted independently from other data.

    MVP providers:
        github — OAuth token scoped to repo permission. Used for project export.
        ghl    — API key / OAuth token. Used for headless CRM form proxy.

    GHL headless proxy pattern:
        Generated funnel forms POST to FastAPI /ghl/contact (public, rate-limited).
        Proxy looks up funnel owner, fetches this row, decrypts access_token_enc,
        forwards request to GHL API server-side.
        GHL API key is NEVER exposed in the browser bundle.

    IMPORTANT: metadata_ column maps to 'metadata' in the DB.
    'metadata' is a reserved attribute name in SQLAlchemy — must use metadata_ in Python.
    """

    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[IntegrationProvider] = mapped_column(
        SAEnum(IntegrationProvider, name="integration_provider", create_type=True),
        nullable=False,
    )
    access_token_enc: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Fernet-encrypted. Never store plaintext. Decrypt only server-side."
    )
    refresh_token_enc: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Fernet-encrypted refresh token. Required for GHL, Meta Ads (tokens expire)."
    )
    account_id: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Provider account ID. GHL: location_id. Meta: ad_account_id. GitHub: username."
    )
    # NOTE: 'metadata' is reserved by SQLAlchemy — column name in DB is 'metadata'
    # but Python attribute must be metadata_
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB, nullable=True,
        comment="Provider-specific extras. GHL: {pipeline_id, tag}. Meta: {pixel_id}. GitHub: {default_branch}."
    )
    token_expires_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="null = token does not expire (GitHub). Set for GHL, Meta Ads."
    )
    connected_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_integrations_user_id", "user_id"),
        Index(
            "idx_integrations_user_provider_unique",
            "user_id", "provider",
            unique=True,
        ),
    )
