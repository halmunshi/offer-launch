import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.limiter import limiter
from app.middleware.clerk_auth import get_current_user
from app.models.enums import AgentType, FunnelStatus, FunnelType, JobStatus, UserPlan, WorkflowStatus, WorkflowType
from app.models.funnel import Funnel
from app.models.job import Job
from app.models.offer import Offer
from app.models.user import User
from app.models.workflow_run import WorkflowRun
from app.schemas.workflow_run import WorkflowRunCreate, WorkflowRunResponse

logger = logging.getLogger(__name__)
STALE_PENDING_RUN_TIMEOUT_MINUTES = 30

router = APIRouter(prefix="/workflow-runs", tags=["workflow-runs"])


@router.post("", response_model=WorkflowRunResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour;10/day")
async def create_workflow_run(
    request: Request,
    payload: WorkflowRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowRunResponse:
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

        if current_user.plan == UserPlan.free:
            funnel_count_result = await db.execute(
                select(func.count(Funnel.id)).where(Funnel.user_id == current_user.id)
            )
            funnel_count = funnel_count_result.scalar_one()
            if funnel_count >= 1:
                raise HTTPException(
                    status_code=403,
                    detail="Free plan supports one funnel. Upgrade to create more.",
                )

        stale_cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=STALE_PENDING_RUN_TIMEOUT_MINUTES
        )
        stale_pending_result = await db.execute(
            select(WorkflowRun.id).where(
                WorkflowRun.user_id == current_user.id,
                WorkflowRun.status == WorkflowStatus.pending,
                WorkflowRun.created_at < stale_cutoff,
            )
        )
        stale_pending_ids = list(stale_pending_result.scalars().all())

        if stale_pending_ids:
            stale_error = (
                "Auto-expired stale pending run after "
                f"{STALE_PENDING_RUN_TIMEOUT_MINUTES} minutes without start"
            )
            await db.execute(
                update(WorkflowRun)
                .where(WorkflowRun.id.in_(stale_pending_ids))
                .values(
                    status=WorkflowStatus.error,
                    error=stale_error,
                    updated_at=func.now(),
                )
            )
            await db.execute(
                update(Job)
                .where(Job.workflow_run_id.in_(stale_pending_ids))
                .values(
                    status=JobStatus.error,
                    error=stale_error,
                    updated_at=func.now(),
                )
            )
            await db.execute(
                update(Funnel)
                .where(Funnel.workflow_run_id.in_(stale_pending_ids))
                .values(
                    status=FunnelStatus.error,
                    updated_at=func.now(),
                )
            )
            await db.commit()

        active_run_result = await db.execute(
            select(WorkflowRun.id)
            .where(
                WorkflowRun.user_id == current_user.id,
                WorkflowRun.status.in_([WorkflowStatus.pending, WorkflowStatus.running]),
            )
            .limit(1)
        )
        active_workflow_run_id = active_run_result.scalar_one_or_none()
        if active_workflow_run_id is not None:
            raise HTTPException(
                status_code=409,
                detail="A funnel generation is already in progress.",
            )

        intake_data = offer.intake_data if isinstance(offer.intake_data, dict) else {}
        funnel_type_value = str(intake_data.get("funnel_type") or FunnelType.vsl.value)
        try:
            funnel_type = FunnelType(funnel_type_value)
        except ValueError:
            funnel_type = FunnelType.vsl

        theme = str(intake_data.get("theme") or intake_data.get("theme_direction") or "bold-dark")

        workflow_run = WorkflowRun(
            offer_id=offer.id,
            user_id=current_user.id,
            workflow_type=WorkflowType.funnel_only,
            active_agents=["copywriter", "funnel_builder"],
            status=WorkflowStatus.pending,
        )
        db.add(workflow_run)
        await db.flush()

        funnel = Funnel(
            offer_id=offer.id,
            workflow_run_id=workflow_run.id,
            user_id=current_user.id,
            name=f"{offer.name} - {funnel_type.value} Funnel",
            funnel_type=funnel_type,
            theme=theme,
            status=FunnelStatus.generating,
        )
        db.add(funnel)
        await db.flush()

        copywriter_job = Job(
            workflow_run_id=workflow_run.id,
            offer_id=offer.id,
            user_id=current_user.id,
            agent_type=AgentType.copywriter,
            status=JobStatus.pending,
            progress=[],
        )
        funnel_builder_job = Job(
            workflow_run_id=workflow_run.id,
            offer_id=offer.id,
            user_id=current_user.id,
            agent_type=AgentType.funnel_builder,
            status=JobStatus.pending,
            progress=[],
        )
        db.add(copywriter_job)
        db.add(funnel_builder_job)
        await db.commit()
        await db.refresh(workflow_run)
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise

    try:
        from app.workers.tasks import generate_funnel_task

        generate_funnel_task.apply_async(args=[str(workflow_run.id)], ignore_result=True)
    except Exception as exc:
        logger.exception("Failed to dispatch generate_funnel_task for workflow run %s", workflow_run.id)
        workflow_run.status = WorkflowStatus.error
        workflow_run.error = "Failed to dispatch workflow run"
        funnel.status = FunnelStatus.error
        copywriter_job.status = JobStatus.error
        copywriter_job.error = "Failed to dispatch workflow run"
        funnel_builder_job.status = JobStatus.error
        funnel_builder_job.error = "Failed to dispatch workflow run"
        await db.commit()
        raise HTTPException(status_code=500, detail="Failed to dispatch workflow run") from exc

    return WorkflowRunResponse(
        id=workflow_run.id,
        offer_id=workflow_run.offer_id,
        user_id=workflow_run.user_id,
        funnel_id=funnel.id,
        job_ids=[copywriter_job.id, funnel_builder_job.id],
        workflow_type=workflow_run.workflow_type,
        active_agents=workflow_run.active_agents,
        status=workflow_run.status,
        error=workflow_run.error,
        started_at=workflow_run.started_at,
        completed_at=workflow_run.completed_at,
        created_at=workflow_run.created_at,
        updated_at=workflow_run.updated_at,
    )


@router.get("/{workflow_run_id}", response_model=WorkflowRunResponse)
async def get_workflow_run(
    workflow_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowRunResponse:
    result = await db.execute(
        select(WorkflowRun).where(
            WorkflowRun.id == workflow_run_id,
            WorkflowRun.user_id == current_user.id,
        )
    )
    workflow_run = result.scalar_one_or_none()
    if workflow_run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    funnel_result = await db.execute(
        select(Funnel).where(
            Funnel.workflow_run_id == workflow_run.id,
            Funnel.user_id == current_user.id,
        )
    )
    funnel = funnel_result.scalar_one_or_none()
    if funnel is None:
        raise HTTPException(status_code=404, detail="Funnel not found for workflow run")

    jobs_result = await db.execute(
        select(Job)
        .where(
            Job.workflow_run_id == workflow_run.id,
            Job.user_id == current_user.id,
        )
        .order_by(Job.created_at)
    )
    jobs = list(jobs_result.scalars().all())

    return WorkflowRunResponse(
        id=workflow_run.id,
        offer_id=workflow_run.offer_id,
        user_id=workflow_run.user_id,
        funnel_id=funnel.id,
        job_ids=[job.id for job in jobs],
        workflow_type=workflow_run.workflow_type,
        active_agents=workflow_run.active_agents,
        status=workflow_run.status,
        error=workflow_run.error,
        started_at=workflow_run.started_at,
        completed_at=workflow_run.completed_at,
        created_at=workflow_run.created_at,
        updated_at=workflow_run.updated_at,
    )
