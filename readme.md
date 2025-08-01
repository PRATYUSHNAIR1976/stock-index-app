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
