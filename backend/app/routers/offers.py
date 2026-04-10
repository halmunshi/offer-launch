import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.clerk_auth import get_current_user
from app.models.enums import OfferStatus
from app.models.offer import Offer
from app.models.user import User
from app.schemas.offer import OfferCreate, OfferResponse, OfferUpdate

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post(
    "",
    response_model=OfferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an offer",
    description="Creates a new offer container and stores normalized intake data.",
    response_description="Created offer.",
)
async def create_offer(
    payload: OfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Offer:
    intake_data = payload.intake_data.model_dump()

    offer = Offer(
        user_id=current_user.id,
        name=payload.name,
        industry=(current_user.industry or "General").strip() or "General",
        intake_data=intake_data,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


@router.get(
    "",
    response_model=list[OfferResponse],
    summary="List offers",
    description="Lists active offers for the current user, newest first.",
    response_description="List of offers.",
)
async def list_offers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Offer]:
    result = await db.execute(
        select(Offer)
        .where(
            Offer.user_id == current_user.id,
            Offer.status != OfferStatus.archived,
        )
        .order_by(desc(Offer.created_at))
    )
    return list(result.scalars().all())


@router.get(
    "/{offer_id}",
    response_model=OfferResponse,
    summary="Get offer by ID",
    description="Returns a single offer owned by the authenticated user.",
    responses={404: {"description": "Offer not found."}},
)
async def get_offer(
    offer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Offer:
    result = await db.execute(
        select(Offer).where(
            Offer.id == offer_id,
            Offer.user_id == current_user.id,
        )
    )
    offer = result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    return offer


@router.patch(
    "/{offer_id}",
    response_model=OfferResponse,
    summary="Update offer name",
    description="Updates the offer display name for an owned offer.",
    responses={404: {"description": "Offer not found."}},
)
async def update_offer(
    offer_id: uuid.UUID,
    payload: OfferUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Offer:
    result = await db.execute(
        select(Offer).where(
            Offer.id == offer_id,
            Offer.user_id == current_user.id,
        )
    )
    offer = result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    if payload.name is not None:
        offer.name = payload.name.strip()

    if payload.industry is not None:
        offer.industry = payload.industry.strip() or offer.industry

    if payload.intake_data is not None:
        offer.intake_data = payload.intake_data.model_dump()

    await db.commit()
    await db.refresh(offer)
    return offer


@router.delete(
    "/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete offer",
    description="Permanently deletes an owned offer and cascades to related records.",
    responses={404: {"description": "Offer not found."}},
)
async def delete_offer(
    offer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    result = await db.execute(
        select(Offer).where(
            Offer.id == offer_id,
            Offer.user_id == current_user.id,
        )
    )
    offer = result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    await db.delete(offer)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
