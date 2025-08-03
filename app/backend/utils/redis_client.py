import redis
import app.backend.utils.config as config

_redis_client = None

def get_redis_client():
    """Get Redis client instance."""
    global _redis_client
    if _redis_client is None:
        REDIS_URL = getattr(config, "REDIS_URL", None)
        if REDIS_URL:
            try:
                _redis_client = redis.Redis.from_url(REDIS_URL)
                # Test connection
                _redis_client.ping()
            except Exception:
                _redis_client = None
    return _redis_client

def health_check():
    """Check Redis health."""
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
