"""
Simplified Agent Manager for A2A Platform.
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .models import (
    AgentCard, RegisteredAgent, AgentCapability, 
    AgentRegistrationResponse, AgentWhitelist
)

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Simplified agent management system.
    """
    
    def __init__(self, whitelist_file: str = "./config/agent_whitelist.json"):
        """Initialize agent manager."""
        self.whitelist_file = whitelist_file
        self.registered_agents: Dict[str, RegisteredAgent] = {}
        self.whitelist: AgentWhitelist = AgentWhitelist()
        
        # Load whitelist
        self._load_whitelist()
        
        logger.info("Agent Manager initialized")
    
    def _load_whitelist(self):
        """Load agent whitelist from file."""
        try:
            whitelist_path = Path(self.whitelist_file)
            if whitelist_path.exists():
                with open(whitelist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.whitelist = AgentWhitelist(**data)
                logger.info(f"Loaded whitelist with {len(self.whitelist.agents)} agents")
            else:
                # Create default whitelist
                self._create_default_whitelist()
        except Exception as e:
            logger.error(f"Failed to load whitelist: {e}")
            self._create_default_whitelist()
    
    def _create_default_whitelist(self):
        """Create default whitelist configuration."""
        try:
            whitelist_path = Path(self.whitelist_file)
            whitelist_path.parent.mkdir(parents=True, exist_ok=True)
            
            default_whitelist = AgentWhitelist(
                agents={
                    "http://127.0.0.1:8888": {
                        "name": "CodeGen Expert",
                        "description": "JeecgBoot代码生成专家",
                        "trusted": True,
                        "auto_approved": True,
                        "created_at": datetime.now().isoformat()
                    },
                    "http://localhost:8888": {
                        "name": "CodeGen Expert (localhost)",
                        "description": "JeecgBoot代码生成专家 (localhost别名)",
                        "trusted": True,
                        "auto_approved": True,
                        "created_at": datetime.now().isoformat()
                    }
                },
                blocked=[],
                settings={
                    "auto_approve_localhost": True,
                    "require_authentication": False,
                    "max_agents": 100
                }
            )
            
            with open(whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(default_whitelist.dict(), f, indent=2, ensure_ascii=False)
            
            self.whitelist = default_whitelist
            logger.info("Created default whitelist")
            
        except Exception as e:
            logger.error(f"Failed to create default whitelist: {e}")
    
    def _save_whitelist(self):
        """Save whitelist to file."""
        try:
            whitelist_path = Path(self.whitelist_file)
            with open(whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(self.whitelist.dict(), f, indent=2, ensure_ascii=False)
            logger.info("Saved whitelist")
        except Exception as e:
            logger.error(f"Failed to save whitelist: {e}")
    
    def is_agent_allowed(self, url: str) -> bool:
        """Check if agent URL is allowed."""
        # Check if in whitelist
        if url in self.whitelist.agents:
            return True
        
        # Check if blocked
        if url in self.whitelist.blocked:
            return False
        
        # Auto-approve localhost if enabled
        if self.whitelist.settings.get("auto_approve_localhost", True):
            if "127.0.0.1" in url or "localhost" in url:
                return True
        
        return False
    
    async def fetch_agent_card(self, url: str) -> Optional[AgentCard]:
        """Fetch agent card from URL."""
        try:
            agent_json_url = f"{url.rstrip('/')}/.well-known/agent.json"
            logger.info(f"Fetching agent card from: {agent_json_url}")
            
            response = requests.get(agent_json_url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch agent card: HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            # Parse capabilities
            capabilities = []
            if "capabilities" in data and isinstance(data["capabilities"], list):
                for cap_data in data["capabilities"]:
                    if isinstance(cap_data, dict):
                        capabilities.append(AgentCapability(**cap_data))
            
            # Create agent card
            agent_card = AgentCard(
                name=data.get("name", "Unknown Agent"),
                description=data.get("description", ""),
                url=data.get("url", url),
                version=data.get("version", "1.0.0"),
                capabilities=capabilities,
                metadata=data.get("metadata", {})
            )
            
            logger.info(f"Successfully fetched agent card: {agent_card.name}")
            return agent_card
            
        except Exception as e:
            logger.error(f"Error fetching agent card from {url}: {e}")
            return None
    
    async def register_agent(self, url: str, force_refresh: bool = False) -> AgentRegistrationResponse:
        """Register an agent."""
        try:
            logger.info(f"Registering agent: {url}")
            
            # Check if agent is allowed
            if not self.is_agent_allowed(url):
                return AgentRegistrationResponse(
                    success=False,
                    message="Agent URL not in whitelist or is blocked"
                )
            
            # Generate agent ID
            agent_id = f"agent_{len(self.registered_agents) + 1}"
            
            # Check if already registered
            existing_agent = None
            for existing_id, agent in self.registered_agents.items():
                if agent.url == url:
                    existing_agent = (existing_id, agent)
                    break
            
            if existing_agent and not force_refresh:
                return AgentRegistrationResponse(
                    success=True,
                    agent_id=existing_agent[0],
                    message="Agent already registered",
                    agent_card=existing_agent[1]
                )
            
            # Fetch agent card
            agent_card = await self.fetch_agent_card(url)
            if not agent_card:
                return AgentRegistrationResponse(
                    success=False,
                    message="Failed to fetch agent card"
                )
            
            # Create registered agent
            registered_agent = RegisteredAgent(
                id=agent_id,
                name=agent_card.name,
                url=url,
                version=agent_card.version,
                description=agent_card.description or "",
                capabilities=agent_card.capabilities,
                status="active",
                registered_at=datetime.now(),
                last_seen=datetime.now(),
                metadata=agent_card.metadata
            )
            
            # Store agent
            if existing_agent:
                # Update existing
                self.registered_agents[existing_agent[0]] = registered_agent
                agent_id = existing_agent[0]
            else:
                # Add new
                self.registered_agents[agent_id] = registered_agent
            
            # Add to whitelist if not already there
            if url not in self.whitelist.agents:
                self.whitelist.agents[url] = {
                    "name": agent_card.name,
                    "description": agent_card.description or "",
                    "trusted": True,
                    "auto_approved": True,
                    "created_at": datetime.now().isoformat()
                }
                self._save_whitelist()
            
            logger.info(f"Successfully registered agent: {registered_agent.name} (ID: {agent_id})")
            
            return AgentRegistrationResponse(
                success=True,
                agent_id=agent_id,
                message=f"Agent '{registered_agent.name}' registered successfully",
                agent_card=registered_agent
            )
            
        except Exception as e:
            logger.error(f"Error registering agent {url}: {e}")
            return AgentRegistrationResponse(
                success=False,
                message=f"Registration failed: {str(e)}"
            )
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        try:
            if agent_id in self.registered_agents:
                agent = self.registered_agents.pop(agent_id)
                logger.info(f"Unregistered agent: {agent.name} (ID: {agent_id})")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unregistering agent {agent_id}: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get agent by ID."""
        return self.registered_agents.get(agent_id)
    
    def get_all_agents(self) -> List[RegisteredAgent]:
        """Get all registered agents."""
        return list(self.registered_agents.values())
    
    def get_agent_count(self) -> int:
        """Get number of registered agents."""
        return len(self.registered_agents)
    
    def get_whitelist_info(self) -> Dict[str, Any]:
        """Get whitelist information."""
        return {
            "agents": self.whitelist.agents,
            "blocked": self.whitelist.blocked,
            "allowed_origins": list(self.whitelist.agents.keys())
        }
