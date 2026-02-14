# Grant Alignment Engine - Backend API

A production-quality FastAPI backend for the Grant Alignment Engine, providing AI-powered grant alignment and compliance analysis for FOAM.

## Overview

The Grant Alignment Engine backend is a comprehensive system for:
- Managing Request for Proposal (RFP) documents
- Creating and versioning boilerplate content
- Analyzing alignment between RFP requirements and organizational content
- Generating gap analyses and risk assessments
- Supporting grant application planning and compliance tracking

## Technology Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with bcrypt
- **Task Queue**: Celery with Redis
- **AI Integration**: OpenAI & Anthropic APIs
- **NLP**: spaCy, scikit-learn, NLTK
- **Document Processing**: pdfplumber, python-docx, pytesseract
- **Testing**: pytest with async support

## Project Structure

```
backend/
├── config.py              # Settings and configuration management
├── database.py            # SQLAlchemy async setup
├── models.py              # ORM models
├── schemas.py             # Pydantic v2 schemas
├── main.py               # FastAPI application entry point
├── seed_data.py          # Database initialization script
├── requirements.txt      # Python dependencies
├── .env.example          # Environment configuration template
└── routers/              # API route handlers (to be created)
    ├── boilerplate.py
    ├── rfp.py
    ├── crosswalk.py
    ├── grant_plan.py
    ├── gap_analysis.py
    ├── user.py
    └── dashboard.py
```

## Setup & Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional, for containerized development)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Initialize Database

```bash
# Create tables and seed with FOAM institutional data
python seed_data.py
```

### 4. Run Development Server

```bash
python main.py
# OR
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

API Documentation:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Using Docker Compose

### Quick Start with Docker

```bash
docker-compose up -d
```

This will start:
- FastAPI application (port 8000)
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- pgAdmin (port 5050) - optional database management

### Seed Database in Docker

```bash
docker-compose exec api python seed_data.py
```

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /api/v1/status` - API status

### Boilerplate Content
- `GET /api/v1/boilerplate/categories` - List categories
- `GET /api/v1/boilerplate/sections` - List sections
- `POST /api/v1/boilerplate/sections` - Create section
- `PUT /api/v1/boilerplate/sections/{id}` - Update section

### RFP Management
- `GET /api/v1/rfps` - List RFPs
- `POST /api/v1/rfps/upload` - Upload RFP document
- `GET /api/v1/rfps/{id}` - Get RFP details
- `GET /api/v1/rfps/{id}/requirements` - Get RFP requirements

### Alignment & Crosswalk
- `GET /api/v1/crosswalks` - List crosswalk maps
- `POST /api/v1/crosswalks` - Create mapping
- `GET /api/v1/crosswalks/rfp/{rfp_id}` - Get RFP alignment matrix

### Grant Planning
- `GET /api/v1/grant-plans` - List plans
- `POST /api/v1/grant-plans` - Create plan
- `GET /api/v1/grant-plans/{id}` - Get plan details
- `PUT /api/v1/grant-plans/{id}` - Update plan

### Gap Analysis
- `GET /api/v1/gap-analyses` - List analyses
- `POST /api/v1/gap-analyses` - Generate analysis
- `GET /api/v1/gap-analyses/{id}` - Get analysis details

### User Management
- `POST /api/v1/users/register` - Register user
- `POST /api/v1/users/login` - Login
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users` - List users (admin only)

### Dashboard
- `GET /api/v1/dashboard/summary` - Dashboard overview

## Database Models

### Core Entities

**BoilerplateCategory**
- Organizational Capacity
- Program Design & Implementation
- Evaluation & Outcomes
- Compliance & Sustainability

**BoilerplateSection**
- Versioned content sections
- Program-specific content
- Compliance relevance tracking
- Evidence type classification

**RFP**
- Document metadata
- Status tracking
- Extracted text and requirements
- Deadline and funding information

**RFPRequirement**
- Parsed requirements from RFPs
- Word limits and scoring weights
- Formatting and eligibility notes

**CrosswalkMap**
- Alignment between RFP requirements and boilerplate
- Risk assessment
- Gap identification
- Customization tracking

**GrantPlan**
- Multi-section grant applications
- Status workflow (draft → submitted)
- Compliance scoring
- Flexible metadata storage

**GapAnalysis**
- Comprehensive gap assessments
- Risk-level categorization
- Recommendations
- Missing metrics and partnerships

**User & AuditLog**
- Role-based access control
- Complete audit trail
- Change tracking

## Data Models

### Enumerations

**RFPStatusEnum**: uploaded, parsing, parsed, analyzed, archived

**AlignmentScoreEnum**: strong, partial, weak, none

**RiskLevelEnum**: green, yellow, red

**FundingTypeEnum**: federal, state, foundation, corporate, other

**UserRoleEnum**: admin, grant_manager, reviewer, viewer

**EvidenceTypeEnum**: quantitative, qualitative, mixed_methods, evaluation, research

**TagTypeEnum**: program, funding_type, evidence, priority_area, outcome, metric

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

```bash
# Login
POST /api/v1/users/login
{
  "email": "user@example.com",
  "password": "password"
}

# Response
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "expires_in": 86400
}

# Use token in Authorization header
Authorization: Bearer eyJ0eXAi...
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key configurations:
- `ENVIRONMENT`: development, staging, production
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Secret key for JWT signing (change in production!)
- `OPENAI_API_KEY`: OpenAI API key for NLP analysis
- `ANTHROPIC_API_KEY`: Anthropic API key for content generation
- `REDIS_URL`: Redis cache connection

### Production Deployment

For production deployment:

1. Set `ENVIRONMENT=production`
2. Set `DEBUG=false`
3. Use strong `JWT_SECRET_KEY` (32+ characters)
4. Configure `CORS_ORIGINS` to allowed domains only
5. Use environment-specific `.env` file (never commit to repo)
6. Enable TrustedHost middleware
7. Use HTTPS/SSL
8. Configure database backups
9. Set up monitoring and logging
10. Use secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.)

## Seed Data

The `seed_data.py` script initializes the database with FOAM institutional data:

```bash
python seed_data.py
```

This creates:
- 4 boilerplate categories with 15+ sections
- FOAM organizational and program content
- Tags for programs, funding types, evidence, outcomes
- Default admin, manager, and reviewer users

Default user credentials (CHANGE IMMEDIATELY IN PRODUCTION):
- admin@foamgrants.org
- manager@foamgrants.org
- reviewer@foamgrants.org
- Password: ChangeMe123!

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run async tests
pytest -v -k async
```

## Development Workflow

### Database Migrations (Alembic)

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black .

# Lint
pylint routers/

# Type checking
mypy .
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
psql -h localhost -U foam_user -d foam_grants

# Reset database (development only)
python -c "
import asyncio
from database import db_manager
asyncio.run(db_manager.initialize())
asyncio.run(db_manager.drop_all_tables())
asyncio.run(db_manager.create_all_tables())
"
```

### Missing Dependencies

```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Flush cache (development only)
redis-cli FLUSHALL
```

## API Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "data": {},
  "message": "Operation successful",
  "status": "success"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "error": "Detailed error description",
  "status": "error",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Paginated Response
```json
{
  "total": 100,
  "skip": 0,
  "limit": 20,
  "items": []
}
```

## FOAM Organization Info

**Organization**: FOAM (501(c)(3))
**Location**: East Baton Rouge Parish, Louisiana
**Founded**: 2017
**EIN**: 82-2374110

**Programs**:
- Project Family Build
- Responsible Fatherhood Classes
- Celebration of Fatherhood Events
- Louisiana Barracks Program

**Annual Targets**: 140 fathers, ~210 children

**Data Systems**: EmpowerDB, nFORM

## Support & Documentation

- API Documentation: `/api/docs`
- ReDoc: `/api/redoc`
- Health Check: `/health`

## License

Copyright FOAM. All rights reserved.

## Contact

For questions or issues, contact the development team.
