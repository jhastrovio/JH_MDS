# backend/core/monitoring.py
"""
Production health checks for JH Market Data Service, with dependency injection.
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import Depends
from redis.asyncio import Redis

from core.settings import Settings, get_settings
from core.deps import get_redis, get_logger

# Attempt to import psutil; mark unavailable if missing
try:
    import psutil
except ImportError:
    psutil = None  # type: ignore

async def _check_memory() -> Dict[str, Any]:
    """Check system memory usage."""
    if psutil is None:
        return {"status": "unknown", "error": "psutil not installed"}
    loop = asyncio.get_running_loop()
    # Run blocking call in executor
    mem = await loop.run_in_executor(None, psutil.virtual_memory)
    usage = mem.percent
    return {
        "status": "ok" if usage < 85 else "warning",
        "usage_percent": usage,
        "available_mb": round(mem.available / 1024 / 1024, 2),
    }

async def _check_redis(redis: Redis) -> Dict[str, Any]:
    """Check Redis connectivity and simple read/write latency."""
    start = datetime.utcnow().timestamp()
    try:
        await redis.ping()
        key = "health:ping"
        await redis.set(key, "ok", ex=10)
        val = await redis.get(key)
        await redis.delete(key)
        latency = (datetime.utcnow().timestamp() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency, 2)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def _check_environment(settings: Settings) -> Dict[str, Any]:
    """Verify critical environment variables are set."""
    vars_to_check = {
        "REDIS_URL": bool(settings.REDIS_URL),
        "SAXO_APP_KEY": bool(settings.SAXO_APP_KEY),
        "SAXO_APP_SECRET": bool(settings.SAXO_APP_SECRET),
        "SAXO_REDIRECT_URI": bool(settings.SAXO_REDIRECT_URI),
    }
    missing = [key for key, ok in vars_to_check.items() if not ok]
    return {
        "status": "error" if missing else "ok",
        "checked_vars": vars_to_check,
        "missing": missing,
    }

async def get_system_health(
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
    logger = Depends(get_logger),
) -> Dict[str, Any]:
    """Aggregate system health status from memory, Redis, and env checks."""
    timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    checks: Dict[str, Any] = {}

    # Memory
    mem = await _check_memory()
    checks["memory"] = mem
    logger.debug("Memory check: %s", mem)

    # Redis
    redis_health = await _check_redis(redis)
    checks["redis"] = redis_health
    logger.debug("Redis check: %s", redis_health)

    # Environment
    env = await _check_environment(settings)
    checks["environment"] = env
    logger.debug("Env check: %s", env)

    # Determine overall status
    status: str
    if any(c.get("status") == "error" for c in checks.values()):
        status = "unhealthy"
    elif any(c.get("status") == "warning" for c in checks.values()):
        status = "degraded"
    else:
        status = "healthy"

    return {
        "timestamp": timestamp,
        "status": status,
        "checks": checks,
    }
