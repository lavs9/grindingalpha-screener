# Indian Stock Market Screener Platform

A comprehensive data aggregation and screening platform for Indian stock markets (NSE) built with FastAPI, PostgreSQL, and n8n workflow automation.

## 🎯 Project Status

**Current Phase:** Phase 0 - Environment Setup (Completed)
**Next Phase:** Phase 1.1 - Database Models & Schema

See [.claude/Implementation-Plan.md](.claude/Implementation-Plan.md) for detailed roadmap.

## 🏗️ Architecture

- **Backend:** FastAPI + SQLAlchemy ORM + PostgreSQL
- **Orchestration:** n8n for automated data pipelines
- **Deployment:** Docker Compose (multi-container setup)
- **Data Sources:** NSE Archives, NSE Website (JSON API), Upstox API

## 📁 Project Structure

```
/screener
├── .claude/                    # Planning & architecture docs
├── CLAUDE.md                   # Claude Code guidance
├── CONTRIBUTING.md             # Coding standards & guidelines
├── docker-compose.yml          # Multi-container orchestration
├── .env.example                # Environment template
├── .env                        # Environment variables (gitignored)
│
├── backend/                    # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                # Application entry point
│   ├── alembic.ini            # Database migration config
│   ├── alembic/               # Migration scripts
│   └── app/
│       ├── api/v1/            # API route handlers
│       ├── core/              # Configuration (settings)
│       ├── database/          # DB session & base
│       ├── models/            # SQLAlchemy models (Phase 1.1+)
│       ├── schemas/           # Pydantic request/response models
│       ├── services/          # Business logic (nse/, upstox/, calculators/)
│       └── utils/             # Validators, logging, utilities
│
├── n8n/                        # Workflow orchestration
│   ├── README.md              # n8n setup instructions
│   └── workflows/             # JSON workflow exports (Phase 1.5+)
│
├── scripts/                    # Database & deployment scripts
│   └── init_db.sql            # PostgreSQL initialization
│
├── logs/                       # Application logs (gitignored)
└── data/                       # Local data storage (gitignored)
```

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose** installed
- **50 GB** free disk space (for PostgreSQL data)
- **Upstox API credentials** (for market data access)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd screener
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your Upstox API credentials:
   # - UPSTOX_API_KEY
   # - UPSTOX_API_SECRET
   # - UPSTOX_ACCESS_TOKEN
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Verify services are running**
   ```bash
   docker-compose ps
   ```

5. **Access the services**
   - **Backend API:** http://localhost:8000
   - **API Documentation (Swagger):** http://localhost:8000/docs
   - **API Documentation (ReDoc):** http://localhost:8000/redoc
   - **n8n Workflow UI:** http://localhost:5678
   - **PostgreSQL:** localhost:5432

### First-Time Setup

1. **Access n8n UI** at http://localhost:5678
   - Create a local account (any email/password)
   - Configure timezone: Settings → General → Asia/Kolkata

2. **Verify backend health**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. **Check database connectivity**
   ```bash
   docker exec -it screener_postgres psql -U screener_user -d screener_db
   # Type \dt to list tables (currently none until Phase 1.1)
   # Type \q to quit
   ```

## 🛠️ Development

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f n8n
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Rebuild After Code Changes

```bash
# Rebuild and restart backend
docker-compose up -d --build backend
```

### Run Database Migrations (Phase 1.1+)

```bash
# Generate new migration
docker exec -it screener_backend alembic revision --autogenerate -m "description"

# Apply migrations
docker exec -it screener_backend alembic upgrade head

# Rollback migration
docker exec -it screener_backend alembic downgrade -1
```

### Stop All Services

```bash
# Stop without removing volumes
docker-compose down

# Stop and remove all data (CAUTION: deletes database)
docker-compose down -v
```

## 📊 Database Access

### Connect to PostgreSQL

```bash
docker exec -it screener_postgres psql -U screener_user -d screener_db
```

### Useful SQL Commands

```sql
-- List all tables
\dt

-- Describe table structure
\d table_name

-- Check data (Phase 1.2+)
SELECT COUNT(*) FROM securities;
SELECT * FROM securities LIMIT 10;

-- Check ingestion status (Phase 1.5+)
SELECT source, status, records_inserted, timestamp
FROM ingestion_logs
ORDER BY timestamp DESC
LIMIT 20;

-- Quit
\q
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file to configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | `postgres` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `screener_db` |
| `DB_USER` | Database user | `screener_user` |
| `DB_PASSWORD` | Database password | (generated) |
| `UPSTOX_API_KEY` | Upstox API key | (required) |
| `UPSTOX_API_SECRET` | Upstox API secret | (required) |
| `UPSTOX_ACCESS_TOKEN` | Upstox access token | (required) |
| `N8N_ENCRYPTION_KEY` | n8n encryption key | (generated) |
| `ENV` | Environment mode | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Upstox API Setup

1. Sign up at [Upstox Developer Console](https://upstox.com/developer/)
2. Create an app to get API key and secret
3. Generate access token (see Upstox documentation)
4. Add credentials to `.env` file

## 🧪 Testing

### Health Check

```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Detailed health check (includes database)
curl http://localhost:8000/api/v1/health/detailed
```

### API Documentation

Visit http://localhost:8000/docs to:
- Explore all available endpoints
- Test endpoints interactively
- View request/response schemas

## 📖 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Guidance for Claude Code when working with this codebase
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Coding standards, validation rules, testing requirements
- **[.claude/PRD.md](.claude/PRD.md)** - Product Requirements Document
- **[.claude/Architecture.md](.claude/Architecture.md)** - System architecture and database schema
- **[.claude/Implementation-Plan.md](.claude/Implementation-Plan.md)** - Phased implementation plan
- **[.claude/file-formats.md](.claude/file-formats.md)** - Data source format specifications
- **[n8n/README.md](n8n/README.md)** - n8n workflow setup instructions

## 🗺️ Roadmap

### Phase 0: Environment Setup ✅ (Completed)
- Docker Compose infrastructure
- Backend FastAPI application structure
- Database configuration
- Alembic migration framework

### Phase 1.1: Database Models (In Progress)
- Create all 11 database tables
- Set up Alembic migrations
- Define Pydantic schemas

### Phase 1.2-1.4: Data Integration (Upcoming)
- NSE data sources (securities, market cap, deals)
- Upstox API integration (OHLCV data)
- Industry classification scraper
- Index constituents management

### Phase 1.5: n8n Workflows (Upcoming)
- Daily EOD data ingestion workflow
- Weekly industry classification workflow
- Historical backfill workflow

### Phase 2: Screeners & Metrics (Future)
- 11 advanced screeners (RRG charts priority)
- 30+ calculated metrics
- Frontend dashboard

See [.claude/Implementation-Plan.md](.claude/Implementation-Plan.md) for complete details.

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Python coding standards (PEP 8, type hints, docstrings)
- Module structure and organization
- Database development guidelines
- API development conventions
- Data validation requirements
- Testing requirements
- Git workflow and commit messages

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs <service-name>

# Verify .env file exists and has valid values
cat .env

# Rebuild containers
docker-compose up -d --build
```

### Database connection errors
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Verify database credentials in .env
# Wait for PostgreSQL health check to pass (can take 10-20 seconds)
docker-compose logs postgres
```

### Port already in use
```bash
# Check what's using the port
lsof -i :8000  # or :5432, :5678

# Stop the conflicting service or change port in docker-compose.yml
```

### Reset everything (CAUTION: deletes all data)
```bash
docker-compose down -v
docker-compose up -d
```

## 📝 License

[Add license information]

## 🙏 Acknowledgments

- **NSE India** - Market data source
- **Upstox** - Market data API
- **n8n** - Workflow automation platform

---

**Development Team**
Last Updated: 2025-11-22
Version: 1.0.0 (Phase 0 Complete)
