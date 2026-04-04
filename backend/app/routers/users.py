from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.clerk_auth import get_current_user
from app.models.enums import FunnelStatus, OfferStatus
from app.models.funnel import Funnel
from app.models.offer import Offer
from app.models.user import User
from app.models.workflow_run import WorkflowRun
from app.schemas.common import BaseSchema
from app.schemas.user import UsageResponse, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


class UserUpdateRequest(BaseSchema):
    full_name: str = Field(min_length=1, max_length=255)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the authenticated user profile from Clerk-linked identity.",
)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Updates editable profile fields for the authenticated user.",
)
async def update_me(
    payload: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    current_user.full_name = payload.full_name.strip()
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get(
    "/me/usage",
    response_model=UsageResponse,
    summary="Get usage summary",
    description="Returns current funnel count, active offer count, and monthly run count.",
)
async def get_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UsageResponse:
    funnel_count_result = await db.execute(
        select(func.count(Funnel.id)).where(
            Funnel.user_id == current_user.id,
            Funnel.status != FunnelStatus.error,
        )
    )
    offer_count_result = await db.execute(
        select(func.count(Offer.id)).where(
            Offer.user_id == current_user.id,
            Offer.status == OfferStatus.active,
        )
    )
    runs_this_month_result = await db.execute(
        select(func.count(WorkflowRun.id)).where(
            WorkflowRun.user_id == current_user.id,
            WorkflowRun.created_at >= func.date_trunc("month", func.now()),
        )
    )

    return UsageResponse(
        funnel_count=int(funnel_count_result.scalar_one()),
        offer_count=int(offer_count_result.scalar_one()),
        runs_this_month=int(runs_this_month_result.scalar_one()),
    )
