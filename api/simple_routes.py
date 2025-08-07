"""
Simplified API routes for A2A Platform.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

from core.models import (
    AgentRegistrationRequest, AgentRegistrationResponse,
    RegisteredAgent, HealthStatus
)
from core.agent_manager import AgentManager

logger = logging.getLogger(__name__)

# Initialize agent manager
agent_manager = AgentManager()

# Create router
router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Platform health check."""
    try:
        return HealthStatus(
            status="healthy",
            timestamp=datetime.now(),
            platform={
                "name": "JEECG A2A Platform",
                "version": "1.0.0",
                "description": "Enterprise A2A Protocol Platform"
            },
            statistics={
                "registered_agents": agent_manager.get_agent_count(),
                "active_tasks": 0,
                "capabilities": {
                    "agent_discovery": True,
                    "intelligent_routing": True,
                    "load_balancing": True,
                    "fault_tolerance": True,
                    "real_time_communication": True,
                    "multi_media_support": True
                }
            }
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/api/agents", response_model=List[RegisteredAgent])
async def get_agents():
    """Get all registered agents."""
    try:
        agents = agent_manager.get_all_agents()
        logger.info(f"Retrieved {len(agents)} agents")
        return agents
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/agents/register", response_model=AgentRegistrationResponse)
async def register_agent(request: AgentRegistrationRequest):
    """Register a new agent."""
    try:
        logger.info(f"Agent registration request: {request.url}")
        
        # Register agent
        response = await agent_manager.register_agent(request.url, request.force_refresh)
        
        if response.success:
            logger.info(f"Agent registration successful: {response.agent_id}")
        else:
            logger.warning(f"Agent registration failed: {response.message}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in agent registration: {e}")
        return AgentRegistrationResponse(
            success=False,
            message=f"Registration failed: {str(e)}"
        )


@router.delete("/api/agents/unregister/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister an agent."""
    try:
        success = agent_manager.unregister_agent(agent_id)
        
        if success:
            logger.info(f"Agent unregistered: {agent_id}")
            return {"success": True, "message": f"Agent {agent_id} unregistered successfully"}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/info/{agent_id}", response_model=RegisteredAgent)
async def get_agent_info(agent_id: str):
    """Get agent information."""
    try:
        agent = agent_manager.get_agent(agent_id)
        
        if agent:
            return agent
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent info {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/whitelist")
async def get_agent_whitelist():
    """Get agent whitelist information."""
    try:
        whitelist_info = agent_manager.get_whitelist_info()
        logger.info("Retrieved whitelist information")
        return whitelist_info
    except Exception as e:
        logger.error(f"Error getting whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/platform/stats")
async def get_platform_stats():
    """Get platform statistics."""
    try:
        stats = {
            "total_agents": agent_manager.get_agent_count(),
            "active_agents": len([a for a in agent_manager.get_all_agents() if a.status == "active"]),
            "platform_uptime": "Running",
            "last_updated": datetime.now().isoformat()
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting platform stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Root redirect
@router.get("/")
async def root():
    """Root endpoint - redirect to agents page."""
    return {"message": "JEECG A2A Platform", "version": "1.0.0", "status": "running"}
