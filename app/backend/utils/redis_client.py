import redis
import app.backend.utils.config as config

def health_check():
    REDIS_URL = getattr(config, "REDIS_URL", None)
    if not REDIS_URL:
        return "unconfigured"
    try:
        r = redis.Redis.from_url(REDIS_URL)
        if r.ping():
            return "ok"
        else:
            return "unreachable"
    except Exception:
        return "unreachable"
