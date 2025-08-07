"""
Agent Registry Implementation

This module provides the core agent registry functionality for the A2A platform,
including agent discovery, registration, health monitoring, and lifecycle management.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config.settings import settings
from core.protocol.handlers import A2AProtocolHandler
from core.protocol.models import AgentCard

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Agent Registry for managing A2A agents.
    
    This class provides:
    - Agent discovery and registration
    - Agent card management and caching
    - Health monitoring and status tracking
    - Automatic cleanup of inactive agents
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        self.agents: Dict[str, AgentCard] = {}
        self.protocol_handler = A2AProtocolHandler(timeout=settings.AGENT_TIMEOUT)
        self._running = False
        
        logger.info("Agent Registry initialized")
    
    async def start(self):
        """Start the agent registry."""
        if self._running:
            return
        
        self._running = True
        logger.info("Agent Registry started")
    
    async def stop(self):
        """Stop the agent registry and cleanup resources."""
        if not self._running:
            return
        
        self._running = False
        await self.protocol_handler.close()
        logger.info("Agent Registry stopped")
    
    async def register_agent(self, agent_url: str, force_refresh: bool = False) -> bool:
        """
        Register an agent with the registry.
        
        Args:
            agent_url: URL of the agent to register
            force_refresh: Whether to force refresh even if already registered
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            logger.info(f"Registering agent: {agent_url}")
            
            # Check if agent is already registered
            agent_id = self._url_to_id(agent_url)
            if agent_id in self.agents and not force_refresh:
                logger.info(f"Agent already registered: {agent_url}")
                # Update last seen time
                self.agents[agent_id].update_last_seen()
                return True
            
            # Retrieve agent card
            agent_card = await self.protocol_handler.get_agent_card(agent_url)
            if not agent_card:
                logger.warning(f"Failed to retrieve agent card for: {agent_url}")
                return False
            
            # Validate agent card
            if not self._validate_agent_card(agent_card):
                logger.warning(f"Invalid agent card for: {agent_url}")
                return False
            
            # Store agent
            agent_id = self._url_to_id(agent_url)
            agent_card.update_last_seen()
            self.agents[agent_id] = agent_card
            
            logger.info(f"Successfully registered agent: {agent_card.name} ({agent_url})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering agent {agent_url}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if agent_id in self.agents:
                agent_name = self.agents[agent_id].name
                del self.agents[agent_id]
                logger.info(f"Unregistered agent: {agent_name} ({agent_id})")
                return True
            else:
                logger.warning(f"Agent not found for unregistration: {agent_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error unregistering agent {agent_id}: {e}")
            return False
    
    async def get_agent_card(self, agent_id: str) -> Optional[AgentCard]:
        """
        Get agent card by ID.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            AgentCard if found, None otherwise
        """
        return self.agents.get(agent_id)
    
    async def get_agent_by_url(self, agent_url: str) -> Optional[AgentCard]:
        """
        Get agent card by URL.
        
        Args:
            agent_url: URL of the agent
            
        Returns:
            AgentCard if found, None otherwise
        """
        agent_id = self._url_to_id(agent_url)
        return self.agents.get(agent_id)
    
    async def list_agents(self) -> List[AgentCard]:
        """
        List all registered agents.
        
        Returns:
            List of all registered agent cards
        """
        return list(self.agents.values())
    
    async def find_agents_by_capability(self, capability_name: str) -> List[AgentCard]:
        """
        Find agents that have a specific capability.
        
        Args:
            capability_name: Name of the capability to search for
            
        Returns:
            List of agent cards that have the specified capability
        """
        matching_agents = []
        
        for agent_card in self.agents.values():
            for capability in agent_card.capabilities:
                if capability.name.lower() == capability_name.lower():
                    matching_agents.append(agent_card)
                    break
        
        return matching_agents
    
    async def perform_health_checks(self):
        """Perform health checks on all registered agents."""
        if not self.agents:
            return
        
        logger.debug(f"Performing health checks on {len(self.agents)} agents")
        
        # Create health check tasks
        health_check_tasks = []
        for agent_id, agent_card in self.agents.items():
            task = asyncio.create_task(
                self._check_agent_health(agent_id, agent_card)
            )
            health_check_tasks.append(task)
        
        # Wait for all health checks to complete
        if health_check_tasks:
            await asyncio.gather(*health_check_tasks, return_exceptions=True)
        
        # Clean up inactive agents
        await self._cleanup_inactive_agents()
    
    async def _check_agent_health(self, agent_id: str, agent_card: AgentCard):
        """Check health of a specific agent."""
        try:
            is_healthy = await self.protocol_handler.health_check(agent_card.url)
            
            if is_healthy:
                agent_card.status = "active"
                agent_card.update_last_seen()
                logger.debug(f"Agent {agent_card.name} is healthy")
            else:
                agent_card.status = "unhealthy"
                logger.warning(f"Agent {agent_card.name} failed health check")
                
        except Exception as e:
            logger.error(f"Error checking health for agent {agent_card.name}: {e}")
            agent_card.status = "error"
    
    async def _cleanup_inactive_agents(self):
        """Remove agents that have been inactive for too long."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=settings.AGENT_TIMEOUT * 3)
        
        inactive_agents = []
        for agent_id, agent_card in self.agents.items():
            if agent_card.last_seen < cutoff_time:
                inactive_agents.append(agent_id)
        
        for agent_id in inactive_agents:
            agent_name = self.agents[agent_id].name
            del self.agents[agent_id]
            logger.info(f"Removed inactive agent: {agent_name} ({agent_id})")
    
    def _url_to_id(self, url: str) -> str:
        """Convert URL to agent ID."""
        # Simple implementation - in production, you might want a more sophisticated approach
        return str(hash(url.rstrip('/')))
    
    def _validate_agent_card(self, agent_card: AgentCard) -> bool:
        """
        Validate an agent card.
        
        Args:
            agent_card: Agent card to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not agent_card.name or not agent_card.url:
                return False
            
            # Check URL format
            if not agent_card.url.startswith(('http://', 'https://')):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating agent card: {e}")
            return False
    
    def get_registry_stats(self) -> Dict:
        """Get registry statistics."""
        def get_agent_status(agent):
            if isinstance(agent.status, str):
                return agent.status
            elif isinstance(agent.status, dict):
                return agent.status.get("state", "unknown")
            else:
                return "unknown"

        active_agents = sum(1 for agent in self.agents.values() if get_agent_status(agent) == "active")
        unhealthy_agents = sum(1 for agent in self.agents.values() if get_agent_status(agent) == "unhealthy")
        
        return {
            "total_agents": len(self.agents),
            "active_agents": active_agents,
            "unhealthy_agents": unhealthy_agents,
            "capabilities": self._get_capability_stats()
        }
    
    def _get_capability_stats(self) -> Dict[str, int]:
        """Get statistics about agent capabilities."""
        capability_counts = {}

        for agent_card in self.agents.values():
            if agent_card.capabilities:
                for capability in agent_card.capabilities:
                    # Handle both dict and object formats
                    if isinstance(capability, dict):
                        name = capability.get('name', 'unknown')
                    else:
                        name = getattr(capability, 'name', 'unknown')
                    capability_counts[name] = capability_counts.get(name, 0) + 1

        return capability_counts
