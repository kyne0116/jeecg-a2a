#!/usr/bin/env python3
"""
简单的A2A测试服务器
"""

import json
import logging
import sys
from typing import Dict, List, Any, Optional

try:
    import httpx
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    print(f"导入错误: {e}")
    print("请安装必要的依赖: pip install fastapi uvicorn httpx")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 创建应用
app = FastAPI(
    title="Test A2A Platform",
    version="1.0.0",
    description="简单的A2A测试平台"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储注册的agents
registered_agents: Dict[str, Dict[str, Any]] = {}

class AgentRegistrationRequest(BaseModel):
    url: str
    force_refresh: bool = False

class AgentRegistrationResponse(BaseModel):
    success: bool
    agent_id: str
    message: str
    agent_card: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "platform": "Test A2A Platform",
        "version": "1.0.0",
        "agents_count": len(registered_agents)
    }

@app.post("/api/agents/register", response_model=AgentRegistrationResponse)
async def register_agent(request: AgentRegistrationRequest):
    """注册agent"""
    try:
        logger.info(f"尝试注册agent: {request.url}")
        
        # 构建agent卡片URL
        agent_url = request.url.rstrip('/')
        if not agent_url.startswith(('http://', 'https://')):
            agent_url = f"http://{agent_url}"
        
        card_url = f"{agent_url}/.well-known/agent.json"
        
        # 获取agent卡片
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(card_url)
            response.raise_for_status()
            agent_card = response.json()
        
        # 生成agent ID
        agent_id = str(hash(agent_url))
        
        # 存储agent信息
        registered_agents[agent_id] = {
            "url": agent_url,
            "card": agent_card,
            "registered_at": "2025-08-07T23:08:00Z"
        }
        
        logger.info(f"成功注册agent: {agent_card.get('name', 'Unknown')} ({agent_url})")
        
        return AgentRegistrationResponse(
            success=True,
            agent_id=agent_id,
            message="Agent注册成功",
            agent_card=agent_card
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP错误获取agent卡片: {e}")
        return AgentRegistrationResponse(
            success=False,
            agent_id="",
            message=f"HTTP错误: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        logger.error(f"请求错误: {e}")
        return AgentRegistrationResponse(
            success=False,
            agent_id="",
            message=f"连接错误: {str(e)}"
        )
    except Exception as e:
        logger.error(f"注册agent时发生错误: {e}")
        return AgentRegistrationResponse(
            success=False,
            agent_id="",
            message=f"注册失败: {str(e)}"
        )

@app.get("/api/agents")
async def list_agents():
    """列出所有注册的agents"""
    return {
        "agents": list(registered_agents.values()),
        "count": len(registered_agents)
    }

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Test A2A Platform",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "register_agent": "/api/agents/register",
            "list_agents": "/api/agents"
        }
    }

def start_server():
    """启动服务器"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 启动测试A2A平台")
        logger.info("📍 服务地址: http://127.0.0.1:9000")
        logger.info("🔗 健康检查: http://127.0.0.1:9000/health")
        logger.info("📋 Agent列表: http://127.0.0.1:9000/api/agents")
        logger.info("📖 API文档: http://127.0.0.1:9000/docs")
        logger.info("=" * 60)
        
        # 启动服务器
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=9000,
            log_level="info",
            access_log=True,
            reload=False
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 服务器被用户停止")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()
