import uuid
from uuid import uuid4
from sqlalchemy import Text, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func, text
from app.database import Base
from app.models.enums import WorkflowType, WorkflowStatus


class WorkflowRun(Base):
    """
    One per user-triggered generation run.
    MVP: one run = one funnel generation (funnel_only).
    V2: one run = full GTM launch across all agents.

    active_agents drives job creation — only agents in this list
    get a corresponding job row spawned.

    langgraph_thread_id (v2): maps to LangGraph AsyncPostgresSaver
    thread_id for HIL resume. Connection string must use plain
    postgresql:// not postgresql+asyncpg://.
    """

    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
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
        comment="Denormalised for O(1) ownership checks"
    )
    workflow_type: Mapped[WorkflowType] = mapped_column(
        SAEnum(WorkflowType, name="workflow_type", create_type=True),
        nullable=False,
        server_default="funnel_only",
    )
    active_agents: Mapped[list] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY['copywriter','funnel_builder']"),
        comment="Which agent nodes run in this workflow. Drives job creation."
    )
    status: Mapped[WorkflowStatus] = mapped_column(
        SAEnum(WorkflowStatus, name="workflow_status", create_type=True),
        nullable=False,
        server_default="pending",
    )
    # v2 — HIL (human-in-the-loop) fields
    hil_state: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="v2 — payload shown to user at HIL pause point"
    )
    hil_checkpoint: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="v2 — which LangGraph node is paused e.g. copywriter"
    )
    langgraph_thread_id: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_workflow_runs_offer_id", "offer_id"),
        Index("idx_workflow_runs_user_id", "user_id"),
        Index("idx_workflow_runs_user_status", "user_id", "status"),
    )