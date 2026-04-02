from typing import Optional, TypedDict


class AgentState(TypedDict):
    # -- Identifiers -------------------------------------------------
    workflow_run_id: str
    offer_id: str
    funnel_id: str
    job_id: str
    copywriter_job_id: Optional[str]

    # -- Pipeline inputs ---------------------------------------------
    # offer_intake is optional. Agents work with or without it.
    # None means user has not completed the intake form yet.
    workflow_type: str
    active_agents: list[str]
    offer_intake: Optional[dict]
    funnel_type: str
    theme_direction: str
    connected_platforms: dict

    # -- Agent outputs -----------------------------------------------
    copywriter_output: Optional[str]
    funnel_builder_output: Optional[dict]

    # -- V2 HIL fields (defined now, unused in MVP) -----------------
    pending_approval: Optional[dict]
    approval_response: Optional[dict]

    # -- Progress tracking -------------------------------------------
    progress: list[dict]
    error: Optional[str]
