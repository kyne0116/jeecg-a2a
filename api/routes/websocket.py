"""
WebSocket endpoints for real-time communication.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from config.settings import settings
from core.platform import platform
from core.protocol.models import Message, Part, PartType, Role, Task, TaskRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def serialize_for_json(obj):
    """Convert objects to JSON-serializable format."""
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'dict'):  # Pydantic model
        return serialize_for_json(obj.dict())
    else:
        return obj

# Connection management
class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, Set[str]] = {}  # session_id -> set of connection_ids
    
    async def connect(self, websocket: WebSocket, connection_id: str, session_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(connection_id)
        
        logger.info(f"WebSocket connection established: {connection_id}")
    
    def disconnect(self, connection_id: str, session_id: str = None):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if session_id and session_id in self.session_connections:
            self.session_connections[session_id].discard(connection_id)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
        
        logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                # Serialize message to handle datetime objects
                serialized_message = serialize_for_json(message)
                await self.active_connections[connection_id].send_text(json.dumps(serialized_message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_session_message(self, message: dict, session_id: str):
        """Send a message to all connections in a session."""
        if session_id in self.session_connections:
            disconnected = []
            for connection_id in self.session_connections[session_id]:
                try:
                    await self.send_personal_message(message, connection_id)
                except Exception as e:
                    logger.error(f"Error sending to connection {connection_id}: {e}")
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected:
                self.disconnect(connection_id, session_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connections."""
        disconnected = []
        for connection_id in list(self.active_connections.keys()):
            try:
                await self.send_personal_message(message, connection_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for chat communication.
    
    Args:
        websocket: WebSocket connection
        session_id: Session ID for grouping connections
    """
    connection_id = str(uuid.uuid4())
    
    try:
        await manager.connect(websocket, connection_id, session_id)
        
        # Send welcome message
        await manager.send_personal_message({
            "type": "system",
            "message": "Connected to JEECG A2A Platform",
            "session_id": session_id,
            "connection_id": connection_id
        }, connection_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process the message
            await process_websocket_message(message_data, connection_id, session_id)
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id, session_id)
        logger.info(f"Client {connection_id} disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id, session_id)


async def process_websocket_message(message_data: dict, connection_id: str, session_id: str):
    """
    Process a message received via WebSocket.
    
    Args:
        message_data: Message data from client
        connection_id: WebSocket connection ID
        session_id: Session ID
    """
    try:
        message_type = message_data.get("type", "chat")
        
        if message_type == "chat":
            await handle_chat_message(message_data, connection_id, session_id)
        elif message_type == "task_status":
            await handle_task_status_request(message_data, connection_id, session_id)
        elif message_type == "agent_list":
            await handle_agent_list_request(message_data, connection_id, session_id)
        elif message_type == "ping":
            await handle_ping(message_data, connection_id, session_id)
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }, connection_id)
            
    except Exception as e:
        logger.error(f"Error processing WebSocket message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Error processing message: {str(e)}"
        }, connection_id)


async def handle_chat_message(message_data: dict, connection_id: str, session_id: str):
    """Handle chat message and submit as task."""
    try:
        content = message_data.get("content", "")
        if not content:
            return
        
        # NOTE: 不再回显用户消息，避免前端已添加本地消息后再次收到服务端回传而重复显示
        # （如需广播到同会话的其他连接，可在此按需实现定向发送，排除当前connection_id）

        # Create A2A task
        part = Part(type=PartType.TEXT, content=content)
        message = Message(role=Role.USER, parts=[part])
        
        task_request = TaskRequest(
            message=message,
            context_id=connection_id,
            session_id=session_id
        )
        
        task = Task(
            id=str(uuid.uuid4()),
            message=task_request.message,
            context_id=task_request.context_id,
            session_id=task_request.session_id,
            metadata=task_request.metadata
        )
        
        # Check if there are any available agents first
        agents = await platform.list_agents()
        active_agents = [agent for agent in agents if agent.status == "active"]

        if not active_agents:
            # Try to auto-register default agent if none available
            try:
                default_agent_url = "http://127.0.0.1:8888"
                registration_result = await platform.register_agent(default_agent_url)

                if registration_result.success:
                    await manager.send_session_message({
                        "type": "message",
                        "role": "system",
                        "content": f"✅ 已自动注册默认代理: {registration_result.agent_card.name}",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }, session_id)
                else:
                    # No agents available - provide helpful response
                    await manager.send_session_message({
                        "type": "message",
                        "role": "system",
                        "content": "⚠️ 当前没有可用的代理服务。请确保至少有一个代理已注册并处于活跃状态。\n\n您可以：\n• 检查代理服务是否正在运行 (http://127.0.0.1:8888)\n• 访问 /chat/agents 页面查看代理状态\n• 手动注册新的代理服务",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }, session_id)
                    return
            except Exception as e:
                logger.error(f"Failed to auto-register default agent: {e}")
                await manager.send_session_message({
                    "type": "message",
                    "role": "system",
                    "content": "⚠️ 当前没有可用的代理服务，且自动注册失败。请手动启动代理服务或访问 /chat/agents 页面进行配置。",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }, session_id)
                return

        # Submit task
        task_id = await platform.submit_task(task)

        # Send task submitted notification
        await manager.send_session_message({
            "type": "task_submitted",
            "task_id": task_id,
            "message": "Task submitted for processing",
            "session_id": session_id
        }, session_id)

        # Monitor task progress
        asyncio.create_task(monitor_task_progress(task_id, session_id))
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Error processing chat message: {str(e)}"
        }, connection_id)


async def handle_task_status_request(message_data: dict, connection_id: str, session_id: str):
    """Handle task status request."""
    try:
        task_id = message_data.get("task_id")
        if not task_id:
            await manager.send_personal_message({
                "type": "error",
                "message": "Task ID is required"
            }, connection_id)
            return
        
        status = await platform.get_task_status(task_id)
        
        await manager.send_personal_message({
            "type": "task_status",
            "task_id": task_id,
            "status": status.dict() if status else None
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Error handling task status request: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Error getting task status: {str(e)}"
        }, connection_id)


async def handle_agent_list_request(message_data: dict, connection_id: str, session_id: str):
    """Handle agent list request."""
    try:
        agents = await platform.list_agents()
        
        agent_list = []
        for agent in agents:
            agent_list.append({
                "name": agent.name,
                "description": agent.description,
                "url": agent.url,
                "status": agent.status,
                "capabilities": [cap.name for cap in agent.capabilities]
            })
        
        await manager.send_personal_message({
            "type": "agent_list",
            "agents": agent_list
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Error handling agent list request: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Error getting agent list: {str(e)}"
        }, connection_id)


async def handle_ping(message_data: dict, connection_id: str, session_id: str):
    """Handle ping message."""
    await manager.send_personal_message({
        "type": "pong",
        "timestamp": message_data.get("timestamp")
    }, connection_id)


async def monitor_task_progress(task_id: str, session_id: str):
    """Monitor task progress and send updates via WebSocket."""
    try:
        sent_messages = set()  # Track sent messages to prevent duplicates

        while True:
            status = await platform.get_task_status(task_id)

            if not status:
                break

            # Send status update (serialize datetime objects)
            status_data = serialize_for_json(status.dict())
            await manager.send_session_message({
                "type": "task_update",
                "task_id": task_id,
                "status": status_data,
                "session_id": session_id
            }, session_id)

            # Check if task is complete
            if status.state in ["completed", "failed", "cancelled"]:
                # Get full task for final response
                task = platform.task_scheduler.active_tasks.get(task_id)
                if task and task.history:
                    # Send agent response (only new messages)
                    for msg in task.history:
                        if msg.role == Role.AGENT:
                            for part in msg.parts:
                                if part.type == PartType.TEXT:
                                    # Create unique message identifier
                                    msg_id = f"{task_id}-{msg.role}-{part.content[:50]}"
                                    if msg_id not in sent_messages:
                                        await manager.send_session_message({
                                            "type": "message",
                                            "role": "agent",
                                            "content": part.content,
                                            "task_id": task_id,
                                            "session_id": session_id,
                                            "timestamp": status.updated_at.isoformat() if status.updated_at else None
                                        }, session_id)
                                        sent_messages.add(msg_id)
                break
            
            # Wait before next check
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error monitoring task progress {task_id}: {e}")
        await manager.send_session_message({
            "type": "error",
            "message": f"Error monitoring task: {str(e)}",
            "task_id": task_id
        }, session_id)
