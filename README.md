# UK Wind Generation Day-Ahead Forecast & Error Quantification Workbench

A specialized full-stack application engineered for UK energy utility trading desks participating in the Day-Ahead wholesale power market. 

This platform enables power procurement traders to:
1. **Visualize the latest available wind forecasts** prior to the Day-Ahead gate closure (e.g., 12:00 UTC on Day $D-1$) to balance renewable generation with thermal plant procurement.
2. **Quantitatively evaluate forecast accuracy** using standard industry metrics (MAE, RMSE, Mean Bias Error, and WAPE) to size risk buffers and minimize imbalance settlement penalties.

---

## 1. System Architecture

```
[React + Vite + Recharts Frontend] ◄──► [FastAPI Python Backend] ◄──► [Read-Through SQLite Cache]
                                                    │
                                                    ▼
                                      [Elexon BMRS Stream API]
```

### Key Modules:
- **`ElexonClient`**: High-performance asynchronous HTTP client (`httpx`) streaming half-hourly actuals (`FUELHH`, wind fuel type) and forecasts (`WINDFOR`) directly from Elexon BMRS.
- **`CacheService`**: Read-through caching layer backed by SQLite with compound indexing to ensure sub-millisecond response times.
- **`DayAheadMatcher`**: Simulates the UK wholesale market gate-closure cutoff, mapping the 48 settlement periods of delivery day $D$ to the latest forecast published at or before the decision deadline.
- **`MetricsEngine`**: Rigorous statistical error engine computing MAE, RMSE, Mean Bias (directional tendency), and Net Procurement Shortfall (MWh).

---

## 2. Directory Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── health.py        # Health check & cache statistics
│   │   │       └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic environment configuration
│   │   │   └── __init__.py
│   │   ├── db/
│   │   │   ├── init_db.py           # SQLite WAL connection & schema initialization
│   │   │   └── __init__.py
│   │   ├── models/                  # Pydantic schemas (DayAheadResponse, Metrics)
│   │   ├── services/
│   │   │   ├── elexon_client.py     # Async HTTP client for Elexon BMRS stream endpoints
│   │   │   ├── cache_service.py     # Read-through cache with SQLite persistence
│   │   │   └── __init__.py
│   │   ├── scripts/
│   │   │   └── seed_cache.py        # CLI tool to pre-warm cache for January 2026
│   │   └── main.py                  # FastAPI application entrypoint & middleware
│   ├── tests/
│   │   ├── test_health.py           # API health tests
│   │   ├── test_elexon_and_cache.py # Cache-aside & Elexon stream unit tests
│   │   └── __init__.py
│   ├── Dockerfile                   # Python container configuration
│   └── requirements.txt             # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/              # Modular UI components (Header, Charts, Table)
│   │   ├── services/
│   │   │   └── api.ts               # Axios HTTP client
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript interfaces for API contracts
│   │   ├── App.tsx                  # Primary workbench view
│   │   ├── index.css                # TailwindCSS base styles
│   │   └── main.tsx                 # React DOM mount point
│   ├── Dockerfile                   # Multi-stage production build (Node -> Nginx)
│   ├── nginx.conf                   # Reverse proxy configuration
│   ├── package.json                 # Frontend dependencies & scripts
│   ├── tailwind.config.js           # Theme styling
│   └── vite.config.ts               # Vite bundler & API proxy configuration
├── data/                            # Persistent cache storage (.gitkeep)
├── docker-compose.yml               # Multi-container orchestration
├── .gitignore                       # Repository ignore rules
└── README.md                        # Documentation
```

---

## 3. How to Start the Application

### Option A: Using Docker Compose (Recommended)
Ensure Docker and Docker Compose are installed and running:

```bash
# Build and launch all services in detached mode
docker-compose up --build -d

# Verify services are running
docker-compose ps
```

- **Frontend Workbench**: Accessible at [http://localhost:3000](http://localhost:3000)
- **Backend API Docs (Swagger UI)**: Accessible at [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

To stop the containers:
```bash
docker-compose down
```

---

### Option B: Local Manual Setup

#### 1. Backend (Python 3.11+)
```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend test suite
pytest

# Optional: Seed first 3 days of January 2026 into cache
python -m app.scripts.seed_cache --start 1 --end 3

# Start FastAPI dev server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend (Node 20+)
```bash
cd frontend

# Install packages
npm install

# Launch Vite development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 4. Live Deployment
* **Live Web Application**: [Pending Deployment - Phase 5]
* **Backend API Swagger**: [Pending Deployment - Phase 5]

---

## 5. AI Tool Disclosure
In accordance with the assignment requirements, AI tools (Google Antigravity / Gemini) were utilized to assist in rapid scaffolding, boilerplate generation, and verification of statistical formulas. All domain logic, architecture design, and Elexon market integration were engineered and reviewed to meet production engineering standards.
