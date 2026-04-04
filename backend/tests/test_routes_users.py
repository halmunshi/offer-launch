import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import FunnelStatus, OfferStatus
from app.models.funnel import Funnel
from app.models.offer import Offer
from app.models.user import User
from app.models.workflow_run import WorkflowRun


@pytest.mark.asyncio
async def test_get_me_returns_current_user(api_client, primary_user: User) -> None:
    response = await api_client.get("/users/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(primary_user.id)
    assert payload["email"] == primary_user.email
    assert payload["plan"] == primary_user.plan.value


@pytest.mark.asyncio
async def test_patch_me_trims_name(api_client, db_session: AsyncSession, primary_user: User) -> None:
    response = await api_client.patch("/users/me", json={"full_name": "  Updated Name  "})
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"

    await db_session.refresh(primary_user)
    assert primary_user.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_get_usage_counts_active_resources(
    api_client,
    db_session: AsyncSession,
    primary_user: User,
    valid_intake_data: dict,
) -> None:
    active_offer = Offer(
        user_id=primary_user.id,
        name="Active Offer",
        industry="business coaching",
        intake_data=valid_intake_data,
        status=OfferStatus.active,
    )
    archived_offer = Offer(
        user_id=primary_user.id,
        name="Archived Offer",
        industry="business coaching",
        intake_data=valid_intake_data,
        status=OfferStatus.archived,
    )
    db_session.add(active_offer)
    db_session.add(archived_offer)
    await db_session.flush()

    active_funnel = Funnel(
        offer_id=active_offer.id,
        user_id=primary_user.id,
        name="Active Funnel",
        status=FunnelStatus.ready,
    )
    errored_funnel = Funnel(
        offer_id=archived_offer.id,
        user_id=primary_user.id,
        name="Errored Funnel",
        status=FunnelStatus.error,
    )
    db_session.add(active_funnel)
    db_session.add(errored_funnel)

    workflow_run = WorkflowRun(
        offer_id=active_offer.id,
        user_id=primary_user.id,
    )
    db_session.add(workflow_run)
    await db_session.commit()

    response = await api_client.get("/users/me/usage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["offer_count"] == 1
    assert payload["funnel_count"] == 1
    assert payload["runs_this_month"] == 1
