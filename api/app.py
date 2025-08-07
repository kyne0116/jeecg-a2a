"""
FastAPI Application for JEECG A2A Platform

This module sets up the main FastAPI application with all routes and middleware.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from core.platform import platform
from core.security.middleware import SecurityMiddleware, AgentAuthMiddleware
from core.security.cors_manager import cors_manager

from .routes import agents, chat, health, tasks, websocket

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting JEECG A2A Platform...")
    try:
        await platform.start()
        logger.info("Platform started successfully")
    except Exception as e:
        logger.error(f"Platform startup failed: {e}")
        # 继续启动，不让错误阻止服务器

    yield

    # Shutdown
    logger.info("Shutting down JEECG A2A Platform...")
    try:
        await platform.stop()
        logger.info("Platform shutdown complete")
    except Exception as e:
        logger.error(f"Platform shutdown failed: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.PLATFORM_NAME,
    description=settings.PLATFORM_DESCRIPTION,
    version=settings.PLATFORM_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add Security Middleware (must be added first) - Temporarily disabled for testing
# app.add_middleware(SecurityMiddleware)
# app.add_middleware(AgentAuthMiddleware)

# Add CORS middleware with dynamic origins
# Include common localhost variations for development
allowed_origins = cors_manager.get_allowed_origins()
# Add localhost variations if not already present
localhost_origins = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    "http://0.0.0.0:9000"
]
for origin in localhost_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(chat.router, tags=["Chat UI"])

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="ui/static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


@app.get("/.well-known/agent.json")
async def get_platform_agent_card():
    """Get the platform's own agent card."""
    from core.protocol.models import AgentCard, Capability, Provider
    
    # Create platform agent card
    platform_card = AgentCard(
        name=settings.PLATFORM_NAME,
        description=settings.PLATFORM_DESCRIPTION,
        url=settings.base_url,
        version=settings.PLATFORM_VERSION,
        provider=Provider(
            name="JEECG",
            url="https://github.com/jeecg"
        ),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain", "application/json"]
    )
    
    # Add platform capabilities
    platform_card.add_capability(
        name="agent_registry",
        description="Agent registration and discovery services",
        input_types=["application/json"],
        output_types=["application/json"]
    )
    
    platform_card.add_capability(
        name="task_scheduling",
        description="Intelligent task routing and execution",
        input_types=["application/json"],
        output_types=["application/json"]
    )
    
    platform_card.add_capability(
        name="chat_interface",
        description="Web-based chat interface for agent interaction",
        input_types=["text/plain", "multipart/form-data"],
        output_types=["text/html", "application/json"]
    )
    
    return platform_card


@app.get("/")
async def root():
    """Root endpoint - redirect to chat interface."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/chat")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
