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
    vsl = "vsl"
    lead_magnet = "lead_magnet"
    webinar = "webinar"                # v2
    product_launch = "product_launch"  # v2
    book = "book"                      # v2
    application = "application"        # v2


class FunnelStatus(str, enum.Enum):
    draft = "draft"
    generating = "generating"
    ready = "ready"
    error = "error"


class StepType(str, enum.Enum):
    # Awareness / entry
    presell = "presell"
    optin = "optin"
    waiting_list = "waiting_list"
    launch_coming = "launch_coming"
    quiz = "quiz"

    # Core sales
    vsl = "vsl"
    sales = "sales"
    webinar_register = "webinar_register"
    webinar_replay = "webinar_replay"

    # Conversion / checkout
    order = "order"
    order_bump = "order_bump"
    application = "application"
    book_call = "book_call"

    # Post-purchase
    upsell = "upsell"
    downsell = "downsell"
    thankyou = "thankyou"
    members_area = "members_area"

    # Bridge / nurture
    bridge = "bridge"
    offer = "offer"
    case_study = "case_study"
    demo = "demo"

    # Custom (v2)
    custom = "custom"


class StepStatus(str, enum.Enum):
    pending = "pending"
    generating = "generating"
    ready = "ready"
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
