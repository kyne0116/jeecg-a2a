"""
Task Scheduler Implementation

This module provides intelligent task scheduling and routing capabilities
for the A2A platform, including load balancing, fault tolerance, and
multi-agent coordination.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set

from config.settings import settings
from core.agent_registry.registry import AgentRegistry
from core.protocol.handlers import A2AProtocolHandler
from core.protocol.models import AgentCard, Task, TaskRequest, TaskState, TaskStatus

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Intelligent Task Scheduler for A2A agents.
    
    This class provides:
    - AI-powered intelligent routing based on agent capabilities
    - Load balancing across available agents
    - Fault tolerance and automatic failover
    - Task queue management and async execution
    - Multi-agent workflow coordination
    """
    
    def __init__(self, agent_registry: AgentRegistry):
        """Initialize the task scheduler."""
        self.agent_registry = agent_registry
        self.protocol_handler = A2AProtocolHandler(timeout=settings.AGENT_TIMEOUT)
        
        # Task management
        self.active_tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=settings.MAX_CONCURRENT_TASKS)
        self.completed_tasks_count = 0
        self.failed_tasks_count = 0
        
        # Agent load tracking
        self.agent_loads: Dict[str, int] = {}  # agent_id -> current task count
        
        # Background task management
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        
        logger.info("Task Scheduler initialized")
    
    async def start(self):
        """Start the task scheduler and worker tasks."""
        if self._running:
            return
        
        self._running = True
        
        # Start worker tasks for processing the queue
        num_workers = min(10, settings.MAX_CONCURRENT_TASKS // 10 + 1)
        for i in range(num_workers):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(worker_task)
        
        logger.info(f"Task Scheduler started with {num_workers} workers")
    
    async def stop(self):
        """Stop the task scheduler and cleanup resources."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for workers to finish
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        await self.protocol_handler.close()
        logger.info("Task Scheduler stopped")
    
    async def submit_task(self, task: Task) -> str:
        """
        Submit a task for execution.
        
        Args:
            task: Task to execute
            
        Returns:
            Task ID
        """
        try:
            # Generate task ID if not provided
            if not task.id:
                task.id = str(uuid.uuid4())
            
            # Update task status
            task.update_status(TaskState.SUBMITTED, "Task submitted to scheduler")
            
            # Add to active tasks
            self.active_tasks[task.id] = task
            
            # Add to processing queue
            await self.task_queue.put(task)
            
            logger.info(f"Task {task.id} submitted to scheduler")
            return task.id
            
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            TaskStatus if found, None otherwise
        """
        task = self.active_tasks.get(task_id)
        return task.status if task else None
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            task = self.active_tasks.get(task_id)
            if not task:
                return False
            
            task.update_status(TaskState.CANCELLED, "Task cancelled by user")
            logger.info(f"Task {task_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    async def _worker_loop(self, worker_name: str):
        """Worker loop for processing tasks from the queue."""
        logger.debug(f"Worker {worker_name} started")
        
        while self._running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Process the task
                await self._process_task(task)
                
                # Mark task as done in queue
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                # No task available, continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_name}: {e}")
                await asyncio.sleep(1)
        
        logger.debug(f"Worker {worker_name} stopped")
    
    async def _process_task(self, task: Task):
        """
        Process a single task.
        
        Args:
            task: Task to process
        """
        try:
            logger.info(f"Processing task {task.id}")
            
            # Update task status
            task.update_status(TaskState.IN_PROGRESS, "Finding suitable agent")
            
            # Find suitable agent
            agent_card = await self._find_suitable_agent(task)
            if not agent_card:
                task.update_status(TaskState.FAILED, "No suitable agent found")
                self.failed_tasks_count += 1
                return
            
            # Execute task on agent
            success = await self._execute_task_on_agent(task, agent_card)
            
            if success:
                task.update_status(TaskState.COMPLETED, "Task completed successfully")
                self.completed_tasks_count += 1
            else:
                # Try failover to another agent
                await self._handle_task_failure(task, agent_card)
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            task.update_status(TaskState.FAILED, f"Processing error: {str(e)}")
            self.failed_tasks_count += 1
        
        finally:
            # Clean up completed/failed tasks after some time
            asyncio.create_task(self._cleanup_task(task.id, delay=300))  # 5 minutes
    
    async def _find_suitable_agent(self, task: Task) -> Optional[AgentCard]:
        """
        Find the most suitable agent for a task using intelligent routing.
        
        Args:
            task: Task to find agent for
            
        Returns:
            Most suitable AgentCard or None
        """
        try:
            # Get all available agents
            agents = await self.agent_registry.list_agents()
            
            # Filter active agents
            active_agents = [agent for agent in agents if agent.status == "active"]
            
            if not active_agents:
                logger.warning("No active agents available")
                return None
            
            # Simple routing: choose agent with lowest load
            # In a more sophisticated implementation, this would use AI to match
            # task requirements with agent capabilities
            
            best_agent = None
            lowest_load = float('inf')
            
            for agent in active_agents:
                agent_id = self._get_agent_id(agent)
                current_load = self.agent_loads.get(agent_id, 0)
                
                if current_load < lowest_load:
                    lowest_load = current_load
                    best_agent = agent
            
            if best_agent:
                logger.info(f"Selected agent {best_agent.name} for task {task.id}")
            
            return best_agent
            
        except Exception as e:
            logger.error(f"Error finding suitable agent: {e}")
            return None
    
    async def _execute_task_on_agent(self, task: Task, agent_card: AgentCard) -> bool:
        """
        Execute a task on a specific agent.
        
        Args:
            task: Task to execute
            agent_card: Agent to execute on
            
        Returns:
            True if successful, False otherwise
        """
        try:
            agent_id = self._get_agent_id(agent_card)
            
            # Update agent load
            self.agent_loads[agent_id] = self.agent_loads.get(agent_id, 0) + 1
            
            # Create task request
            task_request = TaskRequest(
                message=task.message,
                context_id=task.context_id,
                session_id=task.session_id,
                metadata=task.metadata
            )
            
            # Submit task to agent
            result = await self.protocol_handler.submit_task(agent_card.url, task_request)
            
            if result:
                logger.info(f"Task {task.id} successfully submitted to agent {agent_card.name}")
                return True
            else:
                logger.warning(f"Failed to submit task {task.id} to agent {agent_card.name}")
                return False
            
        except Exception as e:
            logger.error(f"Error executing task {task.id} on agent {agent_card.name}: {e}")
            return False
        
        finally:
            # Decrease agent load
            agent_id = self._get_agent_id(agent_card)
            if agent_id in self.agent_loads:
                self.agent_loads[agent_id] = max(0, self.agent_loads[agent_id] - 1)
    
    async def _handle_task_failure(self, task: Task, failed_agent: AgentCard):
        """
        Handle task failure with automatic failover.
        
        Args:
            task: Failed task
            failed_agent: Agent that failed to process the task
        """
        try:
            logger.warning(f"Task {task.id} failed on agent {failed_agent.name}, attempting failover")
            
            # Mark agent as potentially unhealthy
            failed_agent.status = "unhealthy"
            
            # Try to find another agent
            alternative_agent = await self._find_suitable_agent(task)
            
            if alternative_agent and alternative_agent.url != failed_agent.url:
                logger.info(f"Attempting failover to agent {alternative_agent.name}")
                success = await self._execute_task_on_agent(task, alternative_agent)
                
                if success:
                    task.update_status(TaskState.COMPLETED, "Task completed after failover")
                    self.completed_tasks_count += 1
                    return
            
            # No alternative agent or failover failed
            task.update_status(TaskState.FAILED, "Task failed and no alternative agent available")
            self.failed_tasks_count += 1
            
        except Exception as e:
            logger.error(f"Error handling task failure: {e}")
            task.update_status(TaskState.FAILED, f"Failover error: {str(e)}")
            self.failed_tasks_count += 1
    
    async def _cleanup_task(self, task_id: str, delay: int = 0):
        """
        Clean up a completed task after a delay.
        
        Args:
            task_id: ID of task to clean up
            delay: Delay in seconds before cleanup
        """
        if delay > 0:
            await asyncio.sleep(delay)
        
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            logger.debug(f"Cleaned up task {task_id}")
    
    def _get_agent_id(self, agent_card: AgentCard) -> str:
        """Get agent ID from agent card."""
        return str(hash(agent_card.url.rstrip('/')))
    
    def get_scheduler_stats(self) -> Dict:
        """Get scheduler statistics."""
        return {
            "active_tasks": len(self.active_tasks),
            "queue_size": self.task_queue.qsize(),
            "completed_tasks": self.completed_tasks_count,
            "failed_tasks": self.failed_tasks_count,
            "agent_loads": dict(self.agent_loads),
            "worker_count": len(self._worker_tasks)
        }
