# OfferLaunch — PLAN.md
> Master reference. Read this file fully at the start of every Claude Code session,
> alongside the relevant FRONTEND.md or BACKEND.md. Never deviate from decisions made here.

---

## Full product vision

OfferLaunch is an AI-powered GTM (go-to-market) operating system for anyone with an offer to sell something online from online marketers, coaches, consultants, and agencies. The end state: a user describes their offer once and
a team of specialised AI agents autonomously produces everything needed to launch it.

### The agent team (full vision — not all built in MVP)
- **Orchestrator agent** — takes the offer, delegates to all agents, assembles output
- **Funnel builder agent** — full multi-step funnel, all pages and copy
- **Copywriter agent** — VSL scripts, email sequences, ad copy, page variants
- **Market analyst agent** — ICP research, hook angles, objection map, competitor positioning
- **Media buyer agent** — ad creative briefs, audience targeting, budget allocation
- **Designer agent** — layout, colour palette, section structure
- **Email sequence agent** — pre-launch, nurture, post-purchase, win-back

### User experience (full vision)
Fill in your offer once → come back in 10 minutes → your entire launch is ready.
Funnel built. Copy written. Ads briefed. Emails drafted. All consistent in voice and strategy.

### Monetisation (future, TBD but this is a rough idea)
- Free: 1 funnel, VSL only, watermarked export
- Pro ($47–97/mo): unlimited funnels, all types, CF2 + HTML export, all agents
- Agency ($197–297/mo): client workspaces, white-label, bulk generation
- Enterprise: custom

---

## Data hierarchy (critical — shapes the entire DB and UI)

```
User
└── Offer (like a project / repo)
    ├── Funnels (many)
    ├── Ad campaigns (future)
    ├── Email sequences (future)
    └── Strategies (future)
```

An **Offer** is the top-level container. Everything the agents produce belongs to an Offer.
A user can have many Offers. Each Offer can have many Funnels.
This is not a flat "create a funnel" tool — it is an offer-centric workspace.

---

## MVP scope (do not exceed this)

The MVP builds the **Funnel Builder** feature only.

### Two funnel types in MVP (rough structure, could be changed later)
1. **VSL funnel** — 5 pages: VSL page → Order form OR calendar booking form (imbedded calendar) → OTO upsell → Downsell → Thank you
2. **Lead magnet funnel** — 4 pages: Opt-in → Thank you → Bridge page → Offer page

### MVP user flow
```
Sign up → Onboarding wizard (19 - 21 steps, ~3–5 min) → Builder interface → Export
```

### Export targets in MVP
1. HTML ZIP download (self-host anywhere)
2. ClickFunnels 2.0 direct API push (one-click after OAuth)
3. GHL URL bridge (v1.1 — paste-per-step guide, not MVP day-one)

---

## Tech stack (locked — do not change without updating this file)

| Layer | Choice | Notes |
|---|---|---|
| Frontend | Next.js 14 (App Router, TypeScript) | Tailwind CSS + shadcn/ui + Framer Motion |
| Frontend hosting | Netlify | Free tier, commercial use allowed |
| Auth | Clerk | Next.js SDK, email + Google OAuth, 10K MAU free |
| Backend API | FastAPI (Python 3.11+) | Async, Pydantic v2, Uvicorn |
| Background worker | Celery | Async agent jobs, retries |
| API + Worker hosting | Render | Two free web services + UptimeRobot keep-alive |
| Database | Neon (serverless Postgres) | pgvector enabled, DB branching, never suspends |
| ORM | SQLAlchemy 2.0 (async) + Alembic | Alembic for all migrations |
| Job queue / broker | Upstash Redis | Serverless Redis, Celery broker + result backend |
| File storage | Cloudflare R2 | HTML assets, ZIP exports, preview URLs |
| LLM (primary) | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | ~$0.04/funnel, 64K output, sub-agent ready |
| LLM (orchestrator, v2) | Claude Sonnet 4.6 (`claude-sonnet-4-6`) | Orchestrates Haiku worker agents |
| Agent framework | LangGraph | Sequential now, real graph in v2 — same code |
| Email | Resend | 3K/mo free |
| Payments | Stripe | Wire up when first paid plan is ready |

### No Docker for MVP
Render detects Python apps natively. Add Docker in v2 when moving to AWS/ECS.

---

## Repository structure

```
offerlaunch/
├── PLAN.md                  ← this file (read at start of every session)
├── frontend/
│   ├── FRONTEND.md          ← frontend-specific instructions for Claude Code
│   └── [Next.js app]
├── backend/
│   ├── BACKEND.md           ← backend-specific instructions for Claude Code
│   └── [FastAPI app]
├── .gitignore
└── README.md
```

---

## Database schema (full — including future tables (subject to change))

```sql
-- Users (synced from Clerk via webhook)
CREATE TABLE users (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id          TEXT UNIQUE NOT NULL,
  email             TEXT NOT NULL,
  plan              TEXT NOT NULL DEFAULT 'free',  -- free | pro | agency
  stripe_customer_id TEXT,
  created_at        TIMESTAMPTZ DEFAULT now()
);

-- Offers (top-level container — like a project)
CREATE TABLE offers (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
  name              TEXT NOT NULL,                 -- e.g. "6-Figure Coach Academy"
  status            TEXT NOT NULL DEFAULT 'active',
  intake_data       JSONB NOT NULL,                -- full 19-step wizard answers
  ai_context        JSONB,                         -- enriched context from analyst agent
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);

-- Funnels (belongs to an offer)
CREATE TABLE funnels (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offer_id          UUID REFERENCES offers(id) ON DELETE CASCADE,
  user_id           UUID REFERENCES users(id) ON DELETE CASCADE,  -- denormalised for fast auth checks
  name              TEXT NOT NULL,
  funnel_type       TEXT NOT NULL DEFAULT 'vsl',   -- vsl | lead_magnet | webinar (future)
  theme             TEXT NOT NULL DEFAULT 'dark',  -- theme slug selected in wizard
  status            TEXT NOT NULL DEFAULT 'draft', -- draft | generating | ready | error
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);

-- Funnel steps (one row per page)
CREATE TABLE funnel_steps (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  funnel_id         UUID REFERENCES funnels(id) ON DELETE CASCADE,
  step_order        INTEGER NOT NULL,
  step_type         TEXT NOT NULL,  -- presell | vsl | order | upsell | downsell | thankyou | optin | bridge
  html_r2_key       TEXT,           -- R2 object key (not full URL — construct URL from key)
  raw_copy          JSONB,          -- structured copy before HTML injection (for re-generation)
  slug              TEXT NOT NULL,  -- url-safe slug e.g. "vsl-page"
  created_at        TIMESTAMPTZ DEFAULT now()
);

-- Jobs (one per generation run)
CREATE TABLE jobs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  funnel_id         UUID REFERENCES funnels(id) ON DELETE CASCADE,
  user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
  status            TEXT NOT NULL DEFAULT 'pending', -- pending | running | done | error
  current_stage     TEXT,                            -- analyst | copywriter | assembler
  progress          JSONB DEFAULT '[]'::jsonb,       -- [{stage, message, ts, done}]
  error             TEXT,
  started_at        TIMESTAMPTZ,
  completed_at      TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT now()
);

-- Exports (audit trail)
CREATE TABLE exports (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  funnel_id         UUID REFERENCES funnels(id) ON DELETE CASCADE,
  user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
  export_type       TEXT NOT NULL,  -- zip | clickfunnels | ghl_bridge
  destination       TEXT,           -- CF workspace URL or null
  exported_at       TIMESTAMPTZ DEFAULT now()
);

-- CF OAuth tokens (separate table — encrypted, sensitive)
CREATE TABLE integrations (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
  provider          TEXT NOT NULL,  -- clickfunnels | ghl (future)
  access_token_enc  TEXT NOT NULL,  -- Fernet-encrypted token
  workspace_url     TEXT,
  connected_at      TIMESTAMPTZ DEFAULT now()
);
```

### Key schema decisions
- `user_id` is denormalised onto `funnels` and `jobs` for O(1) ownership checks
- HTML is never stored in Postgres — only the R2 object key
- `raw_copy` JSONB on `funnel_steps` enables per-step re-generation without re-running all agents
- `integrations` table is separate so OAuth tokens can be encrypted independently
- `ai_context` on `offers` stores analyst output — reused across all funnels within the same offer

---

## Security requirements (non-negotiable)

### Critical — must be in MVP
1. **JWT auth on every route** — Clerk JWT validated via middleware on every backend request.
   Only `/health` and `/webhooks/clerk` are public.
2. **Ownership checks on every query** — Every DB query filters by both `id` AND `user_id`.
   Never query by `id` alone. Prevents IDOR attacks.
3. **Webhook signature verification** — Clerk webhooks verified via svix signature header.
4. **Rate limiting on generation** — 3 generations/hour, 10/day per user on free plan.
   Use `slowapi` + Upstash Redis counter.
5. **Parameterised queries only** — SQLAlchemy ORM used for all queries.
   If raw SQL is ever needed, use `bindparams()`. Never string-format SQL.
6. **HTML-escape user content** — All user-provided text is `html.escape()`d before
   injection into HTML templates. Prevents stored XSS.
7. **Prompt injection defence** — User inputs are labelled as "user-provided content"
   in system prompts. Strip control characters. Enforce length limits before LLM calls.
8. **Strict CORS** — Allow only the Netlify production domain + localhost:3000.
   Never `allow_origins=["*"]` in production.
9. **Secrets never in git** — `.env` in `.gitignore`. All secrets in Render/Netlify env dashboards.
10. **Encrypt stored OAuth tokens** — CF access tokens encrypted with Fernet before DB write.

### High — build in MVP
11. **CSP on preview iframes** — Prevent AI-generated HTML from executing scripts
    in your app's browsing context.
12. **Input length limits** — Pydantic models enforce max lengths on all text fields.
    Prevents oversized inputs crashing LLM calls or DB writes.
13. **HTTPS only** — Render + Netlify enforce this. Ensure R2 bucket is HTTPS-only.

---

## Agent architecture (LangGraph)

### AgentState (shared TypedDict — single source of truth across all agents)

```python
class AgentState(TypedDict):
    # Input
    offer_id: str
    funnel_id: str
    job_id: str
    offer_intake: dict          # Full 19-step wizard answers
    funnel_type: str            # "vsl" | "lead_magnet"

    # Intermediate outputs
    orchestrator_output: Optional[dict]   # STUB — v2 only
    analyst_output: Optional[dict]        # ICP, hooks, pain points, objections, tone
    copywriter_output: Optional[dict]     # Per-step copy for all pages
    assembler_output: Optional[dict]      # Per-step HTML strings + R2 keys

    # Progress tracking
    progress: list[dict]        # [{stage, message, ts, done}]
    error: Optional[str]
```

### LLM abstraction (never bypass this)

```python
class LLMClient:
    """Single abstraction over all LLM providers.
    To swap model: change LLM_MODEL env var. Zero agent code changes."""

    async def complete(self, system: str, user: str, max_tokens: int = 4096) -> str:
        # Uses Anthropic SDK with prompt caching on system prompt
        # cache_control: ephemeral saves ~80% on repeated system prompt tokens
```

### Pipeline (MVP = sequential, v2 = LangGraph graph)

```
MVP:  analyst_node → copywriter_node → assembler_node
V2:   StateGraph with orchestrator router + parallel execution
```

The shape of agent functions must be LangGraph-compatible from day one:
```python
async def analyst_node(state: AgentState) -> AgentState:
    ...
    return state  # always returns full state
```

---

## Onboarding wizard — 19 steps, 5 sections

### Section A — Who you are (steps 1–4)
| # | Question | Input type |
|---|---|---|
| 1 | Your role | Card select: Coach / Consultant / Agency / Brand / Other |
| 2 | Industry | Card grid + "type your own" text fallback |
| 3 | Brand / business name | Single text input |
| 4 | Your credibility & proof | Textarea: results, years experience, achievements |

### Section B — Your offer (steps 5–9)
| # | Question | Input type |
|---|---|---|
| 5 | Offer name + one-liner | Two text inputs |
| 6 | Price point | Card: <$97 / $97–$997 / $1k–$5k / $5k+ / Custom |
| 7 | What's included | Textarea: deliverables, modules, bonuses |
| 8 | Your unique mechanism | Textarea: "What makes your approach different?" |
| 9 | The transformation | Large textarea: "What does your customer's life look like the day after they buy?" |

### Section C — Your audience (steps 10–13)
| # | Question | Input type |
|---|---|---|
| 10 | Ideal client description | Textarea: conversational framing |
| 11 | Age range | Multi-select pills: 18–24 / 25–34 / 35–44 / 45–54 / 55+ |
| 12 | Biggest pain point | Textarea: "What keeps them up at night?" |
| 13 | Awareness level | Card: Problem-aware / Solution-aware / Offer-aware |

### Section D — Assets & proof (steps 14–16)
| # | Question | Input type |
|---|---|---|
| 14 | Testimonials | Toggle yes/no → if yes: paste up to 3 text testimonials |
| 15 | Assets available | Multi-select: VSL video / Images / Logo / Case studies / None |
| 16 | Guarantee | Card (yes/no) + if yes: type + duration text input |

### Section E — Funnel style (steps 17–19)
| # | Question | Input type |
|---|---|---|
| 17 | Copy style / tonality | Card with example copy snippets (no celebrity names): Bold & Urgent / Calm & Authoritative / Story-driven / Data & Proof / Conversational |
| 18 | Funnel type | Card: VSL Funnel / Lead Magnet Funnel |
| 19 | Theme | AI suggests 2 based on industry + tone. User can pick or browse full list. |

### Onboarding UX requirements
- One question per screen, large 36–40px type
- Framer Motion fade+slide transitions between steps (300ms ease-out)
- Slim progress bar at top showing section name (not step number)
- Section label: "Section 2 of 5 — Your offer" not "Step 6 of 19"
- Dark/near-black background with single accent colour
- Card selectors have hover glow border
- Textareas auto-expand
- Feels like: Typeform × Linear onboarding × prestige agency intake

---

## Builder interface

Two-panel layout (Lovable/Replit style):
- **Left panel (40%):** Chat interface — messages from "Funnel Builder" agent + user input
- **Right panel (60%):** Live preview — step tabs at top, iframe rendering current step HTML

### Builder behaviour
- On first load of a new funnel → generation starts automatically (no user prompt needed)
- SSE stream drives real-time progress messages in chat panel
- Each completed step appears as a chat message with a "Preview" button
- User types to edit: "Make the headline more urgent" → targeted re-run of that step only
- Agent always responds in character as "Funnel Builder"

---

## Build sequence

Follow this order strictly. Do not start Phase N+1 until Phase N is verified and committed.

| Phase | What | Verify before moving on |
|---|---|---|
| 1 | Monorepo skeleton + Next.js + FastAPI + Neon connected | Sign up works, /health 200, DB connected |
| 2 | DB schema migrations + SQLAlchemy models + Clerk webhook | Sign up → user row in Neon |
| 3 | LLMClient + agent nodes + pipeline runner | Python script: dummy offer → HTML files in R2 |
| 4 | Celery + Upstash + generate_funnel task + SSE endpoint | POST /jobs → async run → SSE streams in terminal |
| 5 | Onboarding wizard UI (all 19 steps) | Complete wizard → POST /offers → row in DB |
| 6 | Builder interface (chat + SSE client + preview iframe) | Full flow: wizard → builder → funnel generates live |
| 7 | HTML ZIP export + CF2 OAuth + deploy to Netlify + Render | Download works, CF push works, live URL accessible |

---

## OpenCode session template

Use this at the start of every session:

```
Read PLAN.md and [FRONTEND.md or BACKEND.md] before writing any code.

Today's task: [ONE specific scoped task]

Constraints:
- Only create files inside the structure defined in the plan files
- Do not install packages not in requirements.txt / package.json
- Do not modify files outside the scope of today's task
- [task-specific constraints]

When done: list every file created or modified.
```

---

## Hard constraints for Claude Code (always enforce)

1. Never put agent or LLM logic in route handlers. Routes dispatch jobs. Workers run agents.
2. Always use `LLMClient` abstraction. Never call `anthropic.Anthropic()` directly in agents.
3. Agent functions must always match signature: `async def x(state: AgentState) -> AgentState`
4. Never store HTML in Postgres. HTML → R2. Postgres stores the R2 object key only.
5. Every DB query must filter by both resource `id` AND `user_id`. No exceptions.
6. All user text must be `html.escape()`d before injection into HTML templates.
7. `orchestrator.py` is a stub in MVP. It exists but contains only a `# TODO v2` placeholder.
8. All Anthropic API calls must use `cache_control: ephemeral` on system prompts.
9. SSE endpoint must handle client disconnect: check `await request.is_disconnected()`.
10. Celery tasks must write progress to `jobs.progress` JSONB after each agent stage.
11. Never use `allow_origins=["*"]` in CORS config.
12. Rate limiting middleware must be applied before any generation endpoint.
13. The `offers` table is the top-level container. Funnels belong to offers, not directly to users.