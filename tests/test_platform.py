"""
Tests for the core platform functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from core.platform import A2APlatform
from core.protocol.models import AgentCard, Task, Message, Part, PartType, Role


@pytest.fixture
async def platform():
    """Create a test platform instance."""
    platform = A2APlatform()
    await platform.start()
    yield platform
    await platform.stop()


@pytest.fixture
def sample_agent_card():
    """Create a sample agent card for testing."""
    return AgentCard(
        name="Test Agent",
        description="A test agent for unit testing",
        url="http://localhost:8080",
        version="1.0.0"
    )


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    part = Part(type=PartType.TEXT, content="Hello, world!")
    message = Message(role=Role.USER, parts=[part])
    return Task(
        id="test-task-123",
        message=message
    )


class TestA2APlatform:
    """Test cases for A2APlatform."""
    
    @pytest.mark.asyncio
    async def test_platform_startup_shutdown(self):
        """Test platform startup and shutdown."""
        platform = A2APlatform()
        
        # Test startup
        await platform.start()
        assert platform._running is True
        
        # Test shutdown
        await platform.stop()
        assert platform._running is False
    
    @pytest.mark.asyncio
    async def test_get_platform_info(self, platform):
        """Test getting platform information."""
        info = platform.get_platform_info()
        
        assert "name" in info
        assert "version" in info
        assert "status" in info
        assert "capabilities" in info
        assert info["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, platform, sample_agent_card):
        """Test agent registration."""
        # Mock the agent registry
        platform.agent_registry.register_agent = AsyncMock(return_value=True)
        
        result = await platform.register_agent("http://localhost:8080")
        assert result is True
        
        platform.agent_registry.register_agent.assert_called_once_with("http://localhost:8080")
    
    @pytest.mark.asyncio
    async def test_task_submission(self, platform, sample_task):
        """Test task submission."""
        # Mock the task scheduler
        platform.task_scheduler.submit_task = AsyncMock(return_value="test-task-123")
        
        task_id = await platform.submit_task(sample_task)
        assert task_id == "test-task-123"
        
        platform.task_scheduler.submit_task.assert_called_once_with(sample_task)
    
    @pytest.mark.asyncio
    async def test_task_status_retrieval(self, platform):
        """Test task status retrieval."""
        from core.protocol.models import TaskStatus, TaskState
        
        # Mock the task scheduler
        mock_status = TaskStatus(state=TaskState.COMPLETED)
        platform.task_scheduler.get_task_status = AsyncMock(return_value=mock_status)
        
        status = await platform.get_task_status("test-task-123")
        assert status is not None
        assert status.state == TaskState.COMPLETED
        
        platform.task_scheduler.get_task_status.assert_called_once_with("test-task-123")
    
    @pytest.mark.asyncio
    async def test_task_cancellation(self, platform):
        """Test task cancellation."""
        # Mock the task scheduler
        platform.task_scheduler.cancel_task = AsyncMock(return_value=True)
        
        result = await platform.cancel_task("test-task-123")
        assert result is True
        
        platform.task_scheduler.cancel_task.assert_called_once_with("test-task-123")
    
    @pytest.mark.asyncio
    async def test_list_agents(self, platform, sample_agent_card):
        """Test listing agents."""
        # Mock the agent registry
        platform.agent_registry.list_agents = AsyncMock(return_value=[sample_agent_card])
        
        agents = await platform.list_agents()
        assert len(agents) == 1
        assert agents[0].name == "Test Agent"
        
        platform.agent_registry.list_agents.assert_called_once()


class TestPlatformIntegration:
    """Integration tests for platform components."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, platform, sample_task):
        """Test a complete workflow from task submission to completion."""
        # Mock components for integration test
        platform.agent_registry.register_agent = AsyncMock(return_value=True)
        platform.task_scheduler.submit_task = AsyncMock(return_value="test-task-123")
        
        # Register an agent
        agent_registered = await platform.register_agent("http://localhost:8080")
        assert agent_registered is True
        
        # Submit a task
        task_id = await platform.submit_task(sample_task)
        assert task_id == "test-task-123"
        
        # Verify calls were made
        platform.agent_registry.register_agent.assert_called_once()
        platform.task_scheduler.submit_task.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
