# PrismUX — AI-Powered UX Friction Detector

> **Gemini Live Agent Challenge 2026** — Best of UI Navigators

PrismUX is an autonomous AI agent that navigates real websites like a human user, detects UX friction in real-time, and generates actionable reports — all powered by **Gemini 2.5 Flash multimodal vision**.

Give it any URL + a goal. Watch it perceive, plan, act, and evaluate — narrating its thoughts aloud, playing audio cues, and flagging friction as it goes.

## Highlights at a Glance

| Capability | What It Does |
|-----------|-------------|
| **Multimodal Vision** | Gemini 2.5 Flash analyzes screenshots to detect every interactive element with bounding boxes |
| **PPAE Agent Loop** | Perceive → Plan → Act → Evaluate with confidence gating and grounding verification |
| **DOM + Vision Fusion** | Cross-references Gemini coordinates with Playwright DOM elements in parallel (zero added latency) |
| **Voice Narration** | Agent thoughts narrated via Web Speech API TTS — hear the AI think in real-time |
| **Voice Input** | Speak mid-navigation hints via microphone — guide the agent hands-free |
| **Audio Cues** | Synthesized sound effects per action type (click, scroll, friction, success) via Web Audio API |
| **Persona Testing** | 4 built-in personas + custom builder — each alters navigation behavior and friction detection |
| **7 Friction Categories** | Navigation, contrast, affordance, copy, error, performance, accessibility |
| **AI Stuck Recovery** | 7-level escalating recovery + Gemini-powered intelligent recovery as final fallback |
| **Cookie Consent Handler** | Auto-dismisses banners across main page, iframes, and shadow DOM in 5 languages |
| **Annotated Screenshots** | Downloadable PNGs with friction overlays, severity colors, and improvement suggestions |
| **156 Passing Tests** | Comprehensive coverage: agent core, friction analysis, personas, safety, stuck detection, API |

## Demo

https://github.com/user-attachments/assets/prismux-demo.mp4

> **Try Demo** button pre-fills a purpose-built demo site with deliberate UX friction for instant evaluation.

## How It Works

```
 1. PERCEIVE          2. PLAN              3. ACT               4. EVALUATE
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Screenshot → │   │ Goal-driven  │   │ Playwright   │   │ Before/After │
│ Gemini Flash │──▶│ action pick  │──▶│ executes     │──▶│ comparison   │
│ detects all  │   │ + confidence │   │ click/type/  │   │ via Gemini   │
│ UI elements  │   │ gating @0.65 │   │ scroll/key   │   │ + friction   │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
       │                  │                  │                    │
       ▼                  ▼                  ▼                    ▼
  DOM extraction    Grounding check    Cookie consent      Cross-page memory
  runs in parallel  + DOM fallback     auto-dismiss        + stuck detection
```

Each step streams live via SSE — the frontend shows screenshots, bounding box overlays, reasoning thoughts, and audio feedback in real-time.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  React 19 Frontend  (Vite 7, Tailwind v4, TypeScript)                   │
│  ┌────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ ┌───────┐ ┌──────────┐ │
│  │ Home   │ │ Session │ │ Compare │ │ Report │ │Replay │ │ History  │ │
│  │URL+Goal│ │Live View│ │Personas │ │PDF/CSV │ │Player │ │Dashboard │ │
│  │Personas│ │Audio+Mic│ │Side-by- │ │Annotate│ │Speed  │ │Status    │ │
│  └────────┘ └─────────┘ └─────────┘ └────────┘ └───────┘ └──────────┘ │
│                                                                          │
│  Hooks: useSSE (streaming) · useAudioFeedback (TTS + Web Audio cues)    │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │ SSE (live stream) + REST + Hints API
┌──────────────────────▼───────────────────────────────────────────────────┐
│  FastAPI Backend  (Python 3.11, Pydantic v2)                             │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────┐         │
│  │  NavigatorAgent — Core PPAE Loop                             │         │
│  │  Perceive+Plan → Confidence Gate → Safety → Grounding →     │         │
│  │  DOM Fusion → Act → Cookie Dismiss → Verify → Evaluate →    │         │
│  │  Persona Constraints → Memory Update → Stuck Recovery        │         │
│  └────────────┬──────────────┬──────────────────────────────────┘         │
│               │              │                                            │
│  ┌────────────▼────┐  ┌─────▼──────────┐  ┌──────────────────┐           │
│  │ Gemini 2.5 Flash│  │ Playwright     │  │ Google ADK       │           │
│  │ Vision + JSON   │  │ Chromium       │  │ LoopAgent+Tools  │           │
│  │ + Repair Retry  │  │ + DOM Extract  │  │ Alt Engine       │           │
│  └─────────────────┘  └────────────────┘  └──────────────────┘           │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐      │
│  │ PersonaEngine    │  │ SafetyGuard      │  │ StuckDetector      │      │
│  │ 4 built-in +     │  │ Payment/CAPTCHA/ │  │ URL/action/visual  │      │
│  │ custom builder   │  │ login wall block │  │ 7-level + AI recov │      │
│  └──────────────────┘  └──────────────────┘  └────────────────────┘      │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐      │
│  │ FrictionAnalyzer │  │ PDF Generator    │  │ Cookie Consent     │      │
│  │ 7 categories +   │  │ Branded multi-   │  │ Main + iframes +   │      │
│  │ error classif.   │  │ page reports     │  │ shadow DOM dismiss │      │
│  └──────────────────┘  └──────────────────┘  └────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

## Key Innovation: Multimodal Agent UX

PrismUX goes beyond silent automation. The agent experience is **multimodal for the human operator too**:

- **Voice Narration** — The agent narrates perception and evaluation phases via `speechSynthesis` at 1.3x speed. Hear "I see 12 elements — a product page with pricing cards..." as it navigates.
- **Voice Input** — Click the mic button (or use keyboard) to speak hints mid-navigation: "Try clicking the hamburger menu." Sent via real-time `asyncio.Queue` to the running agent.
- **Audio Cues** — Each action type has a distinct synthesized sound (Web Audio API oscillators): click beep, scroll whoosh, friction alert, success chime. The agent *sounds alive*.
- **Annotated Screenshot Export** — Download PNGs with friction overlays rendered via Canvas API — severity-colored labels, bounding boxes, and improvement suggestions baked into the image.
- **Thought Stream** — Live feed of the agent's internal reasoning: what it sees, what it plans, why it chose that action, and what it thinks happened after.

## Key Innovation: Robust Navigation Intelligence

- **DOM + Vision Fusion** — Playwright DOM extraction runs in parallel with the Gemini vision call (zero latency cost). If Gemini's coordinates miss the target but the label matches a DOM element, coordinates are auto-corrected.
- **Gemini-Powered Stuck Recovery** — When fixed recovery strategies exhaust (scroll → Escape → click outside → go_back → Tab), the agent sends the current screenshot to Gemini and asks: "What should I try to unblock?" Context-aware recovery as a last resort before abandoning.
- **Cookie Consent Auto-Dismissal** — Searches main page, all iframes, and shadow DOM for consent buttons using 20+ button text patterns in 5 languages. Runs on initial page load and after every URL navigation.
- **Structured Output + Repair Retry** — JSON schema enforcement on all Gemini calls. On parse failure, the broken response is sent back with a repair prompt. Exponential backoff with jitter on API errors.
- **Cross-Page Memory** — Tracks visited URLs, successful elements, elements to avoid, and goal progress milestones. Injected into planning prompts so the agent learns from its own history.

## Persona-Based Testing

| Persona | Behavior | Friction Focus |
|---------|----------|---------------|
| **Impatient User** | Picks first CTA, abandons after 3 friction points | Slow loads, confusing navigation |
| **Cautious User** | Reads everything, uses menus, checks security indicators | Missing trust signals, unclear copy |
| **Accessibility-First** | Flags targets <44px, missing ARIA labels, poor contrast | WCAG violations, keyboard traps |
| **Non-Native English** | Confused by jargon/idioms (detects 20+ terms) | Complex copy, ambiguous labels |
| **Custom** | Build your own with traits, focus areas, and free-form instructions | Whatever you define |

Multi-persona comparison runs the same goal with different personas and produces a side-by-side scorecard with category breakdowns.

## Reproducible Testing Instructions

### Prerequisites
- **Docker** and **Docker Compose** (recommended) — OR Python 3.11+ and Node.js 18+
- A **Gemini API key** — get one free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Option A: Docker (one command)

```bash
git clone <repo-url> && cd PrismUX
cp .env.example .env
```

Open `.env` and paste your Gemini API key:
```
GEMINI_API_KEY=your-actual-key-here
```

Then start everything:
```bash
docker-compose up --build
```

This launches three services:
| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | React app — the main UI |
| **Backend API** | http://localhost:8000 | FastAPI + Playwright |
| **Demo Site** | http://localhost:8080 | Purpose-built site with deliberate UX friction |

### Option B: Manual Setup

```bash
# Terminal 1 — Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
export GEMINI_API_KEY=your-actual-key-here
python -m uvicorn main:app --reload
# → http://localhost:8000

# Terminal 2 — Frontend
cd frontend
npm install && npm run dev
# → http://localhost:3000
```

### Step-by-Step Testing Walkthrough

Once the app is running, follow these steps to see every major feature:

#### 1. Quick Demo (2 minutes)
1. Open http://localhost:3000
2. Click **"Try Demo"** — this pre-fills a purpose-built demo site with deliberate UX friction
3. Click **"Start Navigation"**
4. Watch the agent navigate in real-time: live screenshots, bounding box overlays, and the thought stream narrating each PPAE step
5. Enable **voice narration** (speaker icon) to hear the AI think aloud
6. Try sending a **voice hint** (mic icon): say "Try clicking the hamburger menu"
7. Listen for **audio cues** — distinct sounds for clicks, scrolls, friction alerts, and success

#### 2. Real Website Navigation (3 minutes)
1. Go back to the home page
2. Enter any public URL (e.g., `https://vasamuseet.se`) and a goal like "Find ticket prices and opening hours"
3. Select a persona (try **"Accessibility-First User"**)
4. Click **"Start Navigation"** and watch the agent autonomously navigate, dismiss cookie consent banners, and flag friction

#### 3. Persona Comparison (2 minutes)
1. Navigate to **"Compare Personas"** from the home page
2. Enter the same URL and goal
3. Select 2–3 personas to compare
4. View the side-by-side scorecard with category breakdowns and radar chart

#### 4. Reports & Export (1 minute)
1. After any navigation completes, click **"View Report"**
2. Explore the UX Risk Index gauge, severity chart, friction timeline, and annotated screenshots
3. Download the **PDF report** (branded multi-page document) or **CSV export**

#### 5. Session Replay (1 minute)
1. Go to **"Session History"**
2. Click any past session
3. Use the **replay player** to step through the navigation at variable speed

### Automated Test Suite

```bash
# Backend — 156 tests across 14 test files
cd backend && python -m pytest tests/ -v

# Frontend — TypeScript type-check + production build
cd frontend && npx tsc --noEmit && npm run build
```

**What's tested**: ActionExecutor (click, type, scroll, hover, key press, go_back, error handling), Cookie Consent (main page, iframes, shadow DOM, Playwright locator fallback), GeminiVisionService (JSON extraction, code block parsing, perception/action parsing, retry logic, timeout recovery, repair prompt), PDF Generator (valid output, all severity levels, error classification, empty states, large reports), FrictionAnalyzer (categorization, severity, scoring, error classification), PersonaEngine (CRUD, constraints, accessibility, language detection), SafetyGuard (payment, destructive, CAPTCHA, login wall), StuckDetector (loop detection, recovery escalation, screenshot fingerprinting, reset), Navigator API (sessions, hints, capacity, status, steps), Reports (PDF, CSV, JSON), Custom Personas (creation, validation), Health checks.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/sessions` | Create navigation session |
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/{id}` | Get session details |
| POST | `/api/navigate/{id}/start` | Start navigation (SSE stream) |
| POST | `/api/navigate/{id}/start?engine=adk` | Start with ADK engine |
| POST | `/api/navigate/{id}/hint` | Send mid-navigation hint to agent |
| GET | `/api/navigate/{id}/status` | Get navigation status |
| GET | `/api/navigate/{id}/steps` | Get session steps (for replay) |
| GET | `/api/navigate/capacity` | Check browser slot availability |
| GET | `/api/personas` | List available personas |
| POST | `/api/personas/custom` | Create custom persona |
| POST | `/api/personas/compare` | Compare personas on same goal |
| GET | `/api/reports/{id}` | Generate/retrieve friction report |
| GET | `/api/reports/{id}/pdf` | Download branded PDF report |
| GET | `/api/reports/{id}/csv` | Download friction items as CSV |
| GET | `/health` | Health check |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Vision | Gemini 2.5 Flash — multimodal perception, structured JSON, repair retry |
| AI Reports | Gemini 2.5 Pro — executive summaries and improvement priorities |
| AI Recovery | Gemini 2.5 Flash — context-aware stuck recovery from screenshots |
| Agent Framework | Google ADK — LlmAgent + LoopAgent + 8 FunctionTools (alternate engine) |
| Browser | Playwright (Chromium) — headless screenshots, DOM extraction, action execution |
| Backend | FastAPI, Python 3.11, Pydantic v2, asyncio, ReportLab |
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS v4, recharts, Lucide |
| Audio | Web Speech API (TTS + recognition), Web Audio API (synthesized cues) |
| Storage | Cloud Firestore (sessions/reports), Cloud Storage (screenshots) |
| Hosting | Cloud Run, Cloud Build |
| CI/CD | GitHub Actions (pytest + tsc + vite build) |

## Project Structure

```
PrismUX/
├── backend/
│   ├── main.py                               # FastAPI app
│   ├── config.py                             # Settings (env vars)
│   ├── schemas/
│   │   ├── navigation.py                     # NavigationStep, ActionPlan, etc.
│   │   ├── persona.py                        # PersonaConfig, ComparisonRequest
│   │   └── report.py                         # FrictionReport, ErrorClassification
│   ├── routers/
│   │   ├── sessions.py                       # Session CRUD
│   │   ├── navigator.py                      # SSE stream + steps + hint endpoint
│   │   ├── personas.py                       # Persona listing + custom creation
│   │   └── reports.py                        # Report + PDF + CSV export
│   ├── services/
│   │   ├── gemini/client.py                  # Gemini API + structured output + recovery
│   │   ├── gemini/prompts.py                 # All prompt templates (6 prompts)
│   │   ├── browser/manager.py               # Playwright lifecycle + concurrency
│   │   ├── browser/actions.py               # Action executor + cookie consent
│   │   ├── browser/safety.py                # SafetyGuard
│   │   ├── agent/navigator.py               # Core PPAE loop + DOM fusion + hints
│   │   ├── agent/stuck_detector.py          # Loop detection + 7-level recovery
│   │   ├── agent/persona_engine.py          # Persona configs + constraint checks
│   │   ├── agent/adk_agent.py               # ADK FunctionTools + agent graph
│   │   ├── agent/adk_runner.py              # ADK → SSE bridge
│   │   ├── reporting/friction_analyzer.py   # Friction scoring + classification
│   │   ├── reporting/pdf_generator.py       # ReportLab branded PDF
│   │   └── storage/                          # Firestore + GCS clients
│   ├── tests/                                # 156 tests across 14 test files
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                            # Home, Session, Report, Replay, History, Comparison, Architecture
│   │   ├── components/navigator/            # OverlayCanvas, ThoughtStream, ScreenshotViewer, SessionReplay
│   │   ├── components/personas/             # PersonaSelector, PersonaScorecard, CustomPersonaBuilder
│   │   ├── components/report/               # FrictionGauge, SeverityChart, StepTimeline, AnnotatedScreenshots, ComparisonRadar
│   │   ├── components/ui/                   # Layout, ArchitectureDiagram
│   │   ├── hooks/useSSE.ts                  # SSE streaming + thought events
│   │   ├── hooks/useAudioFeedback.ts        # TTS narration + Web Audio cues
│   │   └── types/                            # TypeScript types (strict unions + Speech API)
│   └── Dockerfile
├── demo-site/                                # Purpose-built site with deliberate UX friction
├── infrastructure/
│   ├── deploy.sh                             # GCP deployment script
│   └── cloudbuild.yaml                       # CI/CD pipeline
├── .github/workflows/ci.yml                  # GitHub Actions CI
└── docker-compose.yml                        # Backend + frontend + demo-site
```

## License

MIT
