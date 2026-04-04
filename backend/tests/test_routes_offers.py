import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.offer import Offer
from app.models.user import User


@pytest.mark.asyncio
async def test_create_get_and_update_offer(api_client, valid_intake_data: dict) -> None:
    create_response = await api_client.post(
        "/offers",
        json={"name": "  High Ticket Accelerator  ", "intake_data": valid_intake_data},
    )
    assert create_response.status_code == 201
    created = create_response.json()

    get_response = await api_client.get(f"/offers/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "  High Ticket Accelerator  "

    patch_response = await api_client.patch(
        f"/offers/{created['id']}",
        json={"name": "  Renamed Offer  "},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "Renamed Offer"


@pytest.mark.asyncio
async def test_archive_offer_hides_it_from_list(api_client, valid_intake_data: dict) -> None:
    first = await api_client.post(
        "/offers",
        json={"name": "Offer One", "intake_data": valid_intake_data},
    )
    second = await api_client.post(
        "/offers",
        json={"name": "Offer Two", "intake_data": valid_intake_data},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    archive_response = await api_client.delete(f"/offers/{first.json()['id']}")
    assert archive_response.status_code == 204

    list_response = await api_client.get("/offers")
    assert list_response.status_code == 200
    listed_ids = {item["id"] for item in list_response.json()}
    assert first.json()["id"] not in listed_ids
    assert second.json()["id"] in listed_ids


@pytest.mark.asyncio
async def test_offer_routes_return_404_for_other_users_records(
    api_client,
    db_session: AsyncSession,
    primary_user: User,
    secondary_user: User,
    set_current_user,
    valid_intake_data: dict,
) -> None:
    foreign_offer = Offer(
        user_id=secondary_user.id,
        name="Secondary Offer",
        industry="business coaching",
        intake_data=valid_intake_data,
    )
    db_session.add(foreign_offer)
    await db_session.commit()

    set_current_user(primary_user)

    get_response = await api_client.get(f"/offers/{foreign_offer.id}")
    patch_response = await api_client.patch(
        f"/offers/{foreign_offer.id}",
        json={"name": "Should Fail"},
    )
    delete_response = await api_client.delete(f"/offers/{foreign_offer.id}")

    assert get_response.status_code == 404
    assert patch_response.status_code == 404
    assert delete_response.status_code == 404
