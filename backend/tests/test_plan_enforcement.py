import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.funnel import Funnel
from app.models.offer import Offer
from app.models.user import User


@pytest.mark.asyncio
async def test_free_plan_blocks_second_funnel_generation_current_behavior(
    api_client,
    db_session: AsyncSession,
    primary_user: User,
    valid_intake_data: dict,
    celery_mock_calls: list[dict],
) -> None:
    offer = Offer(
        user_id=primary_user.id,
        name="Offer for free plan cap",
        industry="business coaching",
        intake_data=valid_intake_data,
    )
    db_session.add(offer)
    await db_session.flush()

    existing_funnel = Funnel(
        offer_id=offer.id,
        user_id=primary_user.id,
        name="Existing Funnel",
    )
    db_session.add(existing_funnel)
    await db_session.commit()

    response = await api_client.post("/workflow-runs", json={"offer_id": str(offer.id)})

    # TODO: expected status should be 402 after pricing flow update.
    assert response.status_code == 403
    assert response.json()["detail"] == "Free plan supports one funnel. Upgrade to create more."
    assert celery_mock_calls == []
