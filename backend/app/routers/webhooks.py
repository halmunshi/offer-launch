from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError

from app.config import settings
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _build_full_name(data: dict[str, Any]) -> str | None:
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    full_name = f"{first_name} {last_name}".strip()
    return full_name or None


def _extract_email(data: dict[str, Any]) -> str | None:
    email_addresses = data.get("email_addresses") or []
    if not email_addresses:
        return None

    first_email = email_addresses[0] or {}
    return first_email.get("email_address")


@router.post(
    "/clerk",
    summary="Receive Clerk webhook",
    description=(
        "Verifies Svix signature and upserts or deletes users for Clerk lifecycle events."
    ),
    responses={400: {"description": "Invalid webhook signature."}},
)
async def clerk_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    payload = await request.body()

    headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }

    try:
        event = Webhook(settings.CLERK_WEBHOOK_SECRET).verify(payload, headers)
    except WebhookVerificationError as error:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from error

    event_type = event.get("type")
    data = event.get("data") or {}

    if event_type == "user.created":
        clerk_id = data.get("id")
        email = _extract_email(data)

        if not clerk_id or not email:
            return {"status": "ok"}

        stmt = insert(User).values(
            clerk_id=clerk_id,
            email=email,
            full_name=_build_full_name(data),
            avatar_url=data.get("image_url"),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[User.clerk_id],
            set_={
                "email": email,
                "full_name": _build_full_name(data),
                "avatar_url": data.get("image_url"),
            },
        )
        await db.execute(stmt)
        await db.commit()
        return {"status": "ok"}

    if event_type == "user.updated":
        clerk_id = data.get("id")
        email = _extract_email(data)

        if not clerk_id or not email:
            return {"status": "ok"}

        stmt = (
            update(User)
            .where(User.clerk_id == clerk_id)
            .values(
                email=email,
                full_name=_build_full_name(data),
                avatar_url=data.get("image_url"),
            )
        )
        await db.execute(stmt)
        await db.commit()
        return {"status": "ok"}

    if event_type == "user.deleted":
        clerk_id = data.get("id")
        if not clerk_id:
            return {"status": "ok"}

        stmt = delete(User).where(User.clerk_id == clerk_id)
        await db.execute(stmt)
        await db.commit()
        return {"status": "ok"}

    return {"status": "ok"}
