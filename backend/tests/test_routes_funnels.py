import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.funnel import Funnel
from app.models.offer import Offer
from app.models.user import User


@pytest.mark.asyncio
async def test_get_update_and_list_funnels(
    api_client,
    db_session: AsyncSession,
    primary_user: User,
    valid_intake_data: dict,
) -> None:
    offer = Offer(
        user_id=primary_user.id,
        name="Offer for funnel routes",
        industry="business coaching",
        intake_data=valid_intake_data,
    )
    db_session.add(offer)
    await db_session.flush()

    funnel = Funnel(
        offer_id=offer.id,
        user_id=primary_user.id,
        name="  Initial Funnel Name  ",
    )
    db_session.add(funnel)
    await db_session.commit()

    get_response = await api_client.get(f"/funnels/{funnel.id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "  Initial Funnel Name  "

    patch_response = await api_client.patch(
        f"/funnels/{funnel.id}",
        json={"name": "  Updated Funnel Name  "},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "Updated Funnel Name"

    list_response = await api_client.get("/funnels")
    assert list_response.status_code == 200
    listed_ids = {item["id"] for item in list_response.json()}
    assert str(funnel.id) in listed_ids


@pytest.mark.asyncio
async def test_funnel_routes_return_404_for_other_users_records(
    api_client,
    db_session: AsyncSession,
    primary_user: User,
    secondary_user: User,
    set_current_user,
    valid_intake_data: dict,
) -> None:
    offer = Offer(
        user_id=secondary_user.id,
        name="Secondary Offer",
        industry="business coaching",
        intake_data=valid_intake_data,
    )
    db_session.add(offer)
    await db_session.flush()

    foreign_funnel = Funnel(
        offer_id=offer.id,
        user_id=secondary_user.id,
        name="Secondary Funnel",
    )
    db_session.add(foreign_funnel)
    await db_session.commit()

    set_current_user(primary_user)

    get_response = await api_client.get(f"/funnels/{foreign_funnel.id}")
    patch_response = await api_client.patch(
        f"/funnels/{foreign_funnel.id}",
        json={"name": "Should Fail"},
    )

    assert get_response.status_code == 404
    assert patch_response.status_code == 404
