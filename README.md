# HEATSHIELD - Extreme Heatwave Early Warning and Human Thermal Stress Index

**Live Demo:** [https://extreme-heatwave-early-warning-and.vercel.app/](https://extreme-heatwave-early-warning-and.vercel.app/)

A full-stack **ward-level heat risk early warning system** that ingests weather forecasts, computes physiological heat stress indices (WBGT, Heat Index, UTCI), scores ward vulnerability, and dispatches role-specific alerts to construction workers, healthcare, power grid operators, farmers, and the general public.


## ?? Smart Weather & Risk Tracking
* **Real-Feel Weather:** It measures how hot it actually feels by including humidity, wind, and sun, not just the basic temperature.
* **True Risk Score:** A 42C day is deadlier in a slum than in a wealthy neighborhood. The app calculates danger based on who lives there (elderly, people without AC, crowded housing).
* **"What-If" Simulator:** Officials can test fake weather scenarios (like dragging a slider to make it hotter) to see what would happen and plan for worst-case emergencies.

## ?? Targeted Alerts (Not Just "It's Hot")
* **Power Grids:** Predicts power blackouts and automatically slows down public EV chargers to prevent electrical fires.
* **Outdoor Workers:** Tells construction sites exactly when to force rest breaks or stop work to keep laborers safe.
* **Hospitals:** Warns local clinics to stock up on IV fluids and prepare for a specific jump in heatstroke patients.
* **Farmers:** Warns farmers when their animals are overheating so they can protect their livestock and milk supply.

## ??? Maps & Emergency Planning
* **Smart Relief Placement:** Automatically figures out the absolute best spots to put emergency cooling centers (like AC buses or water stations) to reach the people who need them most.
* **Visual Dashboard:** A clear satellite map that lets city officials instantly see which neighborhoods are in the most danger.

## ?? Connecting with the Community
* **Custom Advice:** Citizens can log their specific risks (e.g., pregnant, elderly, no AC), and the app sends them personalized survival steps instead of a generic text message.
* **Smarter Over Time:** Hospitals input their actual heatstroke patient numbers, which teaches the app to make better predictions next summer.
* **Voice Calls:** Sends automated voice warnings in local languages so people who cannot read or do not own smartphones still get the message.

## ??? Crash-Proof Tech
* **Never Goes Down:** If the live weather satellite feed breaks or disconnects, the system automatically switches to historical backup data so the dashboard never crashes during a live disaster.

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
