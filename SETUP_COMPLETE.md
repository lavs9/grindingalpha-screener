# PostgreSQL 17 + Resource Monitoring - Setup Complete ✅

**Date:** December 12, 2025
**Status:** All services running successfully

---

## Summary of Changes

### Decision: Standard PostgreSQL 17 (No TimescaleDB)

**Rationale:**
- DigitalOcean Managed PostgreSQL uses Apache edition which lacks advanced TimescaleDB features
- Proper B-tree indexing on `symbol` + `date` columns provides excellent performance for screener query patterns
- Simpler operational overhead and wider hosting options available
- Easier migration path to managed databases

### What Was Reverted

1. **docker-compose.yml** - Changed from `timescale/timescaledb:latest-pg17` to `postgres:17-alpine`
2. **scripts/init_db.sql** - Removed `CREATE EXTENSION timescaledb` statement
3. **MONITORING_SETUP.md** - Updated to reflect PostgreSQL 17 setup and indexing strategy
4. **.claude/Implementation-Plan.md** - Marked Phase 0.6 as completed, removed TimescaleDB references

---

## Current Infrastructure

### All 7 Services Running Successfully

```
NAME                         STATUS                    PORTS
screener_backend             Up (healthy)              0.0.0.0:8001->8000/tcp
screener_cadvisor            Up (healthy)              0.0.0.0:8080->8080/tcp
screener_grafana             Up                        0.0.0.0:3000->3000/tcp
screener_n8n                 Up                        0.0.0.0:5678->5678/tcp
screener_postgres            Up (healthy)              0.0.0.0:5433->5432/tcp
screener_postgres_exporter   Up                        0.0.0.0:9187->9187/tcp
screener_prometheus          Up                        0.0.0.0:9090->9090/tcp
```

### Database Verification

**PostgreSQL Version:** 17.7 Alpine (aarch64)
**Extensions Installed:**
- `plpgsql` (v1.0) - PL/pgSQL procedural language
- `uuid-ossp` (v1.1) - UUID generation

**No TimescaleDB** - Using standard PostgreSQL with optimized indexing strategy

---

## Monitoring Stack Details

### 1. Prometheus (Port 9090)
- **Status:** ✅ Running
- **Targets:** 4/4 UP (backend, postgres, cadvisor, prometheus)
- **Scrape Interval:** 15 seconds
- **Retention:** 30 days
- **URL:** http://localhost:9090

### 2. Grafana (Port 3000)
- **Status:** ✅ Running
- **Datasource:** Prometheus (pre-configured)
- **Credentials:** admin / screener_grafana_2024
- **URL:** http://localhost:3000

### 3. cAdvisor (Port 8080)
- **Status:** ✅ Running (healthy)
- **Purpose:** Container-level resource monitoring
- **URL:** http://localhost:8080

### 4. Postgres Exporter (Port 9187)
- **Status:** ✅ Running
- **Metrics:** Database size, connections, cache hit ratio, query stats
- **URL:** http://localhost:9187/metrics

### 5. Backend Metrics (Port 8001)
- **Status:** ✅ Working
- **Endpoint:** /metrics (Prometheus format)
- **Instrumentation:** FastAPI + prometheus-fastapi-instrumentator
- **URL:** http://localhost:8001/metrics

---

## Next Steps

### Immediate Actions

1. **Set Up Grafana Dashboards** (See [MONITORING_SETUP.md](MONITORING_SETUP.md) Step 6)
   - Backend Performance Dashboard (memory, CPU, request latency)
   - Database Performance Dashboard (size, connections, cache hit ratio)
   - Container Resources Dashboard (per-container CPU/memory)

2. **Add Resource Monitoring to Data Ingestion**
   - Use `@monitor_resources` decorator on ingestion endpoints
   - Monitor resource usage during Phase 1 data ingestion
   - Collect baseline metrics for cloud sizing decisions

### Phase 1 Data Ingestion (Ready to Start)

With monitoring in place, you can now:

1. Run all Phase 1 ingestion tasks (NSE securities, market cap, OHLCV, etc.)
2. Monitor resource usage in Grafana dashboards
3. Record peak metrics:
   - Backend: Peak RAM, CPU usage, request latency
   - Database: Database size, connection count, cache hit ratio
4. Use collected metrics to determine optimal cloud sizing for production deployment

### Phase 2 Performance Optimization

When implementing calculated metrics (23 daily indicators):

1. **Verify index performance:**
   ```sql
   -- Check index usage statistics
   SELECT schemaname, tablename, indexname, idx_scan
   FROM pg_stat_user_indexes
   WHERE tablename IN ('ohlcv_daily', 'market_cap_history', 'calculated_metrics')
   ORDER BY idx_scan DESC;
   ```

2. **Add composite indexes if needed:**
   ```sql
   -- Composite index for symbol + date range queries
   CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_date_desc
   ON ohlcv_daily (symbol, date DESC);

   -- Partial index for active securities only
   CREATE INDEX IF NOT EXISTS idx_securities_active_symbol
   ON securities (symbol) WHERE is_active = TRUE;
   ```

3. **Monitor query performance in Grafana**
4. **Deploy to DigitalOcean Managed PostgreSQL** based on collected metrics

---

## Performance Strategy

### Indexing Strategy (Standard PostgreSQL)

**Primary Indexes (Already in Schema):**
- `ohlcv_daily`: Composite unique index on `(symbol, date)`
- `market_cap_history`: Composite unique index on `(symbol, date)`
- `calculated_metrics`: Composite unique index on `(symbol, date)`
- `securities`: Unique index on `symbol`

**Query Patterns:**
- Screener queries: Single date, 2000 rows (indexed by date + symbol)
- Historical queries: Single symbol, date range (indexed by symbol + date DESC)
- Aggregations: Industry-level rollups (indexed by industry_id)

**Expected Performance (with proper indexes):**
- Point queries (single symbol, single date): <10ms
- Range queries (single symbol, 252 days): <100ms
- Full screener (2000 symbols, single date): <1s

### When to Consider Partitioning

- Database exceeds 10 GB (currently ~13 MB)
- Query times >2s for screener queries
- More than 10M records in time-series tables

Use native PostgreSQL monthly partitioning (documented in Architecture.md Section 11).

---

## Cloud Sizing Recommendations

### Current Baseline (Fresh Database)
- **Database Size:** ~13 MB (fresh PostgreSQL 17 with extensions)
- **Backend RAM:** ~145 MB (idle)
- **Monitoring:** All services running on local Docker

### After Phase 1 Ingestion (Estimated)
- **Database Size:** 1-2 GB (5 years OHLCV + market cap + metadata)
- **Backend RAM:** 200-400 MB (during ingestion, depends on batch size)
- **Backend CPU:** Monitor during ingestion to determine vCPU needs

### Production Hosting (After Measuring)

**Database (DigitalOcean Managed PostgreSQL):**
- Basic Plan: $15/month (1 vCPU, 1 GB RAM, 10 GB storage) - **Likely sufficient for Phase 1**
- Pro Plan: $30/month (2 vCPU, 4 GB RAM, 50 GB storage) - Upgrade for Phase 2+

**Backend (Separate Droplet):**
- Monitor actual usage during Phase 1 ingestion
- Estimate: 2 vCPU, 4 GB RAM (~$24/month) for Phase 2 calculations

**Total Estimated Cost:** $40-55/month for production deployment

---

## Documentation Updates

All references to TimescaleDB have been removed from:

- ✅ [docker-compose.yml](docker-compose.yml) - Using `postgres:17-alpine`
- ✅ [scripts/init_db.sql](scripts/init_db.sql) - Only uuid-ossp extension
- ✅ [MONITORING_SETUP.md](MONITORING_SETUP.md) - Updated to PostgreSQL 17 + indexing strategy
- ✅ [.claude/Implementation-Plan.md](.claude/Implementation-Plan.md) - Phase 0.6 marked complete
- ✅ [backend/main.py](backend/main.py) - Prometheus instrumentation in place
- ✅ [backend/requirements.txt](backend/requirements.txt) - Monitoring dependencies added
- ✅ [backend/app/utils/resource_monitor.py](backend/app/utils/resource_monitor.py) - Resource monitoring utility created

---

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Backend API** | http://localhost:8001 | - |
| **Backend Metrics** | http://localhost:8001/metrics | - |
| **API Docs (Swagger)** | http://localhost:8001/docs | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / screener_grafana_2024 |
| **cAdvisor** | http://localhost:8080 | - |
| **Postgres Exporter** | http://localhost:9187/metrics | - |
| **n8n** | http://localhost:5678 | (existing credentials from .env) |

---

## Quick Commands

**Start all services:**
```bash
docker-compose up -d
```

**Check service status:**
```bash
docker-compose ps
```

**View logs:**
```bash
docker-compose logs -f backend
docker-compose logs -f postgres
```

**Stop all services:**
```bash
docker-compose down
```

**Stop and remove volumes (fresh start):**
```bash
docker-compose down -v
```

**Connect to PostgreSQL:**
```bash
docker exec screener_postgres psql -U screener_user -d screener_db
```

**Check database size:**
```bash
docker exec screener_postgres psql -U screener_user -d screener_db -c "SELECT pg_size_pretty(pg_database_size('screener_db'));"
```

---

**Setup Complete!** All services are running with comprehensive monitoring. Ready for Phase 1 data ingestion.
