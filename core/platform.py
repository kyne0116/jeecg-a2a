"""
JEECG A2A Platform - Core Platform Implementation

This module provides the main platform orchestration and coordination.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from config.settings import settings
from core.agent_registry.registry import AgentRegistry
from core.protocol.models import AgentCard, Task, TaskStatus
from core.scheduler.scheduler import TaskScheduler

logger = logging.getLogger(__name__)


class A2APlatform:
    """
    Main A2A Platform class that orchestrates all core components.
    
    This class serves as the central coordinator for:
    - Agent Registry (discovery, registration, health monitoring)
    - Task Scheduler (routing, load balancing, execution)
    - Protocol Handlers (A2A message processing)
    """
    
    def __init__(self):
        """Initialize the A2A Platform."""
        self.agent_registry = AgentRegistry()
        self.task_scheduler = TaskScheduler(self.agent_registry)
        self._running = False
        self._background_tasks: List[asyncio.Task] = []
        
        logger.info("A2A Platform initialized")
    
    async def start(self):
        """Start the platform and all background services."""
        if self._running:
            logger.warning("Platform is already running")
            return
        
        logger.info("Starting A2A Platform...")
        
        try:
            # Start agent registry
            await self.agent_registry.start()
            
            # Start task scheduler
            await self.task_scheduler.start()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self._running = True
            logger.info("A2A Platform started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start A2A Platform: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the platform and cleanup resources."""
        if not self._running:
            return
        
        logger.info("Stopping A2A Platform...")
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Stop components
        await self.task_scheduler.stop()
        await self.agent_registry.stop()
        
        self._running = False
        logger.info("A2A Platform stopped")
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks."""
        # Health check task
        if settings.AGENT_HEALTH_CHECK_INTERVAL > 0:
            health_task = asyncio.create_task(self._health_check_loop())
            self._background_tasks.append(health_task)
        
        # Metrics collection task
        if settings.ENABLE_METRICS:
            metrics_task = asyncio.create_task(self._metrics_collection_loop())
            self._background_tasks.append(metrics_task)
    
    async def _health_check_loop(self):
        """Background task for periodic health checks."""
        while self._running:
            try:
                await self.agent_registry.perform_health_checks()
                await asyncio.sleep(settings.AGENT_HEALTH_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _metrics_collection_loop(self):
        """Background task for metrics collection."""
        while self._running:
            try:
                # Collect and update metrics
                await self._collect_metrics()
                await asyncio.sleep(60)  # Collect metrics every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(10)
    
    async def _collect_metrics(self):
        """Collect platform metrics."""
        # This would integrate with prometheus or other monitoring systems
        metrics = {
            "registered_agents": len(self.agent_registry.agents),
            "active_tasks": len(self.task_scheduler.active_tasks),
            "completed_tasks": self.task_scheduler.completed_tasks_count,
            "failed_tasks": self.task_scheduler.failed_tasks_count,
        }
        
        logger.debug(f"Platform metrics: {metrics}")
    
    # Public API methods
    
    async def register_agent(self, agent_url: str, force_refresh: bool = False) -> bool:
        """Register a new agent with the platform."""
        return await self.agent_registry.register_agent(agent_url, force_refresh)
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the platform."""
        return await self.agent_registry.unregister_agent(agent_id)
    
    async def get_agent_card(self, agent_id: str) -> Optional[AgentCard]:
        """Get agent card for a specific agent."""
        return await self.agent_registry.get_agent_card(agent_id)
    
    async def list_agents(self) -> List[AgentCard]:
        """List all registered agents."""
        return await self.agent_registry.list_agents()
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task for execution."""
        return await self.task_scheduler.submit_task(task)
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task."""
        return await self.task_scheduler.get_task_status(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        return await self.task_scheduler.cancel_task(task_id)
    
    def get_platform_info(self) -> Dict:
        """Get platform information and statistics."""
        return {
            "name": settings.PLATFORM_NAME,
            "version": settings.PLATFORM_VERSION,
            "description": settings.PLATFORM_DESCRIPTION,
            "status": "running" if self._running else "stopped",
            "agents_count": len(self.agent_registry.agents),
            "active_tasks": len(self.task_scheduler.active_tasks),
            "capabilities": {
                "agent_discovery": True,
                "intelligent_routing": settings.is_ai_enabled(),
                "load_balancing": True,
                "fault_tolerance": True,
                "real_time_communication": True,
                "multi_media_support": True,
            }
        }


# Global platform instance
platform = A2APlatform()
