# Black-Scholes Research Platform

## Project Overview
A full-stack research system for evaluating Black-Scholes numerical methods (FDM, Monte Carlo, Binomial Trees). Developed for the MATH499 senior research project at the University of Eastern Africa, Baraton.
 
- **Researcher**: Joseph Kamau Maina (SJOSKA2211)
- **Frontend**: Next.js 14 App Router (Vercel)
- **Backend**: FastAPI 0.111 (Docker)
- **Database**: Supabase PostgreSQL 15
- **Observability**: Prometheus + Grafana
- **Notifications**: Resend + Web Push + Realtime
 
## System Architecture
The platform follows a modern microservices architecture with a focus on observability and research accuracy:
1. **Frontend**: Framer Motion animations, Realtime data feeds, and interactive pricer.
2. **Backend**: 12 numerical method implementations with Prometheus instrumentation.
3. **Database**: Supabase with RLS and Realtime enabled on all 9 tables.
4. **Observability**: Prometheus scrapes the backend every 15s; Grafana provides 4 research dashboards.
 
## Repository Structure
```text
SJOSKA2211/black-scholes-comparison/
├── apps/
│   ├── web/           # Next.js 14 Frontend
│   └── api/           # FastAPI Backend + Docker + Prometheus/Grafana
├── supabase/
│   └── migrations/    # Database schema
└── .github/
    └── workflows/     # CI/CD (Lint, Unit, Integration, E2E, Deploy)
```
 
## Getting Started
 
### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
 
### Local Setup
1. **Clone and Install**:
   ```bash
   git clone https://github.com/SJOSKA2211/black-scholes-comparison.git
   cd black-scholes-comparison
   cd apps/api && pip install -r requirements.txt
   cd ../web && npm install
   ```
 
2. **Configure Environment**:
   Copy `.env.example` files to `.env` in `apps/api` and `apps/web/src` and fill in the required keys (Supabase, Resend, etc.).
 
3. **Start the Stack**:
   ```bash
   cd apps/api
   docker-compose up --build
   ```
 
4. **Run Frontend**:
   ```bash
   cd apps/web
   npm run dev
   ```
 
## Verification
- **Health Check**: `curl http://localhost:8000/health`
- **Metrics**: `http://localhost:8000/metrics`
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3001`
 
## Research Methods
- **Analytical**: Black-Scholes Closed Form
- **FDM**: Explicit, Implicit, Crank-Nicolson
- **Monte Carlo**: Standard, Antithetic, Control Variate, Quasi (Sobol)
- **Trees**: Binomial (CRR), Trinomial, and Richardson Extrapolation variants
 
---
*MATH499 Senior Research · UEAB · SJOSKA2211*


