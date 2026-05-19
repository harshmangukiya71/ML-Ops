# AI Portfolio Manager — Production-Grade Full Stack

> **Functional Stochastic Portfolio Theory · GARCH · PyTorch · FastAPI · Next.js · MongoDB**

A production-ready AI-driven portfolio management system that dynamically learns optimal portfolio weights using Functional SPT, GARCH volatility modeling, and a residual neural network.

---

## Architecture

```
portfolio-mlops/
├── src/                    # ML core (existing)
│   ├── data/               # Downloader, feature engineering
│   ├── models/             # FunctionalSPT, SPTModel (PyTorch)
│   ├── portfolio/          # Rebalancing, transaction costs
│   ├── training/           # Trainer, losses, evaluate
│   └── utils/              # Logger, metrics store
│
├── backend/                # FastAPI API layer
│   ├── api/                # auth.py, portfolio.py, model.py
│   ├── database/           # Motor (async MongoDB), Pydantic schemas
│   ├── services/           # ml_service.py, portfolio_service.py, scheduler.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/               # Next.js 14 App Router
│   ├── src/app/            # dashboard, portfolio, analytics pages
│   ├── src/components/     # Sidebar, MetricCard, AllocationTable, charts
│   └── src/lib/            # API client, utilities
│
├── config/                 # YAML configs for both models
├── train.py                # CLI training entrypoint
├── predict.py              # CLI inference entrypoint
└── docker-compose.yml
```

---

## Quick Start

### 1. Clone & Environment Setup

```bash
git clone https://github.com/harshmangukiya54/Portfolio_Management_ML_Ops.git
cd Portfolio_Management_ML_Ops
```

**Backend**
```bash
cd backend
cp .env.example .env
# Edit .env — set MONGODB_URI and JWT_SECRET
pip install -r requirements.txt
```

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. MongoDB Atlas Setup

1. Create a free cluster at [MongoDB Atlas](https://cloud.mongodb.com)
2. Create a database user
3. Get the connection string and set `MONGODB_URI` in `backend/.env`

### 3. Run Locally

**Backend** (from repo root)
```bash
uvicorn backend.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000`

---

## Docker

```bash
# Start backend only
docker-compose up backend

# Start backend + frontend
docker-compose --profile frontend up

# Run model training (one-off)
docker-compose --profile train run train-functional-spt
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Get JWT token |
| `GET`  | `/auth/me` | Current user |
| `POST` | `/portfolio/create` | Create portfolio |
| `POST` | `/portfolio/add-stock` | Add stock + retrain |
| `POST` | `/portfolio/remove-stock` | Remove stock (proportional redistribution) |
| `GET`  | `/portfolio/weights` | Current weights + ₹ allocations |
| `GET`  | `/portfolio/performance` | Full backtest metrics + time series |
| `POST` | `/portfolio/rebalance` | Force rebalance cycle |
| `POST` | `/model/retrain` | Trigger background retraining |
| `GET`  | `/model/status` | Training status |
| `GET`  | `/model/metrics` | Historical metrics |

Interactive docs: `http://localhost:8000/docs`

---

## ML Model

- **Architecture**: Residual neural network (FunctionalSPT) — maps cross-sectional rank → portfolio weight
- **Features**: Risk-adjusted momentum, market weight rank, GARCH(1,1) volatility
- **Objective**: Maximize relative log-wealth over market + Sharpe penalty (Functional SPT loss)
- **Output**: Positive weights normalized to sum = 1 (no short selling)
- **Rebalancing**: Every 21 trading days with volatility targeting (15% annualized)
- **Transaction costs**: Applied only on rebalance days at 0.1% per unit turnover

---

## Deployment

### Backend → Render
1. Connect GitHub repo
2. Build command: `pip install -r backend/requirements.txt`
3. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Set all env vars from `backend/.env.example`

### Frontend → Vercel
1. Import GitHub repo in Vercel
2. Root directory: `frontend`
3. Set `NEXT_PUBLIC_API_URL` to your Render backend URL

---

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `MONGODB_URI` | MongoDB Atlas connection string |
| `MONGODB_DB` | Database name (default: `portfolio_ai`) |
| `JWT_SECRET` | Secret key for JWT signing |
| `REBALANCE_DAYS` | Rebalancing interval in days (default: 21) |
| `COST_RATE` | Transaction cost rate (default: 0.001 = 0.1%) |
| `VOL_TARGET` | Volatility targeting level (default: 0.15) |
| `SKIP_GARCH` | Set `true` to use rolling vol instead of GARCH (faster) |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
