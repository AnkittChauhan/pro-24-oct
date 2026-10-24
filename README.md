# UK Wind Generation Day-Ahead Forecast & Error Quantification Workbench

A specialized full-stack application engineered for UK energy utility trading desks participating in the Day-Ahead wholesale power market. 

This platform enables power procurement traders to:
1. **Simulate Day-Ahead Gate-Closure Decisions**: Locks the latest available wind forecast prior to auction cutoff (e.g. 12:00 UTC on Day $D-1$ for EPEX SPOT) across all 48 settlement periods.
2. **Quantitatively Evaluate Forecast Accuracy**: Calculates standard wholesale power metrics (MAE, RMSE, Directional Bias MBE, and Weighted Absolute Percentage Error WAPE) to size thermal backup generation and avoid imbalance settlement penalties.
3. **Analyze Gate-Closure Lead-Time Sensitivity**: Compare early morning runs (09:00 UTC) against benchmark (12:00 UTC) and afternoon revisions (16:00 UTC) to observe how forecast uncertainty shrinks closer to delivery.

---

## 1. System Architecture

```text
[React 18 + Vite + Recharts Frontend] ◄──► [FastAPI Python Backend] ◄──► [SQLite WAL Cache]
                                                     │
                                                     ▼
                                       [Elexon BMRS Stream API]
```

### Core Components:
- **`ElexonClient`**: High-performance asynchronous HTTP client (`httpx`) streaming half-hourly actual wind generation (`FUELHH`) and day-ahead forecasts (`WINDFOR`) directly from Elexon BMRS datasets.
- **`CacheService`**: Read-through caching layer backed by SQLite with compound indexing and WAL mode for sub-3ms response times and offline resilience.
- **`DayAheadMatcher`**: Simulates the UK wholesale market gate-closure cutoff, mapping the 48 settlement periods of delivery day $D$ to the latest forecast published at or before the decision deadline:
  $$\text{Selected Forecast}(T) = \arg\max_{publishTime \le Cutoff} (\text{publishTime})$$
- **`MetricsEngine`**: Rigorous statistical error engine computing MAE, RMSE, Mean Bias (directional tendency), WAPE, and Net Shortfall/Surplus in MWh.

---

## 2. Directory Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── health.py        # Health check & cache statistics
│   │   │       ├── day_ahead.py     # /day-ahead, /dates, /monthly-summary endpoints
│   │   │       └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic environment configuration
│   │   │   └── __init__.py
│   │   ├── db/
│   │   │   ├── init_db.py           # SQLite WAL connection & schema initialization
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   ├── day_ahead.py         # Pydantic schemas (DayAheadResponse, Metrics)
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── elexon_client.py     # Async HTTP client for Elexon BMRS stream endpoints
│   │   │   ├── cache_service.py     # Read-through cache with SQLite persistence
│   │   │   ├── matcher.py           # Day-ahead gate closure matching engine
│   │   │   ├── metrics.py           # Quantitative error and volume metrics engine
│   │   │   └── __init__.py
│   │   ├── scripts/
│   │   │   └── seed_cache.py        # CLI pre-warming utility for January 2026 dataset
│   │   └── main.py                  # FastAPI application entrypoint & middleware
│   ├── tests/
│   │   ├── test_health.py           # API health tests
│   │   ├── test_elexon_and_cache.py # Read-through cache & cutoff unit tests
│   │   ├── test_matcher_and_metrics.py # Hand-calculated formula verification
│   │   ├── test_day_ahead_api.py    # API contract and route tests
│   │   ├── test_end_to_end_trading_flow.py # Gate-closure lead-time & volume tests
│   │   └── __init__.py
│   ├── .dockerignore
│   ├── Dockerfile                   # Hardened slim Python container (non-root appuser)
│   ├── pytest.ini
│   └── requirements.txt             # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx           # BMRS stream status & cache stats
│   │   │   ├── DateControls.tsx     # Delivery date picker & D-1 cutoff presets
│   │   │   ├── MetricsCards.tsx     # Executive KPI cards (MAE, RMSE, Bias, Shortfall)
│   │   │   ├── ForecastChart.tsx    # 48-period Recharts curve & error deltas
│   │   │   ├── SettlementTable.tsx  # Granular half-hourly table with CSV export
│   │   │   └── MonthlySummaryModal.tsx # January 2026 31-day benchmark report
│   │   ├── services/
│   │   │   └── api.ts               # Axios client for day-ahead API
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript interfaces for API contracts
│   │   ├── App.tsx                  # Primary workbench workbench
│   │   ├── index.css                # TailwindCSS base styles
│   │   ├── main.tsx                 # React DOM mount point
│   │   └── vite-env.d.ts
│   ├── .dockerignore
│   ├── Dockerfile                   # Multi-stage production build (Node -> Nginx)
│   ├── nginx.conf                   # Reverse proxy configuration
│   ├── package.json                 # Frontend dependencies & scripts
│   ├── tailwind.config.js           # Theme styling
│   ├── tsconfig.json
│   ├── vercel.json                  # Vercel deployment configuration
│   └── vite.config.ts               # Vite bundler & API proxy configuration
├── data/                            # Persistent cache storage (cache.db)
├── docker-compose.yml               # Multi-container local orchestration
├── render.yaml                      # Infrastructure-as-Code for Render deployment
└── README.md                        # Documentation
```

---

## 3. How to Start the Application

### Option A: Using Docker Compose (Recommended)
Ensure Docker is running:

```bash
# Build and launch all services in detached mode
docker-compose up --build -d

# Check service health and logs
docker-compose ps
docker-compose logs -f
```

- **Trader Workbench UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Swagger**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

To stop:
```bash
docker-compose down
```

---

### Option B: Local Manual Setup

#### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run full test suite (16 tests)
pytest

# Pre-seed cache with January 2026 data
python -m app.scripts.seed_cache --synthetic --all

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
cd frontend
npm install

# Run automated build check
npm run build

# Start Vite dev server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000).

---

## 4. Cloud Deployment Guide

The platform is architected for zero-configuration deployment across free-tier cloud platforms:

### 1. Backend Deployment (Render / Railway / Fly.io)
- **Render**: Connect the repository and select **New Web Service** with `backend` as the Root Directory. Use the included [`render.yaml`](file:///Users/ankit/dev/my-pro/pro-24-oct/render.yaml) or configure:
  - **Build Command**: `pip install -r requirements.txt && python -m app.scripts.seed_cache --synthetic --all`
  - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - **Health Check Path**: `/health`
- **Output URL**: e.g., `https://uk-wind-backend.onrender.com`

### 2. Frontend Deployment (Vercel)
- Connect repository on Vercel:
  - **Framework Preset**: Vite
  - **Root Directory**: `frontend`
  - **Environment Variables**:
    - `VITE_API_URL`: Set to your deployed backend URL (e.g., `https://uk-wind-backend.onrender.com`).
- The included [`frontend/vercel.json`](file:///Users/ankit/dev/my-pro/pro-24-oct/frontend/vercel.json) handles client-side route rewrites.

### 3. Public Verification in Incognito Mode
1. Open a new Incognito browser window.
2. Navigate to the deployed frontend URL.
3. Verify that the **Live Elexon Stream** status badge shows connected.
4. Toggle delivery dates (e.g. `2026-01-15`) and cutoffs (`09:00`, `12:00`, `16:00`).
5. Open the **January 2026 Monthly Benchmark Report** modal to verify aggregated statistics.
6. Click **Export CSV** to verify client-side data export.

---

## 5. AI Tool Disclosure
In accordance with submission requirements:
AI tooling (Google Antigravity / Gemini) was utilized to assist with rapid scaffolding, boilerplate generation, and verification of statistical formulas. All domain logic, day-ahead matching rules, database schema indexing, and quantitative metrics were authored and reviewed to ensure production software engineering standards.
