# Resource Monitoring Guide

## Overview

This directory contains the resource monitoring stack for the Stock Screener platform. The monitoring setup includes Prometheus for metrics collection, Grafana for visualization, cAdvisor for container metrics, and Postgres Exporter for database metrics.

**Purpose:** Measure actual resource usage (CPU, RAM, disk I/O) during development to make informed cloud hosting decisions before production deployment.

## Access Dashboards

- **Grafana:** http://localhost:3000
  - **Username:** admin
  - **Password:** (check `.env` file for `GRAFANA_ADMIN_PASSWORD`)

- **Prometheus:** http://localhost:9090
  - Query metrics directly
  - View targets status: http://localhost:9090/targets

- **cAdvisor:** http://localhost:8080
  - Real-time container resource usage

- **Postgres Exporter:** http://localhost:9187/metrics
  - PostgreSQL metrics in Prometheus format

- **Backend Metrics:** http://localhost:8001/metrics
  - FastAPI application metrics

## Key Metrics to Monitor

### Backend (FastAPI Application)

**What to watch:**
- **CPU usage** during data ingestion and calculations
- **RAM usage** peak (determines required vCPU tier for cloud hosting)
- **Request duration** (target: <2s for API endpoints)
- **Process memory** (target: <2 GB for Phase 1)

**Prometheus queries:**
```promql
# Backend memory usage (MB)
process_resident_memory_bytes{job="backend"} / 1024 / 1024

# Backend CPU usage (%)
rate(process_cpu_seconds_total{job="backend"}[5m]) * 100

# HTTP request rate
rate(http_requests_total{job="backend"}[5m])

# Request latency (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Database (PostgreSQL)

**What to watch:**
- **Query duration** (target: <1s for screener queries)
- **Connection pool usage** (ensure no connection exhaustion)
- **Table sizes** (monitor growth, plan partitioning at 10M records)
- **Cache hit ratio** (target: >95%)

**Prometheus queries:**
```promql
# Database size (GB)
pg_database_size_bytes{datname="screener_db"} / 1024 / 1024 / 1024

# Active connections
pg_stat_database_numbackends{datname="screener_db"}

# Cache hit ratio (%)
rate(pg_stat_database_blks_hit{datname="screener_db"}[5m])
/ (rate(pg_stat_database_blks_hit{datname="screener_db"}[5m])
   + rate(pg_stat_database_blks_read{datname="screener_db"}[5m])) * 100

# Rows fetched per second
rate(pg_stat_database_tup_fetched{datname="screener_db"}[5m])
```

### Container Resource Usage (cAdvisor)

**What to watch:**
- Backend container: CPU, RAM, disk I/O
- PostgreSQL container: CPU, RAM, disk I/O
- Network I/O between containers

**Prometheus queries:**
```promql
# Container CPU usage (%)
rate(container_cpu_usage_seconds_total{name=~"screener_.*"}[5m]) * 100

# Container memory usage (MB)
container_memory_usage_bytes{name=~"screener_.*"} / 1024 / 1024

# Container network I/O (bytes/sec)
rate(container_network_receive_bytes_total{name=~"screener_.*"}[5m])
rate(container_network_transmit_bytes_total{name=~"screener_.*"}[5m])
```

## Cloud Sizing Decision Matrix

Based on actual metrics collected during Phase 1-2 implementation:

### Backend Specs (for calculation workloads)

| Peak RAM Usage | vCPU Needed | Recommended Plan | Estimated Cost |
|----------------|-------------|------------------|----------------|
| < 2 GB         | 1-2 vCPU    | Basic Droplet (2 vCPU, 4 GB RAM) | $24/month |
| 2-4 GB         | 2-4 vCPU    | General Purpose (4 vCPU, 8 GB RAM) | $48/month |
| 4-8 GB         | 4-8 vCPU    | General Purpose (8 vCPU, 16 GB RAM) | $96/month |

### Database Specs (already decided)

**DigitalOcean Managed PostgreSQL:**
- **Plan:** Basic (1 vCPU, 1 GB RAM, 10 GB storage)
- **Cost:** $15/month
- **Rationale:** Database queries are simple (fetch by symbol+date), no heavy aggregations

**Note:** Backend handles all calculations (window functions, percentiles), not the database. Database only stores and retrieves data.

### Total Estimated Infrastructure Cost (Phase 1-2)

| Component | Plan | Monthly Cost |
|-----------|------|--------------|
| Database | DigitalOcean Managed PostgreSQL (Basic) | $15 |
| Backend | DigitalOcean Droplet (2-4 vCPU) | $24-48 |
| **Total** | | **$40-65/month** |

## Monitoring Stack Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose Network                │
│                                                           │
│  ┌─────────────┐    ┌──────────────┐   ┌──────────────┐│
│  │   Backend   │───▶│  Prometheus  │──▶│   Grafana    ││
│  │   :8000     │    │    :9090     │   │    :3000     ││
│  └─────────────┘    └──────────────┘   └──────────────┘│
│        │                   ▲                             │
│        │                   │                             │
│  ┌─────▼────┐         ┌───┴──────────┐                 │
│  │PostgreSQL│────────▶│Postgres      │                 │
│  │  :5432   │         │Exporter :9187│                 │
│  └──────────┘         └──────────────┘                 │
│                            ▲                             │
│                       ┌────┴────┐                       │
│                       │cAdvisor │                       │
│                       │  :8080  │                       │
│                       └─────────┘                       │
└─────────────────────────────────────────────────────────┘
```

**Flow:**
1. **Backend** exposes `/metrics` endpoint with Prometheus instrumentation
2. **Postgres Exporter** scrapes PostgreSQL metrics and exposes them
3. **cAdvisor** monitors all Docker containers and exposes metrics
4. **Prometheus** scrapes all targets every 15 seconds
5. **Grafana** queries Prometheus and visualizes data in dashboards

## Monitoring Commands

### Check Container Status

```bash
# View all containers
docker-compose ps

# Real-time container stats
docker stats

# View backend logs
docker-compose logs -f backend

# View Prometheus logs
docker-compose logs -f prometheus
```

### Query Metrics Manually

```bash
# Backend metrics (Prometheus format)
curl http://localhost:8001/metrics

# Prometheus targets status
curl http://localhost:9090/api/v1/targets | jq

# Query Prometheus API
curl --get --data-urlencode 'query=up' http://localhost:9090/api/v1/query | jq

# Postgres exporter metrics
curl http://localhost:9187/metrics | grep pg_database_size
```

### Test Grafana API

```bash
# List datasources (requires authentication)
curl -u admin:YOUR_PASSWORD http://localhost:3000/api/datasources

# Health check
curl http://localhost:3000/api/health
```

## Creating Custom Dashboards

### Via Grafana UI (Recommended)

1. Open Grafana: http://localhost:3000
2. Click "+" → "Dashboard"
3. Add panel with Prometheus query
4. Save dashboard as JSON
5. Place JSON file in `monitoring/grafana/dashboards/` for version control

### Example Panel Queries

**Backend Memory Usage:**
```promql
process_resident_memory_bytes{job="backend"} / 1024 / 1024
```

**Database Size Growth:**
```promql
pg_database_size_bytes{datname="screener_db"} / 1024 / 1024 / 1024
```

**HTTP Request Rate by Endpoint:**
```promql
rate(http_requests_total{job="backend"}[5m])
```

**Container CPU Usage:**
```promql
rate(container_cpu_usage_seconds_total{name="screener_backend"}[5m]) * 100
```

## Resource Logging (Backend)

The backend includes a `ResourceMonitor` utility for detailed resource tracking:

### Usage in Code

```python
from app.utils.resource_monitor import monitor_resources, ResourceMonitor

# Decorator usage (automatic logging)
@monitor_resources("Data Ingestion - NSE Securities")
async def ingest_securities(db: Session = Depends(get_db)):
    # ... endpoint logic ...
    return {"status": "success"}

# Manual logging at specific points
ResourceMonitor.log_resource_usage("After CSV download")
# ... some processing ...
ResourceMonitor.log_resource_usage("After database insert", {"rows_inserted": 1000})
```

### Log Output Format

```
INFO: Resource usage during Data Ingestion - NSE Securities - START:
Process RAM=95.23MB (1.2%), Process CPU=12.5%, System RAM=68.4%, System CPU=24.1%

INFO: Resource usage during Data Ingestion - NSE Securities - END:
Process RAM=152.47MB (1.9%), Process CPU=45.2%, System RAM=71.3%, System CPU=52.3%, duration_seconds=12.45
```

## Maintenance

### Prometheus Data Retention

- **Default:** 30 days (configured in `docker-compose.yml`)
- **Storage:** `prometheus_data` Docker volume
- **Cleanup:** Automatic (old data is purged after 30 days)

### Grafana Data

- **Storage:** `grafana_data` Docker volume
- **Dashboards:** Auto-provisioned from `monitoring/grafana/dashboards/`
- **Datasources:** Auto-provisioned from `monitoring/grafana/datasources/`

### Backup Monitoring Configuration

```bash
# Backup Grafana dashboards
docker exec screener_grafana grafana-cli admin export > grafana_backup.json

# Backup Prometheus data (if needed)
docker cp screener_prometheus:/prometheus ./prometheus_backup
```

## Troubleshooting

### Prometheus Targets Down

**Symptom:** Targets show "Down" status in http://localhost:9090/targets

**Solution:**
```bash
# Check if backend is running
docker-compose ps backend

# Check backend logs
docker-compose logs -f backend

# Verify backend metrics endpoint
curl http://localhost:8001/metrics
```

### Grafana Not Showing Data

**Symptom:** Grafana dashboards are empty or show "No data"

**Checks:**
1. Verify Prometheus is scraping: http://localhost:9090/targets (all should be "UP")
2. Test Prometheus query directly: http://localhost:9090/graph
3. Check Grafana datasource: Settings → Data Sources → Prometheus (should be green)
4. Verify time range in dashboard (adjust to "Last 1 hour")

### cAdvisor Not Working

**Symptom:** Container metrics not appearing

**Solution:**
```bash
# Check cAdvisor logs
docker-compose logs cadvisor

# Restart cAdvisor
docker-compose restart cadvisor

# Verify cAdvisor UI
open http://localhost:8080
```

## Next Steps

### Phase 2 Monitoring (After implementing calculated metrics)

1. Add custom Prometheus metrics for:
   - Calculation duration per metric type (MA, ATR, VARS, etc.)
   - Number of securities processed per calculation run
   - Calculation errors by type

2. Create Grafana dashboards for:
   - Daily calculation performance
   - Metric calculation latency breakdown
   - Error rates by screener type

3. Set up Grafana alerts for:
   - Backend memory >80% of available
   - Calculation duration >1 hour
   - Database connection pool exhaustion
   - Disk usage >80%

### Production Monitoring Considerations

- Consider adding **Loki** for log aggregation (complements Prometheus metrics)
- Set up **Alertmanager** for proactive alerting (email/Slack notifications)
- Implement **health check endpoints** for all critical services
- Configure **backup monitoring** (ensure backups are running successfully)

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [cAdvisor GitHub](https://github.com/google/cadvisor)
- [Postgres Exporter](https://github.com/prometheus-community/postgres_exporter)
- [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)
