"""
Agent management endpoints for JEECG A2A Platform.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from core.platform import platform
from core.protocol.models import AgentCard, AgentRegistrationRequest, AgentRegistrationResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=AgentRegistrationResponse)
async def register_agent(request: AgentRegistrationRequest):
    """
    Register a new agent with the platform.
    
    Args:
        request: Agent registration request containing URL and options
        
    Returns:
        Registration response with success status and agent information
    """
    try:
        logger.info(f"Registering agent: {request.url}")
        
        # Attempt to register the agent
        success = await platform.register_agent(request.url)
        
        if success:
            # Get the registered agent card
            agent_card = await platform.agent_registry.get_agent_by_url(request.url)
            agent_id = platform.agent_registry._url_to_id(request.url)
            
            return AgentRegistrationResponse(
                success=True,
                agent_id=agent_id,
                message="Agent registered successfully",
                agent_card=agent_card
            )
        else:
            return AgentRegistrationResponse(
                success=False,
                agent_id="",
                message="Failed to register agent - could not retrieve agent card or validation failed"
            )
            
    except Exception as e:
        logger.error(f"Error registering agent {request.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.delete("/{agent_id}")
async def unregister_agent(agent_id: str):
    """
    Unregister an agent from the platform.
    
    Args:
        agent_id: ID of the agent to unregister
        
    Returns:
        Success status and message
    """
    try:
        success = await platform.unregister_agent(agent_id)
        
        if success:
            return {"success": True, "message": "Agent unregistered successfully"}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unregistration failed: {str(e)}")


@router.get("/", response_model=List[AgentCard])
async def list_agents():
    """
    List all registered agents.
    
    Returns:
        List of all registered agent cards
    """
    try:
        agents = await platform.list_agents()
        return agents
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/{agent_id}", response_model=AgentCard)
async def get_agent(agent_id: str):
    """
    Get information about a specific agent.
    
    Args:
        agent_id: ID of the agent
        
    Returns:
        Agent card information
    """
    try:
        agent_card = await platform.get_agent_card(agent_id)
        
        if agent_card:
            return agent_card
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.post("/{agent_id}/health-check")
async def check_agent_health(agent_id: str):
    """
    Perform a health check on a specific agent.
    
    Args:
        agent_id: ID of the agent to check
        
    Returns:
        Health check result
    """
    try:
        agent_card = await platform.get_agent_card(agent_id)
        
        if not agent_card:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Perform health check
        is_healthy = await platform.agent_registry.protocol_handler.health_check(agent_card.url)
        
        if is_healthy:
            agent_card.update_last_seen()
            agent_card.status = "active"
        else:
            agent_card.status = "unhealthy"
        
        return {
            "agent_id": agent_id,
            "healthy": is_healthy,
            "status": agent_card.status,
            "last_seen": agent_card.last_seen.isoformat(),
            "url": agent_card.url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking health for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/search/by-capability/{capability_name}")
async def find_agents_by_capability(capability_name: str):
    """
    Find agents that have a specific capability.
    
    Args:
        capability_name: Name of the capability to search for
        
    Returns:
        List of agents with the specified capability
    """
    try:
        agents = await platform.agent_registry.find_agents_by_capability(capability_name)
        return agents
        
    except Exception as e:
        logger.error(f"Error searching agents by capability {capability_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/statistics/registry")
async def get_registry_statistics():
    """
    Get agent registry statistics.
    
    Returns:
        Registry statistics including agent counts and capabilities
    """
    try:
        stats = platform.agent_registry.get_registry_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting registry statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
