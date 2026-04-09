import enum


class UserPlan(str, enum.Enum):
    free = "free"
    standard = "standard"
    pro = "pro"
    agency = "agency"


class OfferStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    deleted = "deleted"


class WorkflowType(str, enum.Enum):
    funnel_only = "funnel_only"
    full_gtm = "full_gtm"          # v2
    ad_campaign = "ad_campaign"    # v2
    email_only = "email_only"      # v2
    research_only = "research_only"  # v2


class WorkflowStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    awaiting_approval = "awaiting_approval"  # v2 — HIL pause
    done = "done"
    error = "error"
    cancelled = "cancelled"


class AgentType(str, enum.Enum):
    analyst = "analyst"
    copywriter = "copywriter"
    funnel_builder = "funnel_builder"
    media_buyer = "media_buyer"  # v2
    email = "email"              # v2
    image = "image"              # v2
    video = "video"              # v2
    audio = "audio"              # v2


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    done = "done"
    error = "error"
    skipped = "skipped"


class FunnelType(str, enum.Enum):
    lead_generation = "lead_generation"
    call_funnel = "call_funnel"
    direct_sales = "direct_sales"


class FunnelStatus(str, enum.Enum):
    draft = "draft"
    generating = "generating"
    ready = "ready"
    published = "published"
    error = "error"


class ExportType(str, enum.Enum):
    github = "github"
    zip = "zip"


class IntegrationProvider(str, enum.Enum):
    github = "github"
    ghl = "ghl"
    meta_ads = "meta_ads"          # v2
    google_ads = "google_ads"      # v2
    klaviyo = "klaviyo"            # v2
    active_campaign = "active_campaign"  # v2
    mailchimp = "mailchimp"        # v2
    elevenlabs = "elevenlabs"      # v2
    kling = "kling"                # v2
    hubspot = "hubspot"            # v2
    clickfunnels = "clickfunnels"      # v2
    zoho_crm = "zoho_crm"            # v2
