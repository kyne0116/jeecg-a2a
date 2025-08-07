"""
Security package for A2A platform.

Provides CORS management, authentication, and security middleware.
"""

from .cors_manager import cors_manager, CORSManager
from .middleware import SecurityMiddleware, AgentAuthMiddleware

__all__ = [
    "cors_manager",
    "CORSManager", 
    "SecurityMiddleware",
    "AgentAuthMiddleware"
]
