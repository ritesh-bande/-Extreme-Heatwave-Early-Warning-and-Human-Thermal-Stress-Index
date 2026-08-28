# Heatwave EWS — Heat Stress & Mortality Risk Early Warning System

A full-stack **ward-level heat risk early warning system** that ingests weather forecasts, computes physiological heat stress indices (WBGT, Heat Index, UTCI), scores ward vulnerability, and dispatches role-specific alerts to construction workers, healthcare, power grid operators, farmers, and the general public.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   Frontend   │────▶│   Backend    │────▶│  PostgreSQL/PostGIS │
│  React/Vite  │     │   FastAPI    │     │  Ward geometries    │
│  Leaflet Map │     │  Uvicorn     │     │  Risk scores        │
│  Port 5173   │     │  Port 8000   │     │  Port 5432          │
└──────────────┘     └──────────────┘     └─────────────────────┘
```

| Service    | Tech Stack                        | Port  |
|------------|-----------------------------------|-------|
| **frontend** | React 18 + Vite + TypeScript + Tailwind + Leaflet | 5173  |
| **backend**  | Python 3.12 + FastAPI + SQLAlchemy + APScheduler   | 8000  |
| **db**       | PostgreSQL 16 + PostGIS 3.4                        | 5432  |

## Quick Start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2+

### Run

```bash
# Clone and start all services
cd heatwave-ews
docker compose up --build
```

Once running:
- **Frontend dashboard**: http://localhost:5173
- **Backend API docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### Environment Variables

Copy and edit `.env` in the project root. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `heatwave` | DB username |
| `POSTGRES_PASSWORD` | `heatwave` | DB password |
| `POSTGRES_DB` | `heatwave_ews` | DB name |
| `DATABASE_URL` | `postgresql://...` | SQLAlchemy connection string |
| `TWILIO_ACCOUNT_SID` | _(empty)_ | Set for real SMS/WhatsApp alerts |
| `TWILIO_AUTH_TOKEN` | _(empty)_ | Set for real SMS/WhatsApp alerts |
| `WEATHER_FETCH_INTERVAL_HOURS` | `3` | Weather ingestion frequency |

### Development

```bash
# Backend only (with auto-reload)
cd backend && uvicorn app.main:app --reload

# Frontend only (with HMR)
cd frontend && npm run dev

# Run backend tests
cd backend && pytest
```

## Project Structure

```
heatwave-ews/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Config, DB engine, shared utilities
│   │   ├── models/       # SQLAlchemy / Pydantic models
│   │   ├── services/     # Business logic (thermal indices, alerts, etc.)
│   │   ├── tasks/        # Background jobs (weather fetch, scheduler)
│   │   └── main.py       # FastAPI application entry point
│   ├── tests/            # pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/              # React components, pages, hooks
│   ├── Dockerfile
│   └── package.json
├── db/
│   └── init.sql          # PostGIS extension + initial schema
├── docker-compose.yml
├── .env                  # Environment variables (not committed in production)
└── README.md
```

## License

Built for SIH (Smart India Hackathon) — Heat Stress & Mortality Risk Early Warning System.
