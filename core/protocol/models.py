"""
A2A Protocol Data Models

This module defines the core data structures for the A2A protocol,
based on Google's A2A specification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class TaskState(str, Enum):
    """Task execution states."""
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Role(str, Enum):
    """Message roles."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class PartType(str, Enum):
    """Message part types."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    DATA = "data"


class Part(BaseModel):
    """A part of a message (text, image, file, etc.)."""
    type: PartType
    content: Union[str, bytes, Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class Message(BaseModel):
    """A message in the A2A protocol."""
    id: Optional[str] = None
    role: Role
    parts: List[Part]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_id: Optional[str] = None
    task_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class TaskStatus(BaseModel):
    """Task status information."""
    state: TaskState
    message: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    error: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class Task(BaseModel):
    """A task in the A2A protocol."""
    id: str
    context_id: Optional[str] = None
    session_id: Optional[str] = None
    message: Message
    status: TaskStatus = Field(default_factory=lambda: TaskStatus(state=TaskState.SUBMITTED))
    history: List[Message] = Field(default_factory=list)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_message(self, message: Message):
        """Add a message to the task history."""
        self.history.append(message)
        self.updated_at = datetime.utcnow()
    
    def update_status(self, state: TaskState, message: Optional[str] = None, 
                     progress: Optional[float] = None, error: Optional[str] = None):
        """Update task status."""
        self.status = TaskStatus(
            state=state,
            message=message,
            progress=progress,
            error=error
        )
        self.updated_at = datetime.utcnow()


class Capability(BaseModel):
    """Agent capability definition."""
    name: str
    description: str
    input_types: List[str] = Field(default_factory=list)
    output_types: List[str] = Field(default_factory=list)
    parameters: Optional[Dict[str, Any]] = None


class Provider(BaseModel):
    """Agent provider information."""
    name: str
    url: Optional[str] = None
    contact: Optional[str] = None


class Authentication(BaseModel):
    """Authentication configuration."""
    schemes: List[str] = Field(default_factory=list)
    required: bool = False


class AgentCard(BaseModel):
    """
    Agent Card - The digital business card for an A2A agent.

    This follows the A2A specification for agent discovery and capability advertisement.
    """
    name: str
    description: Optional[str] = None
    url: str
    provider: Optional[Dict[str, Any]] = None
    version: str = "1.0.0"
    documentation_url: Optional[str] = None
    capabilities: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    authentication: Optional[Dict[str, Any]] = None
    default_input_modes: List[str] = Field(default_factory=lambda: ["text/plain"])
    default_output_modes: List[str] = Field(default_factory=lambda: ["text/plain"])
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # Health and status information
    status: Optional[Union[str, Dict[str, Any]]] = "active"
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    health_check_url: Optional[str] = None

    # Allow extra fields from the agent response
    class Config:
        extra = "allow"
    
    def add_capability(self, name: str, description: str, 
                      input_types: List[str] = None, 
                      output_types: List[str] = None):
        """Add a capability to the agent card."""
        capability = Capability(
            name=name,
            description=description,
            input_types=input_types or ["text/plain"],
            output_types=output_types or ["text/plain"]
        )
        self.capabilities.append(capability)
    
    def update_last_seen(self):
        """Update the last seen timestamp."""
        self.last_seen = datetime.utcnow()
    
    def is_healthy(self, timeout_seconds: int = 300) -> bool:
        """Check if the agent is considered healthy based on last seen time."""
        if self.status != "active":
            return False
        
        time_diff = datetime.utcnow() - self.last_seen
        return time_diff.total_seconds() < timeout_seconds


class TaskRequest(BaseModel):
    """Request to submit a task."""
    message: Message
    context_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Response from task submission."""
    task_id: str
    status: TaskStatus
    message: Optional[str] = None


class AgentRegistrationRequest(BaseModel):
    """Request to register an agent."""
    url: str
    force_refresh: bool = False


class AgentRegistrationResponse(BaseModel):
    """Response from agent registration."""
    success: bool
    agent_id: str
    message: Optional[str] = None
    agent_card: Optional[AgentCard] = None
