# Grant Alignment Engine (GAE)

A structured grant preparation application for **Fathers On A Mission (FOAM)** that analyzes uploaded RFPs, maps funder requirements against FOAM's institutional capabilities, and produces compliance-aligned grant frameworks.

This is not a writing assistant. This is a **grant alignment and structuring engine**.

---

## What It Does

1. **Boilerplate Management** — Central database of FOAM's institutional language, organized by program, evidence type, and funding area, with version control and change tracking.
2. **RFP Parsing** — Upload a PDF or DOCX RFP and automatically extract required sections, scoring rubrics, eligibility criteria, word limits, and formatting rules.
3. **Crosswalk Mapping** — Side-by-side alignment of what the funder wants vs. what FOAM can deliver, with gap flags and risk levels.
4. **Grant Plan Generation** — Structured proposal outline with word count targets, suggested FOAM language blocks, compliance checklists, and scoring indicators.
5. **Gap & Risk Dashboard** — Visual dashboard flagging missing metrics, weak alignment, outdated data, missing partnerships, and evaluation weaknesses.
6. **AI Draft Framework** — Structured section outlines and recommended insert blocks (not full narrative writing), anchored in FOAM strengths and RFP language.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, Recharts, Zustand |
| Backend | Python, FastAPI, SQLAlchemy (async), Pydantic v2 |
| Database | PostgreSQL 16 with pg_trgm full-text search |
| AI (optional) | OpenAI / Anthropic Claude API |
| Infrastructure | Docker Compose, Redis |

---

## Project Structure

```
Grant-Template/
├── docker-compose.yml          # Full-stack orchestration
├── .env.example                # Environment config template
├── database/
│   ├── schema.sql              # 13 tables, indexes, views
│   └── seed.sql                # Pre-loaded FOAM institutional data
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic API schemas
│   ├── config.py               # Application settings
│   ├── database.py             # Database connection
│   ├── seed_data.py            # Python-based data seeding
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Backend container
│   ├── services/
│   │   ├── rfp_parser.py       # PDF/DOCX parsing + NLP extraction
│   │   ├── crosswalk_engine.py # RFP-to-boilerplate alignment
│   │   ├── gap_analyzer.py     # Gap detection + risk scoring
│   │   ├── plan_generator.py   # Structured plan creation
│   │   └── ai_service.py       # OpenAI/Claude integration
│   └── routers/
│       ├── boilerplate.py      # Module 1: Boilerplate CRUD
│       ├── rfp.py              # Module 2: RFP upload/parse
│       ├── crosswalk.py        # Module 3: Alignment mapping
│       ├── plans.py            # Module 4: Plan generation
│       ├── dashboard.py        # Module 5: Risk dashboard
│       └── ai_draft.py         # Module 6: AI framework
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── App.jsx             # Routes for all 7 pages
        ├── api/client.js       # Axios API client
        ├── stores/appStore.js  # Zustand state management
        ├── components/         # Layout, Sidebar, Header, shared UI
        └── pages/
            ├── Dashboard.jsx
            ├── BoilerplateManager.jsx
            ├── RFPUpload.jsx
            ├── CrosswalkEngine.jsx
            ├── GrantPlanGenerator.jsx
            ├── GapRiskDashboard.jsx
            └── AIDraftFramework.jsx
```

---

## Quick Start

### With Docker (recommended)

```bash
cp .env.example .env
# Edit .env with your values (API keys are optional)
docker compose up -d
```

Services start at:
- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Database:** localhost:5432

### Without Docker

**Backend:**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python seed_data.py    # Initialize database with FOAM data
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## FOAM Data Pre-loaded

The database ships with real FOAM institutional content:

- **Organization:** Legal name, EIN, UEI, mission, vision, core values
- **Programs:** Project Family Build, Responsible Fatherhood Classes, Celebration of Fatherhood Events, Louisiana Barracks Program
- **Community Data:** EBR Parish demographics, child welfare statistics, poverty data
- **Partnerships:** EnvisionBR, YWCA, DCFS, CAUW, Wilson Foundation, and more
- **Targets:** 140 fathers, ~210 children per grant year
- **Outcome Goals:** 80% stability, 75% pre/post improvement, 70% completion
- **Data Systems:** EmpowerDB, nFORM, SharePoint/Microsoft 365

---

## API Endpoints (40+)

| Module | Prefix | Endpoints |
|--------|--------|-----------|
| Boilerplate | `/api/boilerplate/` | Categories, sections, tags, versions, search, export/import |
| RFP | `/api/rfp/` | Upload, parse, list, requirements, reparse |
| Crosswalk | `/api/crosswalk/` | Generate, matrix, approve, export, summary |
| Plans | `/api/plans/` | Generate, sections, compliance, status workflow, export |
| Dashboard | `/api/dashboard/` | Overview, gaps, risks, recommendations, timeline |
| AI Draft | `/api/ai/` | Outlines, insert blocks, comparisons, justifications |

Full interactive docs at `/docs` when running.

---

## Build Phases

| Phase | Status | Scope |
|-------|--------|-------|
| Phase 1 | Complete | Boilerplate database + RFP parsing engine |
| Phase 2 | Complete | Crosswalk mapping engine |
| Phase 3 | Complete | Risk dashboard + AI structuring |

---

## License

Private — Fathers On A Mission (FOAM)
