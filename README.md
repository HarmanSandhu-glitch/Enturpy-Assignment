# Entrupy — Product Price Monitoring System

A full-stack product price monitoring system that ingests data from **Grailed**, **Fashionphile**, and **1stdibs**, tracks price history, and pushes real-time webhook notifications on price changes.

---

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+

### 1. Install Python dependencies

```bash
cd "/run/media/harmn/New Volume/Entrupy"
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Seed the database

```bash
python backend/seed.py
```

This loads all 90 sample JSON files into an SQLite database and seeds the dev API key.

### 3. Start the backend

```bash
uvicorn backend.main:app --reload
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:5173
```

---

## API Documentation

All endpoints require the header: `X-API-Key: dev-key`

| Method   | Endpoint             | Description                          |
| -------- | -------------------- | ------------------------------------ |
| `GET`    | `/api/health`        | Health check                         |
| `POST`   | `/api/refresh`       | Trigger async data refresh           |
| `POST`   | `/api/refresh/sync`  | Trigger sync refresh, returns counts |
| `GET`    | `/api/products`      | List products (filterable)           |
| `GET`    | `/api/products/{id}` | Product detail + full price history  |
| `GET`    | `/api/analytics`     | Aggregate stats by source & category |
| `POST`   | `/api/webhooks`      | Register a webhook subscription      |
| `GET`    | `/api/webhooks`      | List active subscriptions            |
| `DELETE` | `/api/webhooks/{id}` | Remove subscription                  |

### Query Parameters — `GET /api/products`

| Param       | Type   | Description                                            |
| ----------- | ------ | ------------------------------------------------------ |
| `source`    | string | Filter by source: `grailed`, `fashionphile`, `1stdibs` |
| `category`  | string | Filter by category name                                |
| `brand`     | string | Case-insensitive brand filter                          |
| `min_price` | float  | Minimum price (USD)                                    |
| `max_price` | float  | Maximum price (USD)                                    |
| `page`      | int    | Page number (default 1)                                |
| `size`      | int    | Page size (default 20, max 100)                        |

### Example Response — `GET /api/analytics`

```json
{
  "total_products": 90,
  "by_source": [
    {
      "source": "grailed",
      "total_products": 30,
      "avg_price": 487.5,
      "min_price": 125.0,
      "max_price": 1800.0
    }
  ],
  "by_category": [
    { "category": "Apparel", "total_products": 30, "avg_price": 487.5 }
  ],
  "last_refreshed_at": "2026-04-02T05:30:00Z"
}
```

---

## Running Tests

```bash
# From project root with venv activated
python -m pytest backend/tests/ -v --tb=short
```

**Test coverage (≥8 tests):**

- Parser field extraction for all 3 marketplaces + edge cases
- API key auth: valid, invalid, missing, usage counter increment
- Products API: list, filter by source/price, detail, 404, bad input
- Analytics: structure and source name validation
- Deduplication: same product upserted once, price change detection, no false positives
- Webhooks: create, list, delete, 404, queue delivery

---

## Design Decisions

### How does price history scale at millions of rows?

The `price_history` table has a composite index on `(product_id, recorded_at)`. For PostgreSQL (production), the table should be partitioned by month using `PARTITION BY RANGE (recorded_at)`. SQLAlchemy's `select` queries always filter by `product_id` first, keeping lookups O(log n) on the index.

For extremely large deployments, recent history can be kept in a hot partition while older months are archived to cold storage or a columnar store (e.g. ClickHouse).

### How are price changes notified?

An in-process `asyncio.Queue` decouples the ingestion path from the notification path. After every upsert, price change events are pushed to the queue — this adds ~0 latency to the fetch. A long-running `asyncio.create_task` background worker drains the queue and POSTs to registered webhook URLs.

All delivery attempts are persisted in the `webhook_deliveries` table with up to 5 retries using exponential backoff. Even if the server restarts, the delivery record exists for audit purposes (though in-flight events are replayed on next refresh).

**Alternatives considered:**

- _Redis/Celery_: Adds an external dependency not needed at this scale.
- _Polling_: Higher client latency, more unnecessary API calls.
- _Server-Sent Events_: Great for browser clients but not useful for machine-to-machine.

### How would you extend to 100+ data sources?

1. **Parser registry**: Each new source adds one `BaseParser` subclass registered in `PARSERS` dict — zero changes to the core fetch loop.
2. **Async parallel fetching**: `asyncio.gather(*[fetch_source(s) for s in sources])` runs all sources concurrently with per-source retry.
3. **Queue + worker scaling**: Replace `asyncio.Queue` with Redis Streams or Kafka when throughput demands it — the worker interface is the same.
4. **Database**: Switch `DATABASE_URL` env var to PostgreSQL with read replicas for analytics queries.

---

## Known Limitations

- **No live scraping**: Ingestion reads from local JSON files. `fetch_with_retry` is implemented for live URLs but not wired to real endpoints.
- **In-process queue**: Events are lost if the server crashes mid-delivery. A persistent queue (Redis Streams) would ensure at-least-once delivery across restarts.
- **Single API key seeded from config**: Production would need a proper key management API.
- **No rate limiting**: API has no per-key rate limits beyond counting usage.
- **SQLite in dev**: Fine for development, but SQLite has no partitioning support. Use PostgreSQL for production.
- **Frontend only polls once**: No live push to frontend; user must click Refresh or navigate to see updates.

# entrupyAssessment

# entrupyAssessment

# entrupyAssessment
