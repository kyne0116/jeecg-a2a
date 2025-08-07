"""
Task management endpoints for JEECG A2A Platform.
"""

import logging
import uuid
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from core.platform import platform
from core.protocol.models import Message, Part, PartType, Role, Task, TaskRequest, TaskResponse, TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=TaskResponse)
async def submit_task(task_request: TaskRequest):
    """
    Submit a task for execution.
    
    Args:
        task_request: Task request containing message and metadata
        
    Returns:
        Task response with task ID and initial status
    """
    try:
        # Create task from request
        task = Task(
            id=str(uuid.uuid4()),
            message=task_request.message,
            context_id=task_request.context_id,
            session_id=task_request.session_id,
            metadata=task_request.metadata
        )
        
        # Submit task to scheduler
        task_id = await platform.submit_task(task)
        
        # Get current status
        status = await platform.get_task_status(task_id)
        
        return TaskResponse(
            task_id=task_id,
            status=status,
            message="Task submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=f"Task submission failed: {str(e)}")


@router.get("/{task_id}/status", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get the status of a task.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Current task status
    """
    try:
        status = await platform.get_task_status(task_id)
        
        if status:
            return status
        else:
            raise HTTPException(status_code=404, detail="Task not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/{task_id}")
async def get_task(task_id: str):
    """
    Get complete task information.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Complete task information including history
    """
    try:
        # Get task from scheduler's active tasks
        task = platform.task_scheduler.active_tasks.get(task_id)
        
        if task:
            return task
        else:
            raise HTTPException(status_code=404, detail="Task not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    Cancel a running task.
    
    Args:
        task_id: ID of the task to cancel
        
    Returns:
        Cancellation result
    """
    try:
        success = await platform.cancel_task(task_id)
        
        if success:
            return {"success": True, "message": "Task cancelled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Task cancellation failed: {str(e)}")


@router.get("/")
async def list_active_tasks():
    """
    List all active tasks.
    
    Returns:
        List of active tasks with their current status
    """
    try:
        active_tasks = []
        
        for task_id, task in platform.task_scheduler.active_tasks.items():
            active_tasks.append({
                "task_id": task_id,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "context_id": task.context_id,
                "session_id": task.session_id
            })
        
        return active_tasks
        
    except Exception as e:
        logger.error(f"Error listing active tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/statistics/scheduler")
async def get_scheduler_statistics():
    """
    Get task scheduler statistics.
    
    Returns:
        Scheduler statistics including task counts and performance metrics
    """
    try:
        stats = platform.task_scheduler.get_scheduler_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting scheduler statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/submit-text")
async def submit_text_task(
    text: str,
    context_id: str = None,
    session_id: str = None
):
    """
    Submit a simple text task.
    
    Args:
        text: Text content of the task
        context_id: Optional context ID
        session_id: Optional session ID
        
    Returns:
        Task response
    """
    try:
        # Create text message
        part = Part(type=PartType.TEXT, content=text)
        message = Message(role=Role.USER, parts=[part])
        
        # Create task request
        task_request = TaskRequest(
            message=message,
            context_id=context_id,
            session_id=session_id
        )
        
        # Submit task
        return await submit_task(task_request)
        
    except Exception as e:
        logger.error(f"Error submitting text task: {e}")
        raise HTTPException(status_code=500, detail=f"Text task submission failed: {str(e)}")
