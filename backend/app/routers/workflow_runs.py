import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.limiter import limiter
from app.middleware.clerk_auth import get_current_user
from app.models.enums import AgentType, FunnelStatus, JobStatus, StepStatus, StepType, WorkflowStatus
from app.models.funnel import Funnel
from app.models.funnel_project import FunnelProject
from app.models.funnel_step import FunnelStep
from app.models.job import Job
from app.models.offer import Offer
from app.models.user import User
from app.models.workflow_run import WorkflowRun
from app.schemas.workflow_run import WorkflowRunCreate, WorkflowRunResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow-runs", tags=["workflow-runs"])


def _steps_for_funnel_type(funnel_type: str) -> list[StepType]:
    if funnel_type == "lead_magnet":
        return [StepType.optin, StepType.thankyou, StepType.bridge, StepType.offer]
    return [
        StepType.presell,
        StepType.vsl,
        StepType.order,
        StepType.upsell,
        StepType.downsell,
        StepType.thankyou,
    ]


@router.post("", response_model=WorkflowRunResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour;10/day")
async def create_workflow_run(
    request: Request,
    payload: WorkflowRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowRun:
    _ = request

    try:
        offer_result = await db.execute(
            select(Offer).where(
                Offer.id == payload.offer_id,
                Offer.user_id == current_user.id,
            )
        )
        offer = offer_result.scalar_one_or_none()
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")

        workflow_run = WorkflowRun(
            offer_id=offer.id,
            user_id=current_user.id,
            workflow_type=payload.workflow_type,
            active_agents=["analyst", "copywriter", "assembler"],
            status=WorkflowStatus.pending,
        )
        db.add(workflow_run)
        await db.flush()

        funnel = Funnel(
            offer_id=offer.id,
            workflow_run_id=workflow_run.id,
            user_id=current_user.id,
            name=f"{offer.name} — {payload.funnel_type.value} Funnel",
            funnel_type=payload.funnel_type,
            theme=payload.theme,
            status=FunnelStatus.draft,
        )
        db.add(funnel)
        await db.flush()

        funnel_project = FunnelProject(
            funnel_id=funnel.id,
            user_id=current_user.id,
            files={},
            boilerplate_version="1.0.0",
        )
        db.add(funnel_project)

        steps = _steps_for_funnel_type(payload.funnel_type.value)
        for index, step_type in enumerate(steps, start=1):
            db.add(
                FunnelStep(
                    funnel_id=funnel.id,
                    step_order=index,
                    step_type=step_type,
                    status=StepStatus.pending,
                    slug=step_type.value.replace("_", "-"),
                )
            )

        job = Job(
            workflow_run_id=workflow_run.id,
            offer_id=offer.id,
            user_id=current_user.id,
            agent_type=AgentType.analyst,
            status=JobStatus.pending,
            progress=[],
        )
        db.add(job)
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise

    try:
        from app.workers.celery_app import celery_app

        celery_app.send_task("generate_funnel_task", args=[str(workflow_run.id)])
    except Exception:
        logger.exception("Failed to dispatch generate_funnel_task for workflow run %s", workflow_run.id)

    return workflow_run


@router.get("/{workflow_run_id}", response_model=WorkflowRunResponse)
async def get_workflow_run(
    workflow_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowRun:
    result = await db.execute(
        select(WorkflowRun).where(
            WorkflowRun.id == workflow_run_id,
            WorkflowRun.user_id == current_user.id,
        )
    )
    workflow_run = result.scalar_one_or_none()
    if workflow_run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    return workflow_run
