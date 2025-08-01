
from fastapi import FastAPI
from app.backend.utils.redis_client import health_check

app = FastAPI(title="Equal-Weighted Index Service")

@app.get("/health")
def health():
    redis_status = health_check()
    return {"status": "ok", "redis": redis_status}
