"""
Chat UI endpoints for JEECG A2A Platform.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Setup Jinja2 templates
templates_dir = Path(__file__).parent.parent.parent / "ui" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """
    Serve the main chat interface.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTML response with chat interface
    """
    try:
        # Get platform information
        from core.platform import platform
        platform_info = platform.get_platform_info()
        
        context = {
            "request": request,
            "platform_name": settings.PLATFORM_NAME,
            "platform_version": settings.PLATFORM_VERSION,
            "platform_description": settings.PLATFORM_DESCRIPTION,
            "websocket_url": f"ws://{settings.HOST}:{settings.PORT}/ws/chat",
            "api_base_url": f"http://{settings.HOST}:{settings.PORT}/api",
            "agents_count": platform_info.get("agents_count", 0),
            "capabilities": platform_info.get("capabilities", {}),
            "debug": settings.DEBUG
        }
        
        return templates.TemplateResponse("chat.html", context)
        
    except Exception as e:
        logger.error(f"Error serving chat interface: {e}")
        # Return a simple error page
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error - {settings.PLATFORM_NAME}</title></head>
                <body>
                    <h1>Error Loading Chat Interface</h1>
                    <p>Sorry, there was an error loading the chat interface: {str(e)}</p>
                    <p><a href="/health">Check Platform Health</a></p>
                </body>
            </html>
            """,
            status_code=500
        )


@router.get("/chat/agents", response_class=HTMLResponse)
async def agents_management(request: Request):
    """
    Serve the agents management interface.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTML response with agents management interface
    """
    try:
        from core.platform import platform

        # Get current agents
        agents_list = await platform.list_agents()
        registry_stats = platform.agent_registry.get_registry_stats()

        # Convert AgentCard objects to dictionaries for template compatibility
        agents = []
        for agent in agents_list:
            agent_dict = {
                "name": agent.name,
                "description": agent.description,
                "url": agent.url,
                "provider": agent.provider,
                "version": agent.version,
                "capabilities": agent.capabilities or [],
                "status": agent.status if isinstance(agent.status, str) else agent.status.get("state", "unknown") if isinstance(agent.status, dict) else "unknown",
                "last_seen": agent.last_seen,
                "metadata": agent.metadata or {}
            }
            agents.append(agent_dict)

        context = {
            "request": request,
            "platform_name": settings.PLATFORM_NAME,
            "agents": agents,
            "registry_stats": registry_stats,
            "api_base_url": f"http://{settings.HOST}:{settings.PORT}/api"
        }

        return templates.TemplateResponse("agents.html", context)
        
    except Exception as e:
        logger.error(f"Error serving agents management: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error - Agents Management</title></head>
                <body>
                    <h1>Error Loading Agents Management</h1>
                    <p>Error: {str(e)}</p>
                    <p><a href="/chat">Back to Chat</a></p>
                </body>
            </html>
            """,
            status_code=500
        )


@router.get("/chat/tasks", response_class=HTMLResponse)
async def tasks_monitoring(request: Request):
    """
    Serve the tasks monitoring interface.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTML response with tasks monitoring interface
    """
    try:
        from core.platform import platform
        
        # Get scheduler statistics
        scheduler_stats = platform.task_scheduler.get_scheduler_stats()
        
        # Get active tasks
        active_tasks = []
        for task_id, task in platform.task_scheduler.active_tasks.items():
            active_tasks.append({
                "id": task_id,
                "status": task.status.state,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "session_id": task.session_id,
                "context_id": task.context_id
            })
        
        context = {
            "request": request,
            "platform_name": settings.PLATFORM_NAME,
            "scheduler_stats": scheduler_stats,
            "active_tasks": active_tasks,
            "api_base_url": f"http://{settings.HOST}:{settings.PORT}/api"
        }
        
        return templates.TemplateResponse("tasks.html", context)
        
    except Exception as e:
        logger.error(f"Error serving tasks monitoring: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error - Tasks Monitoring</title></head>
                <body>
                    <h1>Error Loading Tasks Monitoring</h1>
                    <p>Error: {str(e)}</p>
                    <p><a href="/chat">Back to Chat</a></p>
                </body>
            </html>
            """,
            status_code=500
        )


@router.get("/chat/dashboard", response_class=HTMLResponse)
async def platform_dashboard(request: Request):
    """
    Serve the platform dashboard.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTML response with platform dashboard
    """
    try:
        from core.platform import platform
        
        # Get comprehensive platform information
        platform_info = platform.get_platform_info()
        registry_stats = platform.agent_registry.get_registry_stats()
        scheduler_stats = platform.task_scheduler.get_scheduler_stats()
        
        context = {
            "request": request,
            "platform_name": settings.PLATFORM_NAME,
            "platform_info": platform_info,
            "registry_stats": registry_stats,
            "scheduler_stats": scheduler_stats,
            "settings": {
                "max_concurrent_tasks": settings.MAX_CONCURRENT_TASKS,
                "agent_timeout": settings.AGENT_TIMEOUT,
                "auto_discovery": settings.AUTO_DISCOVERY_ENABLED
            }
        }
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        logger.error(f"Error serving platform dashboard: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error - Platform Dashboard</title></head>
                <body>
                    <h1>Error Loading Platform Dashboard</h1>
                    <p>Error: {str(e)}</p>
                    <p><a href="/chat">Back to Chat</a></p>
                </body>
            </html>
            """,
            status_code=500
        )
