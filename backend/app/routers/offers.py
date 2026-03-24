import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.clerk_auth import get_current_user
from app.models.offer import Offer
from app.models.user import User
from app.schemas.offer import OfferCreate, OfferResponse

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    payload: OfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Offer:
    intake_data = payload.intake_data.model_dump()

    offer = Offer(
        user_id=current_user.id,
        name=payload.name,
        industry=payload.intake_data.industry,
        intake_data=intake_data,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


@router.get("", response_model=list[OfferResponse])
async def list_offers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Offer]:
    result = await db.execute(
        select(Offer)
        .where(Offer.user_id == current_user.id)
        .order_by(desc(Offer.created_at))
    )
    return list(result.scalars().all())


@router.get("/{offer_id}", response_model=OfferResponse)
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
