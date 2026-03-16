# PrismUX — AI-Powered UI Navigator Agent

PrismUX is an autonomous AI agent that navigates real websites using **Gemini 2.0 Flash multimodal vision**, simulates diverse user personas, and generates actionable friction reports — identifying usability issues before real users encounter them.

Built for the **Gemini Live Agent Challenge** hackathon (Best of UI Navigators).

## What It Does

1. **Point it at any website** with a goal (e.g., "Find the pricing page and sign up for a free trial")
2. **Watch the AI navigate in real-time** — screenshots, reasoning, and detected elements stream live via SSE
3. **The agent detects UX friction** as it navigates — confusing labels, small targets, low contrast, slow loads
4. **Get a polished report** with severity-ranked issues, improvement suggestions, and a downloadable PDF

## Demo

https://github.com/user-attachments/assets/prismux-demo.mp4

> **Try Demo** button pre-fills a purpose-built demo site with deliberate UX friction for instant evaluation.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  React 19 Frontend  (Vite 7, Tailwind v4, TypeScript)                   │
│  ┌────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ ┌───────┐ ┌──────────┐ │
│  │ Home   │ │ Session │ │ Compare │ │ Report │ │Replay │ │ History  │ │
│  │URL+Goal│ │Live View│ │Personas │ │PDF/CSV │ │Player │ │Dashboard │ │
│  └────────┘ └─────────┘ └─────────┘ └────────┘ └───────┘ └──────────┘ │
│                                                                          │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │ SSE (live stream) + REST
┌──────────────────────▼───────────────────────────────────────────────────┐
│  FastAPI Backend  (Python 3.11, Pydantic v2)                             │
│                                                                          │
│  ┌─────────────────────────────────────────────────────┐                 │
│  │  NavigatorAgent — Core PPAE Loop                     │                 │
│  │  Perceive+Plan → Confidence Gate → Safety Check →    │                 │
│  │  Grounding → Act → Verify → Evaluate → Memory Update │                 │
│  └────────────┬──────────────┬──────────────────────────┘                 │
│               │              │                                            │
│  ┌────────────▼────┐  ┌─────▼──────────┐  ┌──────────────────┐           │
│  │ Gemini 2.0 Flash│  │ Playwright     │  │ Google ADK       │           │
│  │ (Vision API)    │  │ (Chromium)     │  │ (Alt Engine)     │           │
│  │ Structured JSON │  │ Screenshots    │  │ LoopAgent+Tools  │           │
│  └─────────────────┘  └────────────────┘  └──────────────────┘           │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐      │
│  │ PersonaEngine    │  │ SafetyGuard      │  │ StuckDetector      │      │
│  │ 4 built-in +     │  │ Payment/CAPTCHA/ │  │ URL/action/visual  │      │
│  │ custom builder   │  │ login wall block │  │ loop detection     │      │
│  └──────────────────┘  └──────────────────┘  └────────────────────┘      │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐      │
│  │ FrictionAnalyzer │  │ PDF Generator    │  │ Firestore + GCS    │      │
│  │ 7 categories +   │  │ ReportLab multi- │  │ Sessions, reports, │      │
│  │ error classif.   │  │ page branded PDF │  │ screenshots        │      │
│  └──────────────────┘  └──────────────────┘  └────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

## Key Features

### Navigation Intelligence
- **PPAE loop** (Perceive-Plan-Act-Evaluate) — 2 Gemini API calls per step with structured JSON output
- **Confidence gating** at 0.65 threshold — low-confidence actions trigger re-perception via scroll
- **Grounding validation** — cross-checks vision coordinates against DOM, falls back to text search
- **Action verification** — compares pre/post-click state to confirm actions had effect
- **Cross-page memory** — tracks visited URLs, successful elements, avoid list, goal progress across pages
- **Stuck detection** with escalating recovery: scroll down → scroll up → Escape → click outside → go back → Tab → abandon

### Google ADK Integration
- Alternative navigation engine using `google-adk` LlmAgent + LoopAgent
- 8 FunctionTools wrapping Playwright actions (click, type, scroll, screenshot, etc.)
- Activated via `?engine=adk` query parameter
- Task-local page reference via `contextvars` for safe concurrent sessions

### Persona System
- **4 built-in personas** that alter actual navigation behavior:
  - **Impatient User** — picks first CTA, abandons after 3 friction points
  - **Cautious User** — reads all text, uses nav menus, checks security
  - **Accessibility-First** — flags small targets (<44px), missing ARIA, poor contrast
  - **Non-Native English** — confused by jargon/idioms (detects 20+ terms)
- **Custom Persona Builder** — create personas with traits, focus areas, and custom instructions
- **Multi-persona comparison** — side-by-side scorecard with category breakdown

### Friction Detection
- **7 friction categories**: navigation, contrast, affordance, copy, error, performance, accessibility
- **4 severity levels**: low, medium, high, critical
- **Error classification**: network, timeout, blocked, login_wall, safety, unknown
- **Severity-weighted scoring** with abandonment boost

### Safety & Security
- **SafetyGuard** blocks: payment flows, destructive actions, CAPTCHAs, login walls
- Pattern matching on URL, target element, reasoning, and page text
- Automatic session termination with "blocked" status

### Reports & Export
- **Branded PDF reports** via ReportLab — cover page, executive summary, friction table, step timeline
- **CSV export** of friction items
- **JSON API** for programmatic access
- **Executive summary** and **improvement priorities** generated by Gemini

### Live Experience
- **Real-time thought stream** — see the agent's Perceive → Plan → Act → Evaluate reasoning live
- **Candidate element overlay** — chosen element (solid bbox) + alternatives (dashed) with confidence
- **Pre-click pulse animation** — visual indicator before each action
- **Spatial friction markers** — pulsing circles at coordinates where friction was detected
- **Session replay** — step-by-step playback with speed control and reasoning narration
- **Session history** — dashboard of all past sessions with status, replay, and report links

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- A [Gemini API key](https://aistudio.google.com/apikey)

### 1. Clone and configure

```bash
git clone <repo-url> && cd PrismUX
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn main:app --reload
```

Backend at http://localhost:8000 — API docs at http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend at http://localhost:3000 (proxies API to backend)

### Docker (recommended)

```bash
# Set GEMINI_API_KEY in .env
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Demo site: http://localhost:8080

## Testing

```bash
# Backend (88 tests)
cd backend && python -m pytest tests/ -v

# Frontend type-check + build
cd frontend && npx tsc --noEmit && npm run build
```

Test coverage includes: FrictionAnalyzer (categorization, severity, scoring, error classification), PersonaEngine (CRUD, constraints, accessibility, language), SafetyGuard (payment, destructive, captcha, login wall), StuckDetector (loop detection, recovery escalation), API endpoints (sessions, personas, reports, custom personas, CSV export).

## GCP Deployment

```bash
cd infrastructure
./deploy.sh YOUR_PROJECT_ID us-central1
```

Deploys to Cloud Run with:
- 2Gi memory, 2 CPU
- Concurrency: 1 (avoids Playwright contention)
- Min instances: 1 (avoids cold start)
- 300s request timeout

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/sessions` | Create navigation session |
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/{id}` | Get session details |
| POST | `/api/navigate/{id}/start` | Start navigation (SSE stream) |
| POST | `/api/navigate/{id}/start?engine=adk` | Start with ADK engine |
| GET | `/api/navigate/{id}/status` | Get navigation status |
| GET | `/api/navigate/{id}/steps` | Get completed session steps (replay) |
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
| AI (navigation) | Google Gemini 2.0 Flash — multimodal vision, structured JSON output |
| AI (reports) | Gemini 2.5 Pro — deeper friction analysis |
| AI (ADK) | Google Agent Development Kit — LlmAgent + LoopAgent + FunctionTools |
| Browser | Playwright (Chromium) — headless screenshot + action execution |
| Backend | FastAPI, Python 3.11, Pydantic v2, ReportLab |
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS v4, recharts |
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
│   │   ├── navigator.py                      # SSE stream + steps endpoint
│   │   ├── personas.py                       # Persona listing + custom creation
│   │   └── reports.py                        # Report + PDF + CSV export
│   ├── services/
│   │   ├── gemini/client.py                  # Gemini API + structured output
│   │   ├── gemini/prompts.py                 # All prompt templates
│   │   ├── browser/manager.py               # Playwright lifecycle + concurrency
│   │   ├── browser/actions.py               # Action executor
│   │   ├── browser/safety.py                # SafetyGuard
│   │   ├── agent/navigator.py               # Core PPAE loop
│   │   ├── agent/stuck_detector.py          # Loop detection + recovery
│   │   ├── agent/persona_engine.py          # Persona configs + constraint checks
│   │   ├── agent/adk_agent.py               # ADK FunctionTools + agent graph
│   │   ├── agent/adk_runner.py              # ADK → SSE bridge
│   │   ├── reporting/friction_analyzer.py   # Friction scoring + classification
│   │   ├── reporting/pdf_generator.py       # ReportLab PDF generation
│   │   └── storage/                          # Firestore + GCS clients
│   ├── tests/                                # 88 tests across 12 files
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                            # Home, Session, Report, Replay, History, Comparison, Architecture, NotFound
│   │   ├── components/navigator/            # OverlayCanvas, ReasoningPanel, ThoughtStream, SessionReplay, ScreenshotViewer
│   │   ├── components/personas/             # PersonaSelector, PersonaScorecard, CustomPersonaBuilder
│   │   ├── components/report/               # FrictionHeatmap, SeverityChart, StepTimeline, AccessibilityBadge
│   │   ├── components/ui/                   # Layout, ArchitectureDiagram
│   │   ├── hooks/useSSE.ts                  # SSE streaming + thought events
│   │   └── types/navigation.ts              # TypeScript types (strict unions)
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
