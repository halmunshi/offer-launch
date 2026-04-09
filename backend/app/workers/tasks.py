import asyncio
import atexit
import importlib.util
import json
import logging
import time
from pathlib import Path
from uuid import uuid4

from langfuse import propagate_attributes
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.agents.state import AgentState
from app.config import settings
from app.pipeline.graph import run_pipeline
from app.services.langfuse_client import get_langfuse
from app.workers.celery_app import celery_app

logger = logging.getLogger("offerlaunch.worker")

_worker_loop: asyncio.AbstractEventLoop | None = None

sync_url = settings.DATABASE_URL_DIRECT.replace(
    "postgresql://",
    "postgresql+psycopg2://",
    1,
)
sync_engine = create_engine(sync_url)
SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    global _worker_loop

    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)

    return _worker_loop


def _run_async(coro):
    loop = _get_worker_loop()
    return loop.run_until_complete(coro)


@atexit.register
def _close_worker_loop() -> None:
    global _worker_loop

    if _worker_loop is None or _worker_loop.is_closed():
        return

    _worker_loop.close()
    _worker_loop = None


class MissingWorkflowContextError(ValueError):
    """Raised when workflow context rows are missing and task should be dropped."""


def _resolve_boilerplate_manifest_path() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    repo_root = Path(__file__).resolve().parents[3]
    candidates = [
        backend_root / "boilerplate" / "manifest.py",
        repo_root / "boilerplate" / "manifest.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _load_boilerplate_files() -> dict:
    manifest_path = _resolve_boilerplate_manifest_path()
    if not manifest_path.exists():
        raise FileNotFoundError(f"Boilerplate manifest not found: {manifest_path}")

    spec = importlib.util.spec_from_file_location("boilerplate_manifest", manifest_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import boilerplate manifest module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_boilerplate_files()


def _load_workflow_context(db: Session, workflow_run_id: str) -> tuple[dict, dict, dict, list[dict]]:
    workflow_run = db.execute(
        text("SELECT * FROM workflow_runs WHERE id = CAST(:id AS uuid)"),
        {"id": workflow_run_id},
    ).mappings().first()
    if workflow_run is None:
        raise MissingWorkflowContextError(f"workflow_run not found: {workflow_run_id}")

    offer = db.execute(
        text("SELECT * FROM offers WHERE id = :offer_id"),
        {"offer_id": workflow_run["offer_id"]},
    ).mappings().first()
    if offer is None:
        raise MissingWorkflowContextError(f"offer not found for workflow_run: {workflow_run_id}")

    funnel = db.execute(
        text("SELECT * FROM funnels WHERE workflow_run_id = CAST(:wrid AS uuid)"),
        {"wrid": workflow_run_id},
    ).mappings().first()
    if funnel is None:
        raise MissingWorkflowContextError(f"funnel not found for workflow_run: {workflow_run_id}")

    jobs = db.execute(
        text("SELECT * FROM jobs WHERE workflow_run_id = CAST(:wrid AS uuid) ORDER BY agent_type"),
        {"wrid": workflow_run_id},
    ).mappings().all()
    if not jobs:
        raise MissingWorkflowContextError(f"jobs not found for workflow_run: {workflow_run_id}")

    return workflow_run, offer, funnel, jobs


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    ignore_result=True,
    name="app.workers.tasks.generate_funnel_task",
)
def generate_funnel_task(self, workflow_run_id: str):
    """
    Run the funnel generation pipeline as a background job.
    """
    start_time = time.time()
    funnel_id_for_log: str | None = None

    with SyncSessionLocal() as db:
        try:
            workflow_run, offer, funnel, jobs = _load_workflow_context(db, workflow_run_id)
            funnel_id_for_log = str(funnel["id"])

            logger.info(
                "Pipeline started",
                extra={
                    "workflow_run_id": workflow_run_id,
                    "funnel_id": funnel_id_for_log,
                    "status": "running",
                },
            )

            db.execute(
                text(
                    """
                    UPDATE workflow_runs
                    SET status = 'running',
                        started_at = now(),
                        langgraph_thread_id = :thread_id,
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"id": workflow_run_id, "thread_id": workflow_run_id},
            )
            db.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = 'running',
                        started_at = now(),
                        updated_at = now()
                    WHERE workflow_run_id = CAST(:wrid AS uuid)
                    """
                ),
                {"wrid": workflow_run_id},
            )
            db.commit()

            boilerplate_files = _load_boilerplate_files()
            db.execute(
                text(
                    """
                    INSERT INTO funnel_projects (
                        id,
                        funnel_id,
                        user_id,
                        files,
                        boilerplate_version,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        CAST(:id AS uuid),
                        CAST(:funnel_id AS uuid),
                        CAST(:user_id AS uuid),
                        CAST(:files AS jsonb),
                        '1.0.0',
                        now(),
                        now()
                    )
                    ON CONFLICT (funnel_id) DO UPDATE
                    SET files = EXCLUDED.files,
                        updated_at = now()
                    """
                ),
                {
                    "id": str(uuid4()),
                    "funnel_id": str(funnel["id"]),
                    "user_id": str(workflow_run["user_id"]),
                    "files": json.dumps(boilerplate_files),
                },
            )
            db.commit()

            copywriter_job = next((job for job in jobs if job["agent_type"] == "copywriter"), None)
            funnel_builder_job = next((job for job in jobs if job["agent_type"] == "funnel_builder"), None)
            if copywriter_job is None or funnel_builder_job is None:
                raise ValueError(f"expected copywriter and funnel_builder jobs for workflow_run: {workflow_run_id}")

            intake_data = offer["intake_data"] or {}
            funnel_integrations = funnel["integrations"] if isinstance(funnel.get("integrations"), dict) else {}
            selected_pages = funnel_integrations.get("selected_pages")
            if not isinstance(selected_pages, list):
                selected_pages = []
            funnel_type_value = str(
                getattr(funnel.get("funnel_type"), "value", funnel.get("funnel_type") or "lead_generation")
            )
            funnel_style_value = str(funnel.get("style") or "high_converting")

            state: AgentState = {
                "workflow_run_id": workflow_run_id,
                "offer_id": str(offer["id"]),
                "funnel_id": str(funnel["id"]),
                "job_id": str(funnel_builder_job["id"]),
                "copywriter_job_id": str(copywriter_job["id"]),
                "workflow_type": "funnel_only",
                "active_agents": ["copywriter", "funnel_builder"],
                "offer_intake": intake_data,
                "offer_industry": str(offer.get("industry") or "General"),
                "funnel_name": str(funnel.get("name") or "Untitled Funnel"),
                "funnel_type": funnel_type_value,
                "funnel_style": funnel_style_value,
                "funnel_integrations": funnel_integrations,
                "selected_pages": [str(page) for page in selected_pages],
                "connected_platforms": {},
                "copywriter_output": None,
                "funnel_builder_output": None,
                "pending_approval": None,
                "approval_response": None,
                "progress": [],
                "error": None,
            }

            langfuse_client = get_langfuse()
            if langfuse_client is not None:
                with propagate_attributes(
                    user_id=str(workflow_run["user_id"]),
                    session_id=workflow_run_id,
                    tags=["funnel_generation", str(state["funnel_type"])],
                    metadata={
                        "workflow_run_id": workflow_run_id,
                        "offer_id": str(offer["id"]),
                        "funnel_id": str(funnel["id"]),
                        "funnel_type": str(state["funnel_type"]),
                        "funnel_style": str(state["funnel_style"]),
                    },
                ):
                    final_state = _run_async(run_pipeline(state, workflow_run_id))
            else:
                final_state = _run_async(run_pipeline(state, workflow_run_id))

            db.execute(
                text(
                    """
                    UPDATE workflow_runs
                    SET status = 'done',
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"id": workflow_run_id},
            )
            db.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = 'done',
                        completed_at = now(),
                        updated_at = now()
                    WHERE workflow_run_id = CAST(:wrid AS uuid)
                    """
                ),
                {"wrid": workflow_run_id},
            )
            db.execute(
                text(
                    """
                    UPDATE funnels
                    SET status = 'ready',
                        updated_at = now()
                    WHERE id = CAST(:funnel_id AS uuid)
                    """
                ),
                {"funnel_id": str(funnel["id"])},
            )
            db.commit()

            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "Pipeline completed",
                extra={
                    "workflow_run_id": workflow_run_id,
                    "funnel_id": funnel_id_for_log,
                    "duration_ms": duration_ms,
                    "status": "done",
                },
            )
            return {"workflow_run_id": workflow_run_id, "status": "done"}

        except Exception as exc:
            if isinstance(exc, MissingWorkflowContextError):
                logger.warning("Dropping task %s: %s", workflow_run_id, exc)
                db.rollback()
                return {
                    "workflow_run_id": workflow_run_id,
                    "status": "dropped",
                    "reason": str(exc),
                }

            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Pipeline failed",
                extra={
                    "workflow_run_id": workflow_run_id,
                    "funnel_id": funnel_id_for_log,
                    "duration_ms": duration_ms,
                    "status": "error",
                },
                exc_info=True,
            )
            try:
                db.rollback()
                db.execute(
                    text(
                        """
                        UPDATE workflow_runs
                        SET status = 'error',
                            error = :error,
                            updated_at = now()
                        WHERE id = CAST(:id AS uuid)
                        """
                    ),
                    {"error": str(exc), "id": workflow_run_id},
                )
                db.execute(
                    text(
                        """
                        UPDATE jobs
                        SET status = 'error',
                            error = :error,
                            updated_at = now()
                        WHERE workflow_run_id = CAST(:wrid AS uuid)
                        """
                    ),
                    {"error": str(exc), "wrid": workflow_run_id},
                )
                db.execute(
                    text(
                        """
                        UPDATE funnels
                        SET status = 'error',
                            updated_at = now()
                        WHERE workflow_run_id = CAST(:wrid AS uuid)
                        """
                    ),
                    {"wrid": workflow_run_id},
                )
                db.commit()
            except Exception as db_exc:
                logger.error("Failed to update error state: %s", db_exc)

            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
