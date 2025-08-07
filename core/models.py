"""
Simplified data models for A2A Platform.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentCapability(BaseModel):
    """Agent capability definition."""
    name: str
    description: str = ""
    input_types: List[str] = ["text/plain"]
    output_types: List[str] = ["text/plain"]


class AgentCard(BaseModel):
    """Agent card information."""
    name: str
    description: Optional[str] = None
    url: str
    version: str = "1.0.0"
    capabilities: List[AgentCapability] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RegisteredAgent(BaseModel):
    """Registered agent information."""
    id: str
    name: str
    url: str
    version: str
    description: str = ""
    capabilities: List[AgentCapability] = Field(default_factory=list)
    status: str = "active"  # active, inactive, error
    registered_at: datetime = Field(default_factory=datetime.now)
    last_seen: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentRegistrationRequest(BaseModel):
    """Agent registration request."""
    url: str
    force_refresh: bool = False


class AgentRegistrationResponse(BaseModel):
    """Agent registration response."""
    success: bool
    agent_id: str = ""
    message: str = ""
    agent_card: Optional[RegisteredAgent] = None


class HealthStatus(BaseModel):
    """Platform health status."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    platform: Dict[str, str] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)


class AgentWhitelist(BaseModel):
    """Agent whitelist configuration."""
    agents: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    blocked: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)
