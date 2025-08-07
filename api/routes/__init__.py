"""API routes package."""

# Import all route modules to ensure they are registered
from . import agents, chat, health, tasks, websocket

__all__ = ["agents", "chat", "health", "tasks", "websocket"]
