#!/usr/bin/env python3
"""
最小化的a2a中台服务器，用于测试agent注册功能
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
from typing import Dict, List, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Minimal A2A Platform", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存存储
registered_agents: Dict[str, Dict[str, Any]] = {}

class AgentRegistrationRequest(BaseModel):
    url: str
    force_refresh: bool = False

class AgentRegistrationResponse(BaseModel):
    success: bool
    agent_id: str = ""
    message: str = ""
    agent_card: Dict[str, Any] = {}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "platform": {
            "name": "Minimal A2A Platform",
            "version": "1.0.0"
        },
        "statistics": {
            "registered_agents": len(registered_agents)
        }
    }

@app.get("/api/agents")
async def get_agents():
    """获取所有注册的agents"""
    return list(registered_agents.values())

@app.post("/api/agents/register", response_model=AgentRegistrationResponse)
async def register_agent(request: AgentRegistrationRequest):
    """注册agent"""
    try:
        logger.info(f"开始注册agent: {request.url}")
        
        # 1. 获取agent.json
        agent_json_url = f"{request.url.rstrip('/')}/.well-known/agent.json"
        logger.info(f"获取agent.json: {agent_json_url}")
        
        response = requests.get(agent_json_url, timeout=10)
        if response.status_code != 200:
            return AgentRegistrationResponse(
                success=False,
                message=f"无法获取agent.json: HTTP {response.status_code}"
            )
        
        agent_card = response.json()
        logger.info(f"成功获取agent.json: {agent_card.get('name')}")
        
        # 2. 验证必需字段
        required_fields = ["name", "url", "version"]
        for field in required_fields:
            if field not in agent_card:
                return AgentRegistrationResponse(
                    success=False,
                    message=f"agent.json缺少必需字段: {field}"
                )
        
        # 3. 生成agent ID
        agent_id = f"agent_{len(registered_agents) + 1}"
        
        # 4. 存储agent信息
        agent_info = {
            "id": agent_id,
            "url": request.url,
            "name": agent_card.get("name"),
            "version": agent_card.get("version"),
            "description": agent_card.get("description", ""),
            "capabilities": agent_card.get("capabilities", []),
            "status": "active",
            "registered_at": "2025-08-07T21:00:00Z"
        }
        
        registered_agents[agent_id] = agent_info
        
        logger.info(f"成功注册agent: {agent_info['name']} (ID: {agent_id})")
        
        return AgentRegistrationResponse(
            success=True,
            agent_id=agent_id,
            message=f"Agent '{agent_info['name']}' 注册成功",
            agent_card=agent_info
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求失败: {e}")
        return AgentRegistrationResponse(
            success=False,
            message=f"网络请求失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"注册过程中发生错误: {e}")
        return AgentRegistrationResponse(
            success=False,
            message=f"注册失败: {str(e)}"
        )

@app.delete("/api/agents/unregister/{agent_id}")
async def unregister_agent(agent_id: str):
    """注销agent"""
    if agent_id in registered_agents:
        agent_info = registered_agents.pop(agent_id)
        logger.info(f"成功注销agent: {agent_info['name']} (ID: {agent_id})")
        return {"success": True, "message": f"Agent {agent_info['name']} 注销成功"}
    else:
        raise HTTPException(status_code=404, detail="Agent not found")

@app.get("/api/agents/info/{agent_id}")
async def get_agent_info(agent_id: str):
    """获取agent详细信息"""
    if agent_id in registered_agents:
        return registered_agents[agent_id]
    else:
        raise HTTPException(status_code=404, detail="Agent not found")

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动最小化A2A平台...")
    print("📍 服务地址: http://127.0.0.1:9000")
    print("🔗 健康检查: http://127.0.0.1:9000/health")
    print("📋 Agent列表: http://127.0.0.1:9000/api/agents")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9000,
        log_level="info"
    )
