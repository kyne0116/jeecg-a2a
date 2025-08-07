"""
A2A Protocol Handlers

This module provides handlers for A2A protocol messages and operations.
"""

import json
import logging
from typing import Any, Dict, Optional

import httpx

from .models import AgentCard, Message, Part, PartType, Role, Task, TaskRequest

logger = logging.getLogger(__name__)


class A2AProtocolHandler:
    """
    Handler for A2A protocol operations.
    
    This class provides methods for:
    - Agent card retrieval
    - Task submission and management
    - Message formatting and parsing
    - Protocol validation
    """
    
    def __init__(self, timeout: int = 30):
        """Initialize the protocol handler."""
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def get_agent_card(self, agent_url: str) -> Optional[AgentCard]:
        """
        Retrieve an agent card from the standard A2A endpoint.
        
        Args:
            agent_url: Base URL of the agent
            
        Returns:
            AgentCard if successful, None otherwise
        """
        try:
            # Ensure URL has proper format
            if not agent_url.startswith(('http://', 'https://')):
                agent_url = f"http://{agent_url}"
            
            # Remove trailing slash
            agent_url = agent_url.rstrip('/')
            
            # Construct agent card URL
            card_url = f"{agent_url}/.well-known/agent.json"
            
            logger.debug(f"Fetching agent card from: {card_url}")
            
            response = await self.client.get(card_url)
            response.raise_for_status()
            
            card_data = response.json()
            agent_card = AgentCard(**card_data)
            
            # Ensure the URL is set correctly
            if not agent_card.url:
                agent_card.url = agent_url
            
            logger.info(f"Successfully retrieved agent card for: {agent_card.name}")
            return agent_card
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error retrieving agent card from {agent_url}: {e}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"Request error retrieving agent card from {agent_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving agent card from {agent_url}: {e}")
            return None
    
    async def submit_task(self, agent_url: str, task_request: TaskRequest) -> Optional[Dict[str, Any]]:
        """
        Submit a task to an agent.
        
        Args:
            agent_url: Base URL of the agent
            task_request: Task request to submit
            
        Returns:
            Task response if successful, None otherwise
        """
        try:
            # Ensure URL has proper format
            if not agent_url.startswith(('http://', 'https://')):
                agent_url = f"http://{agent_url}"
            
            agent_url = agent_url.rstrip('/')
            
            # Construct task submission URL
            task_url = f"{agent_url}/api/tasks"
            
            logger.debug(f"Submitting task to: {task_url}")
            
            # Prepare request data
            request_data = task_request.dict()
            
            response = await self.client.post(
                task_url,
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully submitted task to {agent_url}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error submitting task to {agent_url}: {e}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"Request error submitting task to {agent_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error submitting task to {agent_url}: {e}")
            return None
    
    async def get_task_status(self, agent_url: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status from an agent.
        
        Args:
            agent_url: Base URL of the agent
            task_id: ID of the task
            
        Returns:
            Task status if successful, None otherwise
        """
        try:
            if not agent_url.startswith(('http://', 'https://')):
                agent_url = f"http://{agent_url}"
            
            agent_url = agent_url.rstrip('/')
            status_url = f"{agent_url}/api/tasks/{task_id}"
            
            response = await self.client.get(status_url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting task status from {agent_url}: {e}")
            return None
    
    async def health_check(self, agent_url: str) -> bool:
        """
        Perform a health check on an agent.
        
        Args:
            agent_url: Base URL of the agent
            
        Returns:
            True if agent is healthy, False otherwise
        """
        try:
            if not agent_url.startswith(('http://', 'https://')):
                agent_url = f"http://{agent_url}"
            
            agent_url = agent_url.rstrip('/')
            health_url = f"{agent_url}/health"
            
            response = await self.client.get(health_url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.debug(f"Health check failed for {agent_url}: {e}")
            return False
    
    def create_text_message(self, content: str, role: Role = Role.USER, 
                           context_id: Optional[str] = None,
                           task_id: Optional[str] = None) -> Message:
        """Create a text message."""
        part = Part(type=PartType.TEXT, content=content)
        return Message(
            role=role,
            parts=[part],
            context_id=context_id,
            task_id=task_id
        )
    
    def create_image_message(self, image_data: bytes, role: Role = Role.USER,
                            context_id: Optional[str] = None,
                            task_id: Optional[str] = None) -> Message:
        """Create an image message."""
        part = Part(type=PartType.IMAGE, content=image_data)
        return Message(
            role=role,
            parts=[part],
            context_id=context_id,
            task_id=task_id
        )
    
    def create_file_message(self, file_data: bytes, filename: str, 
                           role: Role = Role.USER,
                           context_id: Optional[str] = None,
                           task_id: Optional[str] = None) -> Message:
        """Create a file message."""
        part = Part(
            type=PartType.FILE, 
            content=file_data,
            metadata={"filename": filename}
        )
        return Message(
            role=role,
            parts=[part],
            context_id=context_id,
            task_id=task_id
        )
    
    def validate_agent_card(self, card_data: Dict[str, Any]) -> bool:
        """
        Validate an agent card against the A2A specification.
        
        Args:
            card_data: Agent card data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Required fields
            required_fields = ["name", "url", "version"]
            for field in required_fields:
                if field not in card_data:
                    logger.warning(f"Missing required field in agent card: {field}")
                    return False
            
            # Validate URL format
            url = card_data["url"]
            if not url.startswith(('http://', 'https://')):
                logger.warning(f"Invalid URL format in agent card: {url}")
                return False
            
            # Try to parse as AgentCard
            AgentCard(**card_data)
            return True
            
        except Exception as e:
            logger.warning(f"Agent card validation failed: {e}")
            return False
