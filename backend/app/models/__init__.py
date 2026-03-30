# Import all models here so Alembic can discover them via Base.metadata.
# Order matters — tables with foreign keys must come after their dependencies.

from app.models.enums import (  # noqa: F401
    UserPlan,
    OfferStatus,
    WorkflowType,
    WorkflowStatus,
    AgentType,
    JobStatus,
    FunnelType,
    FunnelStatus,
    ExportType,
    IntegrationProvider,
)

from app.models.user import User  # noqa: F401
from app.models.offer import Offer  # noqa: F401
from app.models.workspace import Workspace  # noqa: F401
from app.models.workspace_member import WorkspaceMember  # noqa: F401
from app.models.workflow_run import WorkflowRun  # noqa: F401
from app.models.job import Job  # noqa: F401
from app.models.agent_output import AgentOutput  # noqa: F401
from app.models.funnel import Funnel  # noqa: F401
from app.models.funnel_project import FunnelProject  # noqa: F401
from app.models.export import Export  # noqa: F401
from app.models.integration import Integration  # noqa: F401
from app.models.asset import Asset  # noqa: F401
from app.models.chat_message import ChatMessage  # noqa: F401
