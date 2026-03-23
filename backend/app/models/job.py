import uuid
from uuid import uuid4
from sqlalchemy import Text, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func, text
from app.database import Base
from app.models.enums import AgentType, JobStatus


class Job(Base):
    """
    One per agent per workflow run.
    MVP: 1 job per run covering the full pipeline (analyst→copywriter→assembler).
    V2: N jobs per run, one per active_agent, running in dependency waves.

    progress is the live SSE feed for the builder chat panel.
    Append-only — never overwrite the array, only append:
      UPDATE jobs SET progress = progress || $new_event::jsonb WHERE id = $id

    Each progress event shape:
      { "stage": str, "message": str, "ts": ISO8601, "done": bool }
    """

    __tablename__ = "jobs"

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
        comment="Denormalised for direct offer-level job queries"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Denormalised for O(1) ownership checks"
    )
    agent_type: Mapped[AgentType] = mapped_column(
        SAEnum(AgentType, name="agent_type", create_type=True),
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status", create_type=True),
        nullable=False,
        server_default="pending",
    )
    progress: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        comment="Append-only array of {stage, message, ts, done}. Never overwrite."
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
        Index("idx_jobs_workflow_run_id", "workflow_run_id"),
        Index("idx_jobs_user_id", "user_id"),
        Index("idx_jobs_user_status", "user_id", "status"),
        Index(
            "idx_jobs_run_agent_unique",
            "workflow_run_id", "agent_type",
            unique=True,
        ),
    )
