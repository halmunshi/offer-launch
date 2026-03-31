import asyncio
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.agents.state import AgentState
from app.config import settings
from app.pipeline.graph import run_pipeline


def _load_boilerplate_files() -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = repo_root / "boilerplate" / "manifest.py"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Boilerplate manifest not found at {manifest_path}")

    spec = importlib.util.spec_from_file_location("boilerplate_manifest", manifest_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load boilerplate manifest module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_boilerplate_files()


async def seed_funnel_project(
    db: AsyncSession,
    *,
    user_id: str,
    offer_id: str,
    workflow_run_id: str,
    funnel_id: str,
    intake_data: dict,
) -> None:
    """
    Seed minimum relational chain + funnel_project row with boilerplate files.
    """
    boilerplate_files = _load_boilerplate_files()
    funnel_project_id = str(uuid4())

    await db.execute(
        text(
            """
            INSERT INTO users (id, clerk_id, email, full_name, created_at, updated_at)
            VALUES (CAST(:user_id AS uuid), :clerk_id, :email, :full_name, now(), now())
            ON CONFLICT DO NOTHING
            """
        ),
        {
            "user_id": user_id,
            "clerk_id": f"test_{user_id[:8]}",
            "email": f"test+{user_id[:8]}@offerlaunch.dev",
            "full_name": "Pipeline Test User",
        },
    )

    await db.execute(
        text(
            """
            INSERT INTO offers (
                id, user_id, name, industry, intake_data, status, created_at, updated_at
            )
            VALUES (
                CAST(:offer_id AS uuid),
                CAST(:user_id AS uuid),
                :name,
                :industry,
                CAST(:intake_data AS jsonb),
                'active',
                now(),
                now()
            )
            ON CONFLICT DO NOTHING
            """
        ),
        {
            "offer_id": offer_id,
            "user_id": user_id,
            "name": intake_data.get("offer_name", "Test Offer"),
            "industry": intake_data.get("industry", "general"),
            "intake_data": json.dumps(intake_data),
        },
    )

    await db.execute(
        text(
            """
            INSERT INTO workflow_runs (
                id, offer_id, user_id, workflow_type, active_agents, status, created_at, updated_at
            )
            VALUES (
                CAST(:workflow_run_id AS uuid),
                CAST(:offer_id AS uuid),
                CAST(:user_id AS uuid),
                'funnel_only',
                ARRAY['copywriter','funnel_builder'],
                'pending',
                now(),
                now()
            )
            ON CONFLICT DO NOTHING
            """
        ),
        {
            "workflow_run_id": workflow_run_id,
            "offer_id": offer_id,
            "user_id": user_id,
        },
    )

    await db.execute(
        text(
            """
            INSERT INTO funnels (
                id, offer_id, workflow_run_id, user_id, name, funnel_type, theme, status, created_at, updated_at
            )
            VALUES (
                CAST(:funnel_id AS uuid),
                CAST(:offer_id AS uuid),
                CAST(:workflow_run_id AS uuid),
                CAST(:user_id AS uuid),
                :name,
                :funnel_type,
                :theme,
                'draft',
                now(),
                now()
            )
            ON CONFLICT DO NOTHING
            """
        ),
        {
            "funnel_id": funnel_id,
            "offer_id": offer_id,
            "workflow_run_id": workflow_run_id,
            "user_id": user_id,
            "name": f"{intake_data.get('offer_name', 'Test Offer')} Funnel",
            "funnel_type": intake_data.get("funnel_type", "vsl"),
            "theme": intake_data.get("theme_direction", "direct-response"),
        },
    )

    await db.execute(
        text(
            """
            INSERT INTO funnel_projects (id, funnel_id, user_id, files, created_at, updated_at)
            VALUES (
                CAST(:funnel_project_id AS uuid),
                CAST(:funnel_id AS uuid),
                CAST(:user_id AS uuid),
                CAST(:files AS jsonb),
                now(),
                now()
            )
            ON CONFLICT (funnel_id) DO UPDATE
            SET files = CAST(:files AS jsonb),
                updated_at = now()
            """
        ),
        {
            "funnel_project_id": funnel_project_id,
            "funnel_id": funnel_id,
            "user_id": user_id,
            "files": json.dumps(boilerplate_files),
        },
    )
    await db.commit()


def build_test_state(
    *,
    funnel_id: str,
    workflow_run_id: str,
    offer_id: str,
    user_id: str,
) -> AgentState:
    _ = user_id
    intake = {
        "offer_name": "Six Figure Coach Academy",
        "offer_one_liner": "Build a 6-figure coaching business in 90 days",
        "brand_name": "Elite Coach Co",
        "industry": "business coaching",
        "role": "coach",
        "price_point": "2997",
        "funnel_type": "vsl",
        "copy_style": "bold",
        "theme_direction": "direct-response",
        "whats_included": "8-week live program, weekly group calls, templates",
        "unique_mechanism": "The Client Acquisition System",
        "transformation": "From zero clients to full roster in 90 days",
        "credibility_proof": "200+ coaches trained, avg first client in 14 days",
        "ideal_client": "Coaches with expertise but no consistent pipeline",
        "age_ranges": ["28-45"],
        "pain_point": "No predictable way to get clients",
        "awareness_level": "solution-aware",
        "testimonials": "Sarah M: Got my first 3k client in week 2.",
        "assets_available": "testimonials",
        "guarantee": "30-day money back guarantee",
        "selected_pages": ["vsl", "order", "thank_you"],
        "theme": "direct-response",
    }

    return {
        "workflow_run_id": workflow_run_id,
        "offer_id": offer_id,
        "funnel_id": funnel_id,
        "job_id": str(uuid4()),
        "workflow_type": "funnel_only",
        "active_agents": ["copywriter", "funnel_builder"],
        "offer_intake": intake,
        "funnel_type": "vsl",
        "theme_direction": "direct-response",
        "connected_platforms": {},
        "copywriter_output": None,
        "funnel_builder_output": None,
        "pending_approval": None,
        "approval_response": None,
        "progress": [],
        "error": None,
    }


async def verify_funnel_files(db: AsyncSession, funnel_id: str) -> dict:
    result = await db.execute(
        text("SELECT files FROM funnel_projects WHERE funnel_id = CAST(:funnel_id AS uuid)"),
        {"funnel_id": funnel_id},
    )
    row = result.fetchone()
    if not row:
        return {"passed": False, "error": "funnel_project row not found"}

    files_obj = row[0]
    files = files_obj if isinstance(files_obj, dict) else json.loads(files_obj)
    file_keys = list(files.keys())

    expected_generated = ["/src/theme.ts", "/src/App.tsx"]
    page_files = sorted([key for key in file_keys if key.startswith("/src/pages/") and key.endswith(".tsx")])
    missing = [file_path for file_path in expected_generated if file_path not in file_keys]

    return {
        "passed": len(missing) == 0 and len(page_files) >= 3,
        "total_files": len(file_keys),
        "page_files": page_files,
        "has_theme": "/src/theme.ts" in file_keys,
        "has_app_tsx": "/src/App.tsx" in file_keys,
        "missing_expected": missing,
        "all_files": sorted(file_keys),
    }


async def main() -> None:

    TEST_USER_ID="2914d88c-a2ef-4505-8bd5-1325d561ae8f" 
    TEST_FUNNEL_ID="f7946932-2ecb-4ae1-8c8d-34ec9042370f"
    
    print("=" * 60)
    print("OfferLaunch - Phase 3 Pipeline Test")
    print("=" * 60)

    database_url = settings.DATABASE_URL
    database_url_direct = settings.DATABASE_URL_DIRECT
    if not database_url or not database_url_direct:
        print("ERROR: DATABASE_URL and DATABASE_URL_DIRECT must be set")
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    engine = create_async_engine(database_url)
    async_session_local = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    user_id = os.environ.get("TEST_USER_ID", str(uuid4()))
    funnel_id = os.environ.get("TEST_FUNNEL_ID", str(uuid4()))
    offer_id = os.environ.get("TEST_OFFER_ID", str(uuid4()))
    workflow_run_id = os.environ.get("TEST_WORKFLOW_RUN_ID", str(uuid4()))

    print(f"\nTest user_id:         {user_id}")
    print(f"Test funnel_id:       {funnel_id}")
    print(f"Test workflow_run_id: {workflow_run_id}")

    state = build_test_state(
        funnel_id=funnel_id,
        workflow_run_id=workflow_run_id,
        offer_id=offer_id,
        user_id=user_id,
    )

    print("\n[1/4] Seeding funnel_project with boilerplate files...")
    async with async_session_local() as db:
        await seed_funnel_project(
            db,
            user_id=user_id,
            offer_id=offer_id,
            workflow_run_id=workflow_run_id,
            funnel_id=funnel_id,
            intake_data=state["offer_intake"] or {},
        )
    print("      Done.")

    print("\n[2/4] Building initial AgentState...")
    print(f"      offer: {state['offer_intake']['offer_name']}")
    print(f"      pages: {state['offer_intake']['selected_pages']}")

    print("\n[3/4] Running pipeline (copywriter -> funnel_builder)...")
    print("      This will take 1-3 minutes. Agent is generating...")
    start = datetime.now(timezone.utc)

    try:
        result_state = await run_pipeline(state, workflow_run_id)
    except Exception as exc:
        print(f"\nPIPELINE ERROR: {exc}")
        import traceback

        traceback.print_exc()
        await engine.dispose()
        sys.exit(1)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    print(f"      Completed in {elapsed:.1f}s")

    print("\n[4/4] Verifying files in Neon...")
    async with async_session_local() as db:
        report = await verify_funnel_files(db, funnel_id)

    print(f"\n{'=' * 60}")
    print("RESULT: PASSED ✓" if report["passed"] else "RESULT: FAILED ✗")
    print(f"{'=' * 60}")
    print(f"Total files in JSONB:  {report.get('total_files', 0)}")
    print(f"theme.ts written:      {report.get('has_theme', False)}")
    print(f"App.tsx written:       {report.get('has_app_tsx', False)}")
    print(f"Page files written:    {report.get('page_files', [])}")

    if report.get("missing_expected"):
        print(f"Missing files:         {report['missing_expected']}")

    print("\nAll files in funnel_projects.files:")
    for file_path in report.get("all_files", []):
        tag = " <- generated" if file_path.startswith("/src/pages/") or file_path in {
            "/src/theme.ts",
            "/src/App.tsx",
        } else " <- boilerplate"
        print(f"  {file_path}{tag}")

    if isinstance(result_state.get("copywriter_output"), str):
        copy_md = result_state["copywriter_output"]
        print(f"\n{'=' * 60}")
        print("COPYWRITER OUTPUT (Markdown):")
        print(f"{'=' * 60}")
        print(copy_md[:2000])
        if len(copy_md) > 2000:
            print(f"... (truncated, total {len(copy_md)} chars)")

    fb_output = result_state.get("funnel_builder_output")
    if fb_output and fb_output.get("result"):
        print(f"\n{'=' * 60}")
        print("FUNNEL BUILDER FINAL MESSAGE:")
        print(f"{'=' * 60}")
        print(fb_output["result"])

    progress_events = result_state.get("progress", [])
    print(f"\n{'=' * 60}")
    print(f"PROGRESS EVENTS ({len(progress_events)}):")
    print(f"{'=' * 60}")
    for event in progress_events:
        ts = str(event.get("ts", ""))[:19]
        stage = event.get("stage", "")
        message = event.get("message", str(event.get("content", ""))[:100])
        event_type = event.get("type", "")
        print(f"  [{ts}] {stage} | {event_type} | {message}")

    await engine.dispose()

    if not report["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
