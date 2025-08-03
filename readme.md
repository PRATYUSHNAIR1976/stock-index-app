# Equal-Weighted Stock Index Service

## Stage 0 Setup

### Requirements
- Python 3.11+
- Docker & docker-compose
- Git

### Quickstart (local)
```bash
source .venv/bin/activate
uvicorn app.backend.main:app --reload
streamlit run streamlit_app/ui.py
```

---

## Dockerized Setup

### 1. Build and start all components
```bash
docker-compose up --build
```

### 2. Access the services
- FastAPI: http://localhost:8000/health
- Streamlit: http://localhost:8501/
- Redis: localhost:6379

### 3. Stopping all services
```bash
docker-compose down
```

### Notes
- Ensure `.env` is present in the project root for FastAPI config.
- All dependencies from `requirements.txt` are installed in both containers.
- Redis data is ephemeral unless you add a volume.

---

## Data Sources and Ingestion Strategy

### Data Sources

This project uses two sources for historical stock price data:

1. **Yahoo Finance (`yfinance` Python library)**
   - **Ease of Use:** Simple Python API, no API key required.
   - **Rate Limits:** Generous for most use cases, but undocumented and subject to change.
   - **Coverage:** Wide coverage of US and global equities.
   - **Reliability:** Generally reliable, but may occasionally miss data for certain dates or symbols.

2. **Alpha Vantage (TIME_SERIES_DAILY endpoint)**
   - **Ease of Use:** Requires free API key, simple REST API.
   - **Rate Limits:** Strict (5 requests/minute, 500 requests/day for free tier).
   - **Coverage:** Good coverage of major equities, but some symbols may be missing.
   - **Reliability:** Reliable for supported symbols, but subject to rate limits and API downtime.

### Fallback Logic

For each symbol and date, the ingestion job:

- **Tries Yahoo Finance first** (up to 3 retries with exponential backoff and jitter).
- **Falls back to Alpha Vantage** if Yahoo Finance fails or returns insufficient data (also retried).
- **Logs which source succeeded** and classifies errors (network, missing data, API limit, other).
- **Ensures that a failure for one symbol/date does not abort the entire run.**

### Idempotency Strategy

- **daily_stock_data** table uses a composite primary key (`symbol`, `date`) to enforce uniqueness.
- **Idempotent insert logic**: Attempts to insert only if the symbol/date pair does not already exist.
- **stock_metadata** table is upserted for each symbol, updating company name, exchange, and last_updated timestamp.

### Example Usage

Run the ingestion job for a date range and a default symbol list:

```sh
python ingestion/fetcher.py --start-date 2025-07-28 --end-date 2025-08-01
```

Or specify a custom symbol file:

```sh
python ingestion/fetcher.py --start-date 2025-07-28 --end-date 2025-08-01 --symbols-file symbols.txt
```

### Interpreting the Output

After running, you'll see:

- **Progress logs** for each symbol and date.
- **Summary statistics**:
  - Number of successful and failed fetches.
  - Breakdown of error types (network, API limit, missing data, other).
- **Failure report** listing all failed symbol/date pairs and reasons.
- **Stock metadata table** showing all symbols ingested, their company names, exchanges, and last updated timestamps.

This approach ensures robust, repeatable ingestion with clear error reporting and reliable data storage.
