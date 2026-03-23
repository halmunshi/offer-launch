import uuid
from uuid import uuid4
from sqlalchemy import Integer, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import AgentType


class AgentOutput(Base):
    """
    One row per agent per workflow run.
    Stores full structured JSON output from each agent.
    Downstream agents read upstream outputs via workflow_run_id.

    Read pattern (copywriter reading analyst output):
        SELECT output_data FROM agent_outputs
        WHERE workflow_run_id = $1 AND agent_type = 'analyst'
        ORDER BY version DESC LIMIT 1

    output_data schema per agent_type:
        analyst:    { icp, hook_angles, objections, tone_guidance, competitor_analysis }
        copywriter: { pages: { presell: {...}, vsl: {...}, order: {...}, ... } }
        assembler:  { file_paths: ["/src/pages/VSL.tsx", ...] }
    """

    __tablename__ = "agent_outputs"

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
    agent_type: Mapped[AgentType] = mapped_column(
        SAEnum(AgentType, name="agent_type", create_type=False),
        # create_type=False — enum already created by jobs table
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1",
        comment="Increments when this agent is re-run for the same workflow_run"
    )
    output_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_agent_outputs_run_id", "workflow_run_id"),
        Index("idx_agent_outputs_offer_id", "offer_id"),
        Index(
            "idx_agent_outputs_run_agent_version",
            "workflow_run_id", "agent_type", "version"
        ),
        Index("idx_agent_outputs_offer_agent", "offer_id", "agent_type"),
    )