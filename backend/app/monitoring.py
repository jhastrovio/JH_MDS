"""
Production monitoring and health checks for JH Market Data Service.
"""
import time
import psutil
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .logger import logger


class HealthChecker:
    """Health check utilities for production monitoring."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_redis_check = None
        self.last_oauth_check = None
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        try:
            health_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": int(time.time() - self.start_time),
                "status": "healthy",
                "checks": {}
            }
            
            # Memory usage
            memory = psutil.virtual_memory()
            health_data["checks"]["memory"] = {
                "usage_percent": memory.percent,
                "available_mb": round(memory.available / 1024 / 1024, 2),
                "status": "ok" if memory.percent < 85 else "warning"
            }
            
            # Redis connectivity
            redis_status = await self._check_redis_health()
            health_data["checks"]["redis"] = redis_status
            
            # OAuth configuration
            oauth_status = self._check_oauth_config()
            health_data["checks"]["oauth"] = oauth_status
            
            # Environment variables
            env_status = self._check_environment_variables()
            health_data["checks"]["environment"] = env_status
            
            # Overall status
            if any(check.get("status") == "error" for check in health_data["checks"].values()):
                health_data["status"] = "unhealthy"
            elif any(check.get("status") == "warning" for check in health_data["checks"].values()):
                health_data["status"] = "degraded"
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            from storage.redis_client import get_redis
            
            start_time = time.time()
            redis_client = get_redis()
            
            # Test basic connectivity
            await redis_client.ping()
            
            # Test read/write performance
            test_key = "health_check_test"
            await redis_client.set(test_key, "test_value", ex=10)
            retrieved = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            
            latency_ms = round((time.time() - start_time) * 1000, 2)
            
            return {
                "status": "ok",
                "latency_ms": latency_ms,
                "read_write_test": "passed" if retrieved == "test_value" else "failed",
                "last_checked": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }
    
    def _check_oauth_config(self) -> Dict[str, Any]:
        """Check OAuth configuration status."""
        try:
            import os
            
            required_vars = ["SAXO_APP_KEY", "SAXO_APP_SECRET", "SAXO_REDIRECT_URI"]
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            
            if missing_vars:
                return {
                    "status": "error",
                    "error": f"Missing environment variables: {missing_vars}",
                    "last_checked": datetime.utcnow().isoformat()
                }
            
            return {
                "status": "ok",
                "configured_vars": len(required_vars),
                "last_checked": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OAuth config check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }
    
    def _check_environment_variables(self) -> Dict[str, Any]:
        """Check critical environment variables."""
        import os
        
        critical_vars = {
            "NODE_ENV": os.environ.get("NODE_ENV", "development"),
            "REDIS_URL": "SET" if os.environ.get("REDIS_URL") else "MISSING",
            "JWT_SECRET": "SET" if os.environ.get("JWT_SECRET") else "MISSING",
            "SAXO_APP_KEY": "SET" if os.environ.get("SAXO_APP_KEY") else "MISSING"
        }
        
        missing_critical = [var for var, value in critical_vars.items() 
                          if value == "MISSING" and var != "NODE_ENV"]
        
        return {
            "status": "error" if missing_critical else "ok",
            "critical_vars": critical_vars,
            "missing_critical": missing_critical,
            "last_checked": datetime.utcnow().isoformat()
        }


# Global health checker instance
health_checker = HealthChecker()
