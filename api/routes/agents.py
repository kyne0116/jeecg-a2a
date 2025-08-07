"""
Agent management endpoints for JEECG A2A Platform.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

from core.platform import platform
from core.protocol.models import AgentCard, AgentRegistrationRequest, AgentRegistrationResponse
from core.security.cors_manager import cors_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=AgentRegistrationResponse)
async def register_agent(request: AgentRegistrationRequest, http_request: Request):
    """
    Register a new agent with the platform.

    Enhanced with security validation and dynamic CORS management.

    Args:
        request: Agent registration request containing URL and options
        http_request: HTTP request object for security validation

    Returns:
        Registration response with success status and agent information
    """
    try:
        logger.info(f"Registering agent: {request.url}")

        # 1. 获取agent卡片进行预验证
        agent_card = await platform.agent_registry.protocol_handler.get_agent_card(request.url)
        if not agent_card:
            return AgentRegistrationResponse(
                success=False,
                agent_id="",
                message="Failed to retrieve agent card from URL"
            )

        # 2. 安全验证
        agent_card_dict = agent_card.dict() if hasattr(agent_card, 'dict') else agent_card.__dict__
        validation_result = cors_manager.validate_agent_registration(request.url, agent_card_dict)

        if not validation_result[0]:
            return AgentRegistrationResponse(
                success=False,
                agent_id="",
                message=f"Security validation failed: {validation_result[1]}"
            )

        # 3. 注册agent
        success = await platform.register_agent(request.url, request.force_refresh)

        if success:
            # 4. 添加到CORS白名单
            cors_manager.add_agent_to_whitelist(request.url, agent_card_dict)

            # 5. 获取注册的agent信息
            registered_agent = await platform.agent_registry.get_agent_by_url(request.url)
            agent_id = platform.agent_registry._url_to_id(request.url)

            logger.info(f"Successfully registered and whitelisted agent: {request.url}")

            return AgentRegistrationResponse(
                success=True,
                agent_id=agent_id,
                message="Agent registered successfully and added to whitelist",
                agent_card=registered_agent
            )
        else:
            return AgentRegistrationResponse(
                success=False,
                agent_id="",
                message="Failed to register agent - validation or connection failed"
            )
            
    except Exception as e:
        logger.error(f"Error registering agent {request.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.delete("/unregister/{agent_id}")
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


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """
    Delete/unregister an agent from the platform (alternative endpoint for frontend compatibility).

    Args:
        agent_id: ID of the agent to delete (can be hash-based ID or base64-encoded URL)

    Returns:
        Success status and message
    """
    try:
        # First try with the provided agent_id
        success = await platform.unregister_agent(agent_id)

        if not success:
            # If not found, try to decode as base64 URL and convert to proper agent ID
            try:
                import base64
                decoded_url = base64.b64decode(agent_id + '==').decode('utf-8')  # Add padding
                # Convert URL to the same hash-based ID that the backend uses
                proper_agent_id = str(hash(decoded_url.rstrip('/')))
                success = await platform.unregister_agent(proper_agent_id)
            except Exception:
                # If base64 decoding fails, the agent_id might be invalid
                pass

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


@router.get("/info/{agent_id}", response_model=AgentCard)
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


@router.get("/whitelist")
async def get_agent_whitelist():
    """获取agent白名单"""
    try:
        return {
            "agents": cors_manager.agent_whitelist,
            "blocked": list(cors_manager.blocked_origins),
            "allowed_origins": cors_manager.get_allowed_origins()
        }
    except Exception as e:
        logger.error(f"Error getting whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whitelist/add")
async def add_to_whitelist(data: Dict[str, Any]):
    """手动添加agent到白名单"""
    try:
        url = data.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        agent_info = data.get("agent_info", {})
        success = cors_manager.add_agent_to_whitelist(url, agent_info)

        if success:
            return {"success": True, "message": f"Added {url} to whitelist"}
        else:
            return {"success": False, "message": "Failed to add to whitelist"}

    except Exception as e:
        logger.error(f"Error adding to whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/whitelist/{agent_url:path}")
async def remove_from_whitelist(agent_url: str):
    """从白名单中移除agent"""
    try:
        success = cors_manager.remove_agent_from_whitelist(agent_url)

        if success:
            return {"success": True, "message": f"Removed {agent_url} from whitelist"}
        else:
            return {"success": False, "message": "Agent not found in whitelist"}

    except Exception as e:
        logger.error(f"Error removing from whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/block")
async def block_agent(data: Dict[str, Any]):
    """阻止agent"""
    try:
        url = data.get("url")
        reason = data.get("reason", "Manual block")

        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        success = cors_manager.block_agent(url, reason)

        if success:
            return {"success": True, "message": f"Blocked {url}"}
        else:
            return {"success": False, "message": "Failed to block agent"}

    except Exception as e:
        logger.error(f"Error blocking agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))
