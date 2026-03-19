# OfferLaunch — BACKEND.md
> Read PLAN.md first, then this file. This covers backend-specific implementation.
> Stack: FastAPI (Python 3.11+) · SQLAlchemy 2.0 async · Alembic · Celery · Upstash Redis · Neon Postgres

---

## Folder structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI app init, middleware, router registration
│   ├── config.py                   # Settings via pydantic-settings — reads from .env
│   ├── database.py                 # Async SQLAlchemy engine + session factory
│   │
│   ├── middleware/
│   │   ├── clerk_auth.py           # Validate Clerk JWT on every request
│   │   ├── rate_limit.py           # slowapi rate limiter setup
│   │   └── cors.py                 # CORS config (whitelist only)
│   │
│   ├── routers/
│   │   ├── health.py               # GET /health (public — UptimeRobot ping)
│   │   ├── webhooks.py             # POST /webhooks/clerk (public — Clerk events)
│   │   ├── offers.py               # POST /offers, GET /offers, GET /offers/{id}
│   │   ├── funnels.py              # GET /funnels/{id}, PATCH /funnels/{id}
│   │   ├── jobs.py                 # POST /jobs, GET /jobs/{id}, GET /jobs/{id}/stream (SSE)
│   │   └── exports.py              # GET /exports/zip/{funnel_id}, CF2 OAuth + push
│   │
│   ├── models/                     # SQLAlchemy ORM models (one file per table)
│   │   ├── user.py
│   │   ├── offer.py
│   │   ├── funnel.py
│   │   ├── funnel_step.py
│   │   ├── job.py
│   │   ├── export.py
│   │   └── integration.py
│   │
│   ├── schemas/                    # Pydantic v2 request/response schemas
│   │   ├── offer.py                # OfferCreate, OfferResponse
│   │   ├── funnel.py               # FunnelResponse
│   │   ├── job.py                  # JobCreate, JobResponse, ProgressEvent
│   │   └── export.py               # ExportRequest, ExportResponse
│   │
│   ├── agents/                     # LangGraph-compatible agent nodes
│   │   ├── __init__.py
│   │   ├── base.py                 # LLMClient abstraction (never bypass this)
│   │   ├── state.py                # AgentState TypedDict
│   │   ├── orchestrator.py         # STUB — v2 only. Contains TODO comment only.
│   │   ├── analyst.py              # Market analyst node
│   │   ├── copywriter.py           # Copywriter node
│   │   └── assembler.py            # HTML assembler node
│   │
│   ├── pipeline/
│   │   ├── runner.py               # Sequential pipeline (calls nodes in order)
│   │   └── templates/              # HTML page templates with {{SLOT}} placeholders
│   │       ├── vsl/
│   │       │   ├── 01_presell.html
│   │       │   ├── 02_vsl.html
│   │       │   ├── 03_order.html
│   │       │   ├── 04_upsell.html
│   │       │   ├── 05_downsell.html
│   │       │   └── 06_thankyou.html
│   │       └── lead_magnet/
│   │           ├── 01_optin.html
│   │           ├── 02_thankyou.html
│   │           ├── 03_bridge.html
│   │           └── 04_offer.html
│   │
│   ├── workers/
│   │   ├── celery_app.py           # Celery instance configured with Upstash Redis
│   │   └── tasks.py                # generate_funnel Celery task
│   │
│   └── services/
│       ├── storage.py              # Cloudflare R2 via boto3 (S3-compatible)
│       ├── export.py               # ZIP builder using zipfile stdlib
│       ├── clickfunnels.py         # CF2 OAuth flow + API push
│       └── encryption.py          # Fernet encryption for OAuth tokens
│
├── alembic/                        # DB migrations
│   ├── env.py
│   └── versions/
├── tests/
├── requirements.txt
├── Dockerfile                      # Not used in MVP — ready for v2
├── .env.example
└── BACKEND.md                      # This file
```

---

## Key implementation details

### App entry point (`app/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI(title="OfferLaunch API")

# CORS — whitelist only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://offerlaunch.netlify.app",   # production
        "http://localhost:3000",              # dev
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
app.include_router(health.router)         # /health — no auth
app.include_router(webhooks.router)       # /webhooks — no auth (but signature verified)
app.include_router(offers.router)         # /offers — auth required
app.include_router(funnels.router)        # /funnels — auth required
app.include_router(jobs.router)           # /jobs — auth required
app.include_router(exports.router)        # /exports — auth required
```

### Auth middleware (`middleware/clerk_auth.py`)

Every protected route calls `get_current_user()` as a dependency:

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    # Verify JWT with Clerk's public key
    # Extract clerk_id from sub claim
    # Query user from DB by clerk_id
    # Return User model
    # Raise 401 if invalid/expired
```

### Route ownership pattern (use on every query)

```python
# ALWAYS filter by both id AND user_id
result = await db.execute(
    select(Funnel).where(
        Funnel.id == funnel_id,
        Funnel.user_id == current_user.id  # ownership check — never omit this
    )
)
funnel = result.scalar_one_or_none()
if not funnel:
    raise HTTPException(status_code=404)  # 404 not 403 — don't leak existence
```

### Rate limiting on generation

```python
@router.post("/")
@limiter.limit("3/hour;10/day")  # per authenticated user
async def create_job(request: Request, ...):
    ...
```

### Celery + Upstash (`workers/celery_app.py`)

```python
from celery import Celery

celery = Celery(
    "offerlaunch",
    broker=settings.CELERY_BROKER_URL,      # rediss://... Upstash URL
    backend=settings.CELERY_RESULT_BACKEND, # same Upstash URL
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},  # Upstash requires SSL
)
```

### generate_funnel task (`workers/tasks.py`)

```python
@celery.task(bind=True, max_retries=3)
def generate_funnel(self, funnel_id: str, offer_id: str, job_id: str):
    """
    1. Load offer intake data from DB
    2. Build initial AgentState
    3. Run pipeline.runner.run_pipeline()
    4. Save results to DB
    5. Update job status to done/error
    """
    # All DB access inside task uses sync SQLAlchemy (Celery is sync)
    # Use asyncio.run() if you need async within the task
```

### SSE endpoint (`routers/jobs.py`)

```python
@router.get("/{job_id}/stream")
async def stream_job_progress(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify job belongs to current_user first
    job = await get_job_owned_by(job_id, current_user.id, db)
    if not job:
        raise HTTPException(404)

    async def event_generator():
        last_count = 0
        while True:
            if await request.is_disconnected():
                break
            # Poll job progress from DB
            current = await get_job_progress(job_id, db)
            # Send any new progress events since last poll
            new_events = current.progress[last_count:]
            for event in new_events:
                yield f"data: {json.dumps(event)}\n\n"
            last_count = len(current.progress)
            if current.status in ("done", "error"):
                yield f"data: {json.dumps({'status': current.status, 'done': True})}\n\n"
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### LLM abstraction (`agents/base.py`)

```python
class LLMClient:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.LLM_MODEL  # "claude-haiku-4-5-20251001"

    async def complete(self, system: str, user: str, max_tokens: int = 4096) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=[{
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"}  # prompt caching — 80% cost reduction
            }],
            messages=[{"role": "user", "content": user}]
        )
        return response.content[0].text
```

### HTML template injection (`agents/assembler.py`)

```python
import html

def inject_copy(template_path: str, copy: dict) -> str:
    with open(template_path) as f:
        template = f.read()
    for key, value in copy.items():
        safe_value = html.escape(str(value))  # ALWAYS escape — prevents stored XSS
        template = template.replace(f"{{{{{key}}}}}", safe_value)
    return template
```

### Cloudflare R2 (`services/storage.py`)

```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
)

async def upload_html(key: str, html: str) -> str:
    s3.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        Body=html.encode("utf-8"),
        ContentType="text/html",
    )
    return f"{settings.R2_PUBLIC_URL}/{key}"  # public URL
```

### Fernet encryption for OAuth tokens (`services/encryption.py`)

```python
from cryptography.fernet import Fernet

def encrypt(value: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.decrypt(value.encode()).decode()
```

---

## Pydantic input schemas — enforce max lengths

```python
class OfferCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    intake_data: IntakeData

class IntakeData(BaseModel):
    role: str = Field(max_length=50)
    industry: str = Field(max_length=100)
    brand_name: str = Field(max_length=100)
    credibility: str = Field(max_length=2000)
    offer_name: str = Field(max_length=100)
    offer_one_liner: str = Field(max_length=300)
    price_point: str = Field(max_length=50)
    whats_included: str = Field(max_length=3000)
    unique_mechanism: str = Field(max_length=2000)
    transformation: str = Field(max_length=2000)
    ideal_client: str = Field(max_length=2000)
    age_ranges: list[str] = Field(max_length=5)
    pain_point: str = Field(max_length=2000)
    awareness_level: str = Field(max_length=50)
    testimonials: list[str] = Field(default=[], max_length=3)
    assets: list[str] = Field(default=[])
    copy_style: str = Field(max_length=50)
    funnel_type: Literal["vsl", "lead_magnet"]
    theme: str = Field(max_length=50)
    # ... etc
```

---

## Environment variables

```bash
# backend/.env (never commit — use .env.example with placeholders)

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/offerlaunch?sslmode=require

# Redis (Upstash)
CELERY_BROKER_URL=rediss://:token@xxx.upstash.io:6380/0
CELERY_RESULT_BACKEND=rediss://:token@xxx.upstash.io:6380/0

# LLM
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-haiku-4-5-20251001

# Storage (Cloudflare R2)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=offerlaunch-assets
R2_PUBLIC_URL=https://assets.offerlaunch.com

# Auth (Clerk)
CLERK_SECRET_KEY=sk_...
CLERK_WEBHOOK_SECRET=whsec_...
CLERK_JWKS_URL=https://clerk.offerlaunch.com/.well-known/jwks.json

# ClickFunnels OAuth
CF_CLIENT_ID=...
CF_CLIENT_SECRET=...
CF_REDIRECT_URI=https://offerlaunch-api.onrender.com/exports/cf/callback

# Encryption
ENCRYPTION_KEY=...  # generate with: Fernet.generate_key().decode()

# Email
RESEND_API_KEY=re_...

# App
FRONTEND_URL=https://offerlaunch.netlify.app
ENVIRONMENT=production  # development | production
```

---

## Render deployment

### API service
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

### Worker service (separate Render service, same repo)
- Build command: `pip install -r requirements.txt`
- Start command: `celery -A app.workers.celery_app worker --loglevel=info`
- No health check needed

### UptimeRobot
- Monitor type: HTTP(s)
- URL: `https://offerlaunch-api.onrender.com/health`
- Interval: every 5 minutes
- Keeps both services awake (worker connects to Redis on startup and stays alive)

---

## Requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.0
pydantic-settings==2.2.1
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.13.1
celery==5.4.0
redis==5.0.4
anthropic==0.28.0
boto3==1.34.0
cryptography==42.0.0
python-jose[cryptography]==3.3.0
httpx==0.27.0
slowapi==0.1.9
resend==0.8.0
python-multipart==0.0.9
```

---

## Hard constraints for Claude Code (backend-specific)

1. Sync SQLAlchemy in Celery tasks (Celery is sync). Async SQLAlchemy in FastAPI routes.
2. Never return a 403 for ownership failures — return 404. Don't leak resource existence.
3. Every router dependency chain must include `get_current_user` except /health and /webhooks.
4. Progress events written to `jobs.progress` JSONB must be appended (not overwritten).
5. R2 object keys follow pattern: `funnels/{funnel_id}/steps/{step_type}.html`
6. Templates loaded at startup and cached in memory — do not read template files per-request.
7. All LLM outputs must be validated as valid JSON before saving to DB. Retry once if invalid.
8. Celery tasks must catch all exceptions and update job status to "error" before re-raising.
9. The `/webhooks/clerk` endpoint must verify svix signature before processing any event.
10. Agent node functions are pure: given the same AgentState input, produce the same output.