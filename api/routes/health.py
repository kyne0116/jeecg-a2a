"""
Health check endpoints for JEECG A2A Platform.
"""

import logging
from datetime import datetime

from fastapi import APIRouter

from config.settings import settings
from core.platform import platform

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns platform health status and basic information.
    """
    try:
        platform_info = platform.get_platform_info()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": {
                "name": settings.PLATFORM_NAME,
                "version": settings.PLATFORM_VERSION,
                "description": settings.PLATFORM_DESCRIPTION
            },
            "statistics": {
                "registered_agents": platform_info.get("agents_count", 0),
                "active_tasks": platform_info.get("active_tasks", 0),
                "capabilities": platform_info.get("capabilities", {})
            },
            "configuration": {
                "max_concurrent_tasks": settings.MAX_CONCURRENT_TASKS,
                "agent_timeout": settings.AGENT_TIMEOUT,
                "auto_discovery_enabled": settings.AUTO_DISCOVERY_ENABLED
            }
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with component status.
    """
    try:
        # Get registry stats
        registry_stats = platform.agent_registry.get_registry_stats()
        
        # Get scheduler stats
        scheduler_stats = platform.task_scheduler.get_scheduler_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "agent_registry": {
                    "status": "healthy",
                    "statistics": registry_stats
                },
                "task_scheduler": {
                    "status": "healthy", 
                    "statistics": scheduler_stats
                },
                "platform": {
                    "status": "healthy",
                    "running": platform._running
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/metrics")
async def get_metrics():
    """
    Get platform metrics in Prometheus format.
    """
    try:
        registry_stats = platform.agent_registry.get_registry_stats()
        scheduler_stats = platform.task_scheduler.get_scheduler_stats()
        
        metrics = []
        
        # Agent metrics
        metrics.append(f"a2a_registered_agents_total {registry_stats['total_agents']}")
        metrics.append(f"a2a_active_agents_total {registry_stats['active_agents']}")
        metrics.append(f"a2a_unhealthy_agents_total {registry_stats['unhealthy_agents']}")
        
        # Task metrics
        metrics.append(f"a2a_active_tasks_total {scheduler_stats['active_tasks']}")
        metrics.append(f"a2a_completed_tasks_total {scheduler_stats['completed_tasks']}")
        metrics.append(f"a2a_failed_tasks_total {scheduler_stats['failed_tasks']}")
        metrics.append(f"a2a_task_queue_size {scheduler_stats['queue_size']}")
        
        # Worker metrics
        metrics.append(f"a2a_worker_count {scheduler_stats['worker_count']}")
        
        return "\n".join(metrics)
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return f"# Error collecting metrics: {e}"
