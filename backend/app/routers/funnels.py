import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.clerk_auth import get_current_user
from app.models.funnel import Funnel
from app.models.user import User
from app.schemas.common import BaseSchema
from app.schemas.funnel import FunnelResponse

router = APIRouter(prefix="/funnels", tags=["funnels"])


class FunnelUpdateRequest(BaseSchema):
    name: str = Field(min_length=1, max_length=255)


@router.get(
    "/{funnel_id}",
    response_model=FunnelResponse,
    summary="Get funnel by ID",
    description="Returns a funnel owned by the authenticated user.",
    responses={404: {"description": "Funnel not found."}},
)
async def get_funnel(
    funnel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Funnel:
    result = await db.execute(
        select(Funnel).where(
            Funnel.id == funnel_id,
            Funnel.user_id == current_user.id,
        )
    )
    funnel = result.scalar_one_or_none()
    if funnel is None:
        raise HTTPException(status_code=404, detail="Funnel not found")
    return funnel


@router.patch(
    "/{funnel_id}",
    response_model=FunnelResponse,
    summary="Update funnel name",
    description="Updates the display name of an owned funnel.",
    responses={404: {"description": "Funnel not found."}},
)
async def update_funnel(
    funnel_id: uuid.UUID,
    payload: FunnelUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Funnel:
    result = await db.execute(
        select(Funnel).where(
            Funnel.id == funnel_id,
            Funnel.user_id == current_user.id,
        )
    )
    funnel = result.scalar_one_or_none()
    if funnel is None:
        raise HTTPException(status_code=404, detail="Funnel not found")

    funnel.name = payload.name.strip()
    await db.commit()
    await db.refresh(funnel)
    return funnel


@router.get(
    "",
    response_model=list[FunnelResponse],
    summary="List funnels",
    description="Lists funnels for the authenticated user, newest first.",
)
async def list_funnels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Funnel]:
    result = await db.execute(
        select(Funnel)
        .where(Funnel.user_id == current_user.id)
        .order_by(desc(Funnel.created_at))
    )
    return list(result.scalars().all())


@router.delete(
    "/{funnel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete funnel",
    description="Permanently deletes an owned funnel and cascades to related project records.",
    responses={404: {"description": "Funnel not found."}},
)
async def delete_funnel(
    funnel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    result = await db.execute(
        select(Funnel).where(
            Funnel.id == funnel_id,
            Funnel.user_id == current_user.id,
        )
    )
    funnel = result.scalar_one_or_none()
    if funnel is None:
        raise HTTPException(status_code=404, detail="Funnel not found")

    await db.delete(funnel)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
