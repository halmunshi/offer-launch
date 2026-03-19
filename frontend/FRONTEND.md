# OfferLaunch — FRONTEND.md
> Read PLAN.md first, then this file. This covers frontend-specific implementation details.
> Stack: Next.js 14 (App Router) · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion · Clerk

---

## Folder structure

```
frontend/
├── app/
│   ├── layout.tsx                    # Root layout — ClerkProvider, fonts
│   ├── (auth)/
│   │   ├── sign-in/[[...sign-in]]/page.tsx
│   │   └── sign-up/[[...sign-up]]/page.tsx
│   ├── (app)/                        # Protected routes (middleware enforces auth)
│   │   ├── layout.tsx                # App shell layout
│   │   ├── dashboard/
│   │   │   └── page.tsx              # List user's offers + funnels
│   │   ├── onboarding/
│   │   │   └── page.tsx              # 19-step wizard (client component)
│   │   └── builder/
│   │       └── [funnelId]/
│   │           └── page.tsx          # Builder interface
│   └── api/
│       └── webhooks/
│           └── clerk/route.ts        # Clerk webhook handler
├── components/
│   ├── onboarding/
│   │   ├── OnboardingWizard.tsx      # Wizard shell + step router
│   │   ├── WizardProgress.tsx        # Section progress bar
│   │   └── steps/                   # One component per step (Step01Role.tsx ... Step19Theme.tsx)
│   ├── builder/
│   │   ├── BuilderLayout.tsx         # Two-panel container
│   │   ├── ChatPanel.tsx             # Message list + input
│   │   ├── ChatMessage.tsx           # Individual message bubble
│   │   ├── PreviewPanel.tsx          # Step tabs + iframe
│   │   ├── StepTabs.tsx              # Tab nav between funnel steps
│   │   └── ExportMenu.tsx            # Export dropdown
│   └── ui/                           # shadcn/ui components (auto-generated)
├── lib/
│   ├── api.ts                        # Typed fetch wrapper → backend API
│   ├── sse.ts                        # useSSE hook for streaming job progress
│   ├── types.ts                      # Shared TypeScript interfaces
│   └── utils.ts                      # cn() and other helpers
├── hooks/
│   ├── useOnboarding.ts              # Wizard state machine (current step, answers, navigation)
│   └── useBuilder.ts                 # Builder state (messages, current step preview)
├── middleware.ts                     # Clerk auth — protect (app) routes
└── .env.local                        # Local env vars (never commit)
```

---

## Key implementation details

### Auth (Clerk)
- Wrap root layout with `<ClerkProvider>`
- `middleware.ts` protects all routes under `/(app)/` using `clerkMiddleware()`
- After sign-up, Clerk fires webhook → backend creates user row → redirect to `/onboarding`
- Use `useAuth()` to get `getToken()` — pass JWT as `Authorization: Bearer` on all API calls

### API calls (`lib/api.ts`)
Every call to the FastAPI backend must:
1. Get the Clerk JWT via `getToken()`
2. Set `Authorization: Bearer {token}` header
3. Set `Content-Type: application/json`
4. Handle 401/403 by redirecting to sign-in

```typescript
// Pattern for all API calls
const { getToken } = useAuth()
const token = await getToken()
const res = await api.post('/offers', body, token)
```

### SSE streaming (`lib/sse.ts` + `hooks/useBuilder.ts`)
- Use `EventSource` API to connect to `GET {API_URL}/jobs/{jobId}/stream`
- SSE events contain progress JSON: `{ stage, message, ts, done, status }`
- On each event: append message to chat panel, update step status
- On `status: "done"`: mark generation complete, load preview URLs
- On `status: "error"`: show error message in chat

```typescript
// useSSE hook signature
function useSSE(jobId: string, onMessage: (data: ProgressEvent) => void): void
```

### Onboarding wizard

**State management:** use `useOnboarding` hook with `useReducer` — tracks current step index,
all answers so far, and navigation (next/back). Answers accumulate in a single `IntakeData` object.

**Animation:** Framer Motion `AnimatePresence` + `motion.div` on each step.
- Enter: `{ opacity: 0, x: 40 }` → `{ opacity: 1, x: 0 }` — 300ms ease-out
- Exit: `{ opacity: 0, x: -40 }` — 200ms

**Validation:** Each step has a `isValid(answers)` function. Next button disabled until valid.
Use `react-hook-form` for text inputs with Zod schemas.

**On completion:** POST to `POST /api/offers` with full `IntakeData`.
Response contains `{ offer_id, funnel_id, job_id }`.
Redirect to `/builder/{funnel_id}?jobId={job_id}`.

**Design spec:**
- Background: `#0a0a0a` (near black)
- Accent: `#6366f1` (indigo-500) — used for active states, progress bar, CTAs
- Text: `#f8fafc` (slate-50) primary, `#94a3b8` (slate-400) secondary
- Question text: 36px, font-weight 500, line-height 1.2
- Card selectors: `border: 1px solid #1e293b`, hover: `border-color: #6366f1` + subtle glow
- Progress bar: slim 2px line at very top, indigo fill, section label below

### Builder interface

**Layout:**
```
[Header: logo + funnel name + export button]
[Left 40% | Right 60%]
Left:  chat messages (scrollable) + input bar pinned to bottom
Right: step tabs row + iframe filling remaining height
```

**Chat messages:**
- Agent messages: left-aligned, small avatar circle with "FB" initials (Funnel Builder)
- User messages: right-aligned, subtle background
- Progress messages: center-aligned, muted, with spinner during generation
- Each completed step message has a "Preview step →" button that switches the right panel tab

**iframe preview:**
- `src` = R2 public URL of the HTML page
- `sandbox="allow-same-origin allow-scripts"` — allow scripts for interactive elements
- Add CSP header on the preview route: `Content-Security-Policy: default-src 'self' 'unsafe-inline' fonts.googleapis.com`
- Show skeleton loader while iframe loads

### TypeScript types (`lib/types.ts`)

```typescript
interface Offer {
  id: string
  name: string
  status: string
  intakeData: IntakeData
  funnels: Funnel[]
  createdAt: string
}

interface Funnel {
  id: string
  offerId: string
  name: string
  funnelType: 'vsl' | 'lead_magnet'
  theme: string
  status: 'draft' | 'generating' | 'ready' | 'error'
  steps: FunnelStep[]
}

interface FunnelStep {
  id: string
  stepOrder: number
  stepType: string
  htmlUrl: string | null
  slug: string
}

interface Job {
  id: string
  funnelId: string
  status: 'pending' | 'running' | 'done' | 'error'
  progress: ProgressEvent[]
}

interface ProgressEvent {
  stage: string
  message: string
  ts: string
  done: boolean
}

interface IntakeData {
  // Section A
  role: string
  industry: string
  brandName: string
  credibility: string
  // Section B
  offerName: string
  offerOneLiner: string
  pricePoint: string
  whatsIncluded: string
  uniqueMechanism: string
  transformation: string
  // Section C
  idealClient: string
  ageRanges: string[]
  painPoint: string
  awarenessLevel: string
  // Section D
  hasTestimonials: boolean
  testimonials: string[]
  assets: string[]
  hasGuarantee: boolean
  guaranteeType: string
  guaranteeDuration: string
  // Section E
  copyStyle: string
  funnelType: 'vsl' | 'lead_magnet'
  theme: string
}
```

---

## Environment variables

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000          # → https://offerlaunch-api.onrender.com in prod
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=whsec_...
```

---

## Netlify deployment

1. Connect GitHub repo to Netlify
2. Build command: `cd frontend && npm run build`
3. Publish directory: `frontend/.next`
4. Add all env vars in Netlify dashboard (Settings → Environment variables)
5. Add `frontend/netlify.toml`:

```toml
[build]
  command = "npm run build"
  publish = ".next"

[[plugins]]
  package = "@netlify/plugin-nextjs"
```

---

## Package list (do not add packages not in this list without updating PLAN.md)

```json
{
  "dependencies": {
    "next": "14.x",
    "react": "18.x",
    "react-dom": "18.x",
    "typescript": "5.x",
    "@clerk/nextjs": "latest",
    "tailwindcss": "3.x",
    "framer-motion": "11.x",
    "react-hook-form": "7.x",
    "zod": "3.x",
    "@hookform/resolvers": "3.x",
    "lucide-react": "latest",
    "clsx": "latest",
    "tailwind-merge": "latest"
  }
}
```

shadcn/ui components are added via CLI (`npx shadcn-ui@latest add [component]`) as needed.