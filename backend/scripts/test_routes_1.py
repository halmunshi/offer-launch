"""
Session 4D Verification Script
==============================

This script runs the Session 4D verification checklist against a running API.

It validates:
1) Route registration for /funnels and /funnel-projects
2) GET /funnels/{funnel_id}
3) GET /funnel-projects/{funnel_id}
4) PUT /funnel-projects/{funnel_id}/files surgical patch behavior
5) POST /workflow-runs rate limiting at 5/hour

Before running:
- Start API server (uvicorn)
- Set the configuration variables in this file
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

import httpx


# ---------------------------------------------------------------------------
# REQUIRED MANUAL CONFIGURATION
# ---------------------------------------------------------------------------
# Base URL for local API.
API_BASE_URL = "http://localhost:8000"

# Bearer token for a valid Clerk-authenticated user.
TOKEN = "eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDExMUFBQSIsImtpZCI6Imluc18zQjhIME9GNDRVYndxb2NpRjYxVEVwN0dneTUiLCJ0eXAiOiJKV1QifQ.eyJhenAiOiJodHRwOi8vbG9jYWxob3N0OjMwMDAiLCJleHAiOjE3NzUxNTk3MzEsImZ2YSI6WzAsLTFdLCJpYXQiOjE3NzUxNTk2NzEsImlzcyI6Imh0dHBzOi8vaGFyZHktaGFkZG9jay01LmNsZXJrLmFjY291bnRzLmRldiIsIm5iZiI6MTc3NTE1OTY2MSwic2lkIjoic2Vzc18zQm9lNXV6NDk3ZUZaSEdyMXp2YTFIRHhOb0EiLCJzdHMiOiJhY3RpdmUiLCJzdWIiOiJ1c2VyXzNCTmY1NFZITmZPYlhXTVR2MFJrbkF1NEVqWCIsInYiOjJ9.sW2mSPzu0c4Ju_S4yL7NPV5b0HJhKrJDNJ1d_4Zwr51A-468JfLs-mpxMgSCAB7m1LjoaCNGbDRXX85MBkKr-zRCpr9V3E11Vz5tGAsT2UzI3fRkh39A1fo1KNKbWCzQW_WVh57pyR1R9mdIYT3S7AbUkCMUWIPAJxmyvmB7dZnPGsKZ1rXlZZePIe8m4n5cs6GZxJ2qFQk5yknYblZervqNBGhvBz7ksyZmt4ANaY0l7kUKszKZeIaVNZgL7RW6RUnkKlasbEXwxlUayg6lK7p4qLjsvNqAPD7d4DEtzAvpxYLbradR4LvXhh8AgaCysFI8bJaVc6fWWTXnJFgmgA"

# Existing funnel ID owned by the token user.
FUNNEL_ID = "81eac4ca-ef88-44ad-a972-bcf6f96f30bd"

# Existing offer ID owned by the token user (used for rate limit test).
OFFER_ID = "81eac4ca-ef88-44ad-a972-bcf6f96f30bd"

# File target for surgical patch test.
PATCH_PATH = "/src/theme.ts"
PATCH_CONTENT = "export default {}"


def print_test_header(title: str) -> None:
    # Clear section delimiter for readability in terminal output.
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_json(label: str, payload: Any) -> None:
    # Always show raw JSON for each test response as requested.
    print(f"{label}:")
    print(json.dumps(payload, indent=2, default=str))


def auth_headers() -> dict[str, str]:
    # Authorization header used by all protected endpoints.
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }


def ensure_config() -> None:
    # Guardrail to avoid running with placeholder values.
    placeholders = {
        "TOKEN": TOKEN,
        "FUNNEL_ID": FUNNEL_ID,
        "OFFER_ID": OFFER_ID,
    }

    missing = [name for name, value in placeholders.items() if value.startswith("PASTE_")]
    if missing:
        print("ERROR: Update these variables before running:", ", ".join(missing))
        sys.exit(1)


def check_1_routes(client: httpx.Client) -> None:
    print_test_header("CHECK 1 - Route Registration")
    response = client.get(f"{API_BASE_URL}/openapi.json", timeout=30)
    print("Status:", response.status_code)

    data = response.json()
    paths = sorted(list((data.get("paths") or {}).keys()))
    print_json("Raw JSON (paths excerpt)", paths)

    required_paths = ["/funnels/{funnel_id}", "/funnel-projects/{funnel_id}"]
    missing = [path for path in required_paths if path not in paths]
    if missing:
        raise AssertionError(f"Missing routes: {missing}")


def check_2_get_funnel(client: httpx.Client) -> None:
    print_test_header("CHECK 2 - GET /funnels/{funnel_id}")
    response = client.get(
        f"{API_BASE_URL}/funnels/{FUNNEL_ID}",
        headers=auth_headers(),
        timeout=30,
    )
    print("Status:", response.status_code)
    body = response.json()
    print_json("Raw JSON", body)

    assert response.status_code == 200, "Expected HTTP 200"


def check_3_get_funnel_project(client: httpx.Client) -> dict[str, Any]:
    print_test_header("CHECK 3 - GET /funnel-projects/{funnel_id}")
    response = client.get(
        f"{API_BASE_URL}/funnel-projects/{FUNNEL_ID}",
        headers=auth_headers(),
        timeout=30,
    )
    print("Status:", response.status_code)
    body = response.json()
    print_json("Raw JSON", body)

    assert response.status_code == 200, "Expected HTTP 200"

    files = body.get("files") or {}
    assert isinstance(files, dict), "Expected files to be an object"
    assert len(files) >= 30, "Expected 30+ files in project"
    return body


def check_4_surgical_patch(client: httpx.Client, before_project: dict[str, Any]) -> None:
    print_test_header("CHECK 4 - PUT /funnel-projects/{funnel_id}/files (Surgical Patch)")

    # Capture baseline for target and one non-target key.
    before_files = before_project.get("files") or {}
    before_target = (before_files.get(PATCH_PATH) or {}).get("code")
    non_target_key = next((k for k in before_files.keys() if k != PATCH_PATH), None)
    before_non_target = before_files.get(non_target_key)

    put_response = client.put(
        f"{API_BASE_URL}/funnel-projects/{FUNNEL_ID}/files",
        headers=auth_headers(),
        json={"path": PATCH_PATH, "content": PATCH_CONTENT},
        timeout=30,
    )
    print("PUT Status:", put_response.status_code)
    put_body = put_response.json()
    print_json("PUT Raw JSON", put_body)
    assert put_response.status_code == 200, "Expected HTTP 200 from PUT"

    after_response = client.get(
        f"{API_BASE_URL}/funnel-projects/{FUNNEL_ID}",
        headers=auth_headers(),
        timeout=30,
    )
    print("GET-after Status:", after_response.status_code)
    after_body = after_response.json()
    print_json("GET-after Raw JSON", after_body)
    assert after_response.status_code == 200, "Expected HTTP 200 from GET-after"

    after_files = after_body.get("files") or {}
    after_target = (after_files.get(PATCH_PATH) or {}).get("code")
    after_non_target = after_files.get(non_target_key)

    # Print concise before/after summary for the surgical patch guarantee.
    print_json(
        "Before/After Summary",
        {
            "target_path": PATCH_PATH,
            "target_before_snippet": (before_target or "")[:120],
            "target_after": after_target,
            "non_target_key": non_target_key,
            "non_target_unchanged": before_non_target == after_non_target,
        },
    )

    assert after_target == PATCH_CONTENT, "Target file content was not updated"
    assert before_non_target == after_non_target, "Non-target file changed unexpectedly"


def check_5_rate_limit(client: httpx.Client) -> None:
    print_test_header("CHECK 5 - Rate Limit on POST /workflow-runs")

    statuses: list[int] = []
    bodies: list[dict[str, Any]] = []

    # Fire 6 rapid requests; limiter should block by 6th request.
    for _ in range(6):
        response = client.post(
            f"{API_BASE_URL}/workflow-runs",
            headers=auth_headers(),
            json={"offer_id": OFFER_ID},
            timeout=30,
        )
        statuses.append(response.status_code)
        bodies.append(response.json())
        time.sleep(0.1)

    print_json("Statuses", statuses)
    print_json("Raw JSON responses", bodies)

    assert statuses[-1] == 429, "Expected 6th request to be rate-limited"
    assert (
        bodies[-1].get("detail") == "Generation limit reached. Try again later."
    ), "Unexpected rate limit message"


def main() -> None:
    ensure_config()

    print("Running Session 4D verification script...")
    print(f"API_BASE_URL: {API_BASE_URL}")
    print(f"FUNNEL_ID: {FUNNEL_ID}")
    print(f"OFFER_ID: {OFFER_ID}")

    with httpx.Client() as client:
        check_1_routes(client)
        check_2_get_funnel(client)
        project = check_3_get_funnel_project(client)
        check_4_surgical_patch(client, project)
        check_5_rate_limit(client)

    print_test_header("RESULT")
    print("All Session 4D checks passed.")


if __name__ == "__main__":
    main()
