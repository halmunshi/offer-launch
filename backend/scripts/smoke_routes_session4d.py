"""
Workflow Run Integration Smoke Test
==================================

This script tests the end-to-end workflow run lifecycle through the API.

What it tests:
1) Authenticated `POST /workflow-runs` creates a new workflow run for an existing offer.
2) API response shape includes the expected identifiers (`id`, `funnel_id`, `job_ids`).
3) Background processing updates run state from `pending/running` to terminal state.
4) Optional DB verification confirms:
   - `workflow_runs.status = done`
   - `funnels.status = ready`
   - all related `jobs.status = done`

What to expect:
- Success path: script exits `0` and prints `RESULT: PASSED`.
- Failure path: script exits `1` and prints the reason (HTTP error, timeout, error status, DB mismatch).

Prerequisites:
- FastAPI server is running (default: http://127.0.0.1:8000)
- Celery worker is running and connected
- Environment variables are set:
  - `TEST_BEARER_TOKEN` (Clerk JWT for the test user)
  - `TEST_OFFER_ID` (existing offer owned by that user)
- Optional:
  - `API_BASE_URL` (default: http://127.0.0.1:8000)
  - `WORKFLOW_TIMEOUT_SECONDS` (default: 900)
  - `POLL_INTERVAL_SECONDS` (default: 5)
  - `VERIFY_DB` (default: true)
"""

import asyncio
import json
import os
from pathlib import Path
import sys
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Load .env if python-dotenv is available.
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

# Ensure `app.*` imports work when running from backend/scripts.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings


def _auth_headers(token: str) -> dict[str, str]:
    """Build auth + content headers for API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


async def _create_workflow_run(
    client: httpx.AsyncClient,
    *,
    api_base_url: str,
    bearer_token: str,
    offer_id: str,
) -> dict[str, Any]:
    """Trigger `POST /workflow-runs` and validate response basics."""
    response = await client.post(
        f"{api_base_url}/workflow-runs",
        headers=_auth_headers(bearer_token),
        json={"offer_id": offer_id},
        timeout=30.0,
    )

    if response.status_code != 201:
        raise RuntimeError(
            "POST /workflow-runs failed "
            f"(status={response.status_code}, body={response.text})"
        )

    payload = response.json()

    # Validate minimal expected shape so downstream polling can rely on it.
    required_keys = ["id", "funnel_id", "job_ids", "status"]
    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        raise RuntimeError(f"Create response missing keys: {missing_keys}")

    if not isinstance(payload.get("job_ids"), list) or len(payload["job_ids"]) != 2:
        raise RuntimeError(f"Expected two job ids, got: {payload.get('job_ids')}")

    return payload


async def _poll_workflow_run_until_terminal(
    client: httpx.AsyncClient,
    *,
    api_base_url: str,
    bearer_token: str,
    workflow_run_id: str,
    timeout_seconds: int,
    poll_interval_seconds: int,
) -> dict[str, Any]:
    """
    Poll GET /workflow-runs/{id} until terminal status or timeout.

    Terminal states for this MVP path:
    - done
    - error
    """
    deadline = asyncio.get_event_loop().time() + timeout_seconds

    while True:
        response = await client.get(
            f"{api_base_url}/workflow-runs/{workflow_run_id}",
            headers=_auth_headers(bearer_token),
            timeout=30.0,
        )

        if response.status_code != 200:
            raise RuntimeError(
                "GET /workflow-runs/{id} failed "
                f"(status={response.status_code}, body={response.text})"
            )

        payload = response.json()
        status = payload.get("status")

        print(f"  polled status={status}")

        if status in {"done", "error"}:
            return payload

        if asyncio.get_event_loop().time() >= deadline:
            raise TimeoutError(
                f"Timed out waiting for workflow {workflow_run_id} to finish "
                f"after {timeout_seconds}s"
            )

        await asyncio.sleep(poll_interval_seconds)


async def _verify_db_state(
    *,
    workflow_run_id: str,
    funnel_id: str,
    expected_job_ids: list[str],
) -> dict[str, Any]:
    """
    Verify final DB state for run/funnel/jobs.

    This is optional but useful to confirm route + worker side-effects.
    """
    engine = create_async_engine(settings.DATABASE_URL)
    async_session_local = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session_local() as db:
            workflow_row = (
                await db.execute(
                    text(
                        """
                        SELECT id, status, error, started_at, completed_at
                        FROM workflow_runs
                        WHERE id = CAST(:id AS uuid)
                        """
                    ),
                    {"id": workflow_run_id},
                )
            ).mappings().first()

            funnel_row = (
                await db.execute(
                    text(
                        """
                        SELECT id, status
                        FROM funnels
                        WHERE id = CAST(:id AS uuid)
                        """
                    ),
                    {"id": funnel_id},
                )
            ).mappings().first()

            job_rows = list(
                (
                    await db.execute(
                        text(
                            """
                            SELECT id, status, error
                            FROM jobs
                            WHERE workflow_run_id = CAST(:workflow_run_id AS uuid)
                            ORDER BY created_at
                            """
                        ),
                        {"workflow_run_id": workflow_run_id},
                    )
                ).mappings().all()
            )

        actual_job_ids = [str(row["id"]) for row in job_rows]
        statuses = {
            "workflow": workflow_row["status"] if workflow_row else None,
            "funnel": funnel_row["status"] if funnel_row else None,
            "jobs": [row["status"] for row in job_rows],
        }

        return {
            "passed": (
                workflow_row is not None
                and funnel_row is not None
                and statuses["workflow"] == "done"
                and statuses["funnel"] == "ready"
                and len(job_rows) == 2
                and set(actual_job_ids) == set(expected_job_ids)
                and all(status == "done" for status in statuses["jobs"])
            ),
            "statuses": statuses,
            "workflow_error": workflow_row["error"] if workflow_row else None,
            "actual_job_ids": actual_job_ids,
            "expected_job_ids": expected_job_ids,
        }
    finally:
        await engine.dispose()


async def main() -> None:
    """Run the workflow run integration smoke test."""
    api_base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    bearer_token = os.environ.get("TEST_BEARER_TOKEN", "").strip()
    offer_id = os.environ.get("TEST_OFFER_ID", "").strip()

    timeout_seconds = int(os.environ.get("WORKFLOW_TIMEOUT_SECONDS", "900"))
    poll_interval_seconds = int(os.environ.get("POLL_INTERVAL_SECONDS", "5"))
    verify_db = os.environ.get("VERIFY_DB", "true").lower() in {"1", "true", "yes", "y"}

    print("=" * 72)
    print("OfferLaunch - Workflow Run Integration Test")
    print("=" * 72)

    # Basic preflight checks.
    if not bearer_token:
        print("ERROR: TEST_BEARER_TOKEN is required")
        sys.exit(1)
    if not offer_id:
        print("ERROR: TEST_OFFER_ID is required")
        sys.exit(1)

    print(f"API_BASE_URL: {api_base_url}")
    print(f"TEST_OFFER_ID: {offer_id}")
    print(f"VERIFY_DB:    {verify_db}")

    async with httpx.AsyncClient() as client:
        print("\n[1/3] Creating workflow run...")
        created = await _create_workflow_run(
            client,
            api_base_url=api_base_url,
            bearer_token=bearer_token,
            offer_id=offer_id,
        )
        print(json.dumps(created, indent=2))

        workflow_run_id = str(created["id"])
        funnel_id = str(created["funnel_id"])
        job_ids = [str(job_id) for job_id in created["job_ids"]]

        print("\n[2/3] Polling workflow until terminal status...")
        final_state = await _poll_workflow_run_until_terminal(
            client,
            api_base_url=api_base_url,
            bearer_token=bearer_token,
            workflow_run_id=workflow_run_id,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        print("Final API state:")
        print(json.dumps(final_state, indent=2))

    # Fail immediately if workflow ended in error.
    if final_state.get("status") == "error":
        print("\nRESULT: FAILED")
        print(f"Reason: workflow entered error state ({final_state.get('error')})")
        sys.exit(1)

    if final_state.get("status") != "done":
        print("\nRESULT: FAILED")
        print(f"Reason: unexpected terminal status {final_state.get('status')}")
        sys.exit(1)

    print("\n[3/3] Verifying DB state...")
    if verify_db:
        report = await _verify_db_state(
            workflow_run_id=workflow_run_id,
            funnel_id=funnel_id,
            expected_job_ids=job_ids,
        )
        print(json.dumps(report, indent=2))

        if not report["passed"]:
            print("\nRESULT: FAILED")
            print("Reason: DB state mismatch")
            sys.exit(1)
    else:
        print("Skipped (VERIFY_DB=false)")

    print("\nRESULT: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
