import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.clerk_auth import get_current_user
from app.models.funnel_project import FunnelProject
from app.models.user import User
from app.schemas.funnel_project import FilePatchRequest, FilePatchResponse, FunnelProjectResponse

router = APIRouter(prefix="/funnel-projects", tags=["funnel-projects"])


@router.get("/{funnel_id}", response_model=FunnelProjectResponse)
async def get_funnel_project(
    funnel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FunnelProject:
    result = await db.execute(
        select(FunnelProject).where(
            FunnelProject.funnel_id == funnel_id,
            FunnelProject.user_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Funnel project not found")
    return project


@router.put("/{funnel_id}/files", response_model=FilePatchResponse)
async def update_funnel_project_file(
    funnel_id: uuid.UUID,
    payload: FilePatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FilePatchResponse:
    result = await db.execute(
        text(
            """
            UPDATE funnel_projects
            SET files = jsonb_set(
                files,
                ARRAY[:path_key]::text[],
                jsonb_build_object('code', CAST(:content AS text)),
                true
            ),
                updated_at = now()
            WHERE funnel_id = CAST(:funnel_id AS uuid)
              AND user_id = CAST(:user_id AS uuid)
            RETURNING updated_at
            """
        ),
        {
            "path_key": payload.path,
            "content": payload.content,
            "funnel_id": str(funnel_id),
            "user_id": str(current_user.id),
        },
    )
    updated_at = result.scalar_one_or_none()
    if updated_at is None:
        await db.rollback()
        raise HTTPException(status_code=404, detail="Funnel project not found")

    await db.commit()

    return FilePatchResponse(path=payload.path, updated_at=updated_at)
