"""Short-term memory / cache.

Uses Redis if reachable; otherwise falls back to an in-memory dict so the app
still works in local/dummy mode without a Redis container.
"""
import json
import hashlib
import logging
import time
from typing import Any, Optional

from app.config.settings import settings

log = logging.getLogger(__name__)

_redis = None
_mem: dict[str, tuple[float, str]] = {}  # key -> (expires_at, json_value)
_use_redis = settings.use_redis


def _connect():
    global _redis, _use_redis
    if not _use_redis:
        return None
    if _redis is not None:
        return _redis
    try:
        import redis
        client = redis.from_url(settings.redis_url, decode_responses=True,
                                socket_connect_timeout=2)
        client.ping()
        _redis = client
        log.info("cache: connected to redis at %s", settings.redis_url)
        return _redis
    except Exception as e:
        log.warning("cache: redis unavailable (%s) — falling back to in-memory", e)
        _use_redis = False
        return None


def _fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def cache_key(namespace: str, *parts: str) -> str:
    return f"rca:{namespace}:" + ":".join(parts)


def get(key: str) -> Optional[Any]:
    r = _connect()
    try:
        if r is not None:
            raw = r.get(key)
            return json.loads(raw) if raw else None
        # in-memory
        entry = _mem.get(key)
        if not entry:
            return None
        expires_at, raw = entry
        if expires_at < time.time():
            _mem.pop(key, None)
            return None
        return json.loads(raw)
    except Exception as e:
        log.warning("cache.get(%s) failed: %s", key, e)
        return None


def set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    ttl = ttl or settings.cache_ttl_seconds
    raw = json.dumps(value, default=str)
    r = _connect()
    try:
        if r is not None:
            r.setex(key, ttl, raw)
        else:
            _mem[key] = (time.time() + ttl, raw)
    except Exception as e:
        log.warning("cache.set(%s) failed: %s", key, e)


def fingerprint_logs(results: list) -> str:
    return _fingerprint(results)
