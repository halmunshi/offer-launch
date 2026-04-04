import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AgentType, FunnelStatus, JobStatus, WorkflowStatus
from app.models.funnel import Funnel
from app.models.job import Job
from app.models.offer import Offer
from app.models.user import User
from app.models.workflow_run import WorkflowRun


@pytest.mark.asyncio
async def test_create_workflow_run_creates_records_and_dispatches_task(
    api_client,
    db_session: AsyncSession,
    primary_user: User,
    valid_intake_data: dict,
    celery_mock_calls: list[dict],
) -> None:
    offer = Offer(
        user_id=primary_user.id,
        name="Workflow Offer",
        industry="business coaching",
        intake_data=valid_intake_data,
    )
    db_session.add(offer)
    await db_session.commit()

    response = await api_client.post("/workflow-runs", json={"offer_id": str(offer.id)})

    assert response.status_code == 201
    payload = response.json()
    assert payload["offer_id"] == str(offer.id)
    assert payload["user_id"] == str(primary_user.id)
    assert payload["status"] == WorkflowStatus.pending.value
    assert len(payload["job_ids"]) == 2

    workflow_run = await db_session.get(WorkflowRun, payload["id"])
    assert workflow_run is not None
    assert workflow_run.status == WorkflowStatus.pending

    jobs_result = await db_session.execute(select(Job).where(Job.workflow_run_id == workflow_run.id))
    jobs = list(jobs_result.scalars().all())
    assert len(jobs) == 2
    assert {job.agent_type for job in jobs} == {AgentType.copywriter, AgentType.funnel_builder}
    assert {job.status for job in jobs} == {JobStatus.pending}

    funnel = await db_session.get(Funnel, payload["funnel_id"])
    assert funnel is not None
    assert funnel.status == FunnelStatus.generating

    assert len(celery_mock_calls) == 1
    assert celery_mock_calls[0]["method"] == "apply_async"


@pytest.mark.asyncio
async def test_get_workflow_run_returns_jobs_and_funnel(
    api_client,
    primary_user: User,
    db_session: AsyncSession,
    valid_intake_data: dict,
) -> None:
    offer = Offer(
        user_id=primary_user.id,
        name="Workflow Offer 2",
        industry="business coaching",
        intake_data=valid_intake_data,
    )
    db_session.add(offer)
    await db_session.commit()

    create_response = await api_client.post("/workflow-runs", json={"offer_id": str(offer.id)})
    assert create_response.status_code == 201

    workflow_run_id = create_response.json()["id"]
    response = await api_client.get(f"/workflow-runs/{workflow_run_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == workflow_run_id
    assert payload["funnel_id"] is not None
    assert len(payload["job_ids"]) == 2


@pytest.mark.asyncio
async def test_create_workflow_run_returns_409_when_active_run_exists(
    api_client,
    db_session: AsyncSession,
    primary_user: User,
    valid_intake_data: dict,
    celery_mock_calls: list[dict],
) -> None:
    offer = Offer(
        user_id=primary_user.id,
        name="Conflict Offer",
        industry="business coaching",
        intake_data=valid_intake_data,
    )
    db_session.add(offer)
    await db_session.flush()

    active_run = WorkflowRun(
        offer_id=offer.id,
        user_id=primary_user.id,
        status=WorkflowStatus.pending,
    )
    db_session.add(active_run)
    await db_session.commit()

    response = await api_client.post("/workflow-runs", json={"offer_id": str(offer.id)})

    assert response.status_code == 409
    assert response.json()["detail"] == "A funnel generation is already in progress."
    assert celery_mock_calls == []


@pytest.mark.asyncio
async def test_get_workflow_run_returns_404_for_other_user(
    api_client,
    db_session: AsyncSession,
    primary_user: User,
    secondary_user: User,
    set_current_user,
    valid_intake_data: dict,
) -> None:
    foreign_offer = Offer(
        user_id=secondary_user.id,
        name="Foreign Offer",
        industry="business coaching",
        intake_data=valid_intake_data,
    )
    db_session.add(foreign_offer)
    await db_session.flush()

    foreign_run = WorkflowRun(
        offer_id=foreign_offer.id,
        user_id=secondary_user.id,
    )
    db_session.add(foreign_run)
    await db_session.flush()

    foreign_funnel = Funnel(
        offer_id=foreign_offer.id,
        workflow_run_id=foreign_run.id,
        user_id=secondary_user.id,
        name="Foreign Funnel",
    )
    db_session.add(foreign_funnel)

    job_one = Job(
        workflow_run_id=foreign_run.id,
        offer_id=foreign_offer.id,
        user_id=secondary_user.id,
        agent_type=AgentType.copywriter,
        status=JobStatus.pending,
        progress=[],
    )
    job_two = Job(
        workflow_run_id=foreign_run.id,
        offer_id=foreign_offer.id,
        user_id=secondary_user.id,
        agent_type=AgentType.funnel_builder,
        status=JobStatus.pending,
        progress=[],
    )
    db_session.add(job_one)
    db_session.add(job_two)
    await db_session.commit()

    set_current_user(primary_user)

    response = await api_client.get(f"/workflow-runs/{foreign_run.id}")
    assert response.status_code == 404
