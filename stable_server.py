#!/usr/bin/env python3
"""
最稳定的A2A服务器版本
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# 最小化导入，避免依赖问题
try:
    import requests
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    print(f"导入错误: {e}")
    print("请安装必要的依赖: pip install fastapi uvicorn requests")
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
    title="Stable A2A Platform",
    version="1.0.0",
    description="稳定的A2A平台"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存存储
agents_storage: Dict[str, Dict[str, Any]] = {}
agent_counter = 0

# 数据模型
class AgentRegistrationRequest(BaseModel):
    url: str
    force_refresh: bool = False

class AgentRegistrationResponse(BaseModel):
    success: bool
    agent_id: str = ""
    message: str = ""
    agent_card: Optional[Dict[str, Any]] = None

# API端点
@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "Stable A2A Platform",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "agents": "/api/agents",
            "register": "/api/agents/register",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "platform": {
                "name": "Stable A2A Platform",
                "version": "1.0.0",
                "description": "稳定的A2A平台"
            },
            "statistics": {
                "registered_agents": len(agents_storage),
                "active_tasks": 0,
                "uptime": "running"
            }
        }
    except Exception as e:
        logger.error(f"健康检查错误: {e}")
        raise HTTPException(status_code=500, detail="健康检查失败")

@app.get("/api/agents")
async def get_agents():
    """获取所有注册的agents"""
    try:
        agents_list = list(agents_storage.values())
        logger.info(f"返回 {len(agents_list)} 个agents")
        return agents_list
    except Exception as e:
        logger.error(f"获取agents列表错误: {e}")
        raise HTTPException(status_code=500, detail="获取agents列表失败")

@app.post("/api/agents/register")
async def register_agent(request: AgentRegistrationRequest):
    """注册agent"""
    global agent_counter
    
    try:
        logger.info(f"开始注册agent: {request.url}")
        
        # 检查是否已注册
        existing_agent = None
        for agent_id, agent in agents_storage.items():
            if agent.get("url") == request.url:
                existing_agent = (agent_id, agent)
                break
        
        if existing_agent and not request.force_refresh:
            logger.info(f"Agent已存在: {existing_agent[0]}")
            return AgentRegistrationResponse(
                success=True,
                agent_id=existing_agent[0],
                message="Agent已经注册",
                agent_card=existing_agent[1]
            ).dict()
        
        # 获取agent.json
        agent_json_url = f"{request.url.rstrip('/')}/.well-known/agent.json"
        logger.info(f"获取agent.json: {agent_json_url}")
        
        try:
            response = requests.get(agent_json_url, timeout=15)
            if response.status_code != 200:
                logger.error(f"获取agent.json失败: HTTP {response.status_code}")
                return AgentRegistrationResponse(
                    success=False,
                    message=f"无法获取agent.json: HTTP {response.status_code}"
                ).dict()
            
            agent_data = response.json()
            logger.info(f"成功获取agent数据: {agent_data.get('name', 'Unknown')}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return AgentRegistrationResponse(
                success=False,
                message=f"网络请求失败: {str(e)}"
            ).dict()
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return AgentRegistrationResponse(
                success=False,
                message="agent.json格式无效"
            ).dict()
        
        # 生成agent ID
        if existing_agent:
            agent_id = existing_agent[0]
        else:
            agent_counter += 1
            agent_id = f"agent_{agent_counter}"
        
        # 创建agent信息
        agent_info = {
            "id": agent_id,
            "name": agent_data.get("name", "Unknown Agent"),
            "url": request.url,
            "version": agent_data.get("version", "1.0.0"),
            "description": agent_data.get("description", ""),
            "capabilities": len(agent_data.get("capabilities", [])),
            "status": "active",
            "registered_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "metadata": {
                "original_data": agent_data.get("metadata", {}),
                "endpoints": agent_data.get("endpoints", {}),
                "protocols": agent_data.get("protocols", {})
            }
        }
        
        # 存储agent
        agents_storage[agent_id] = agent_info
        
        logger.info(f"Agent注册成功: {agent_info['name']} (ID: {agent_id})")
        
        return AgentRegistrationResponse(
            success=True,
            agent_id=agent_id,
            message=f"Agent '{agent_info['name']}' 注册成功",
            agent_card=agent_info
        ).dict()
        
    except Exception as e:
        logger.error(f"注册过程中发生错误: {e}")
        return AgentRegistrationResponse(
            success=False,
            message=f"注册失败: {str(e)}"
        ).dict()

@app.delete("/api/agents/unregister/{agent_id}")
async def unregister_agent(agent_id: str):
    """注销agent"""
    try:
        if agent_id in agents_storage:
            agent = agents_storage.pop(agent_id)
            logger.info(f"Agent注销成功: {agent['name']} (ID: {agent_id})")
            return {
                "success": True,
                "message": f"Agent '{agent['name']}' 注销成功",
                "agent_id": agent_id
            }
        else:
            logger.warning(f"尝试注销不存在的agent: {agent_id}")
            raise HTTPException(status_code=404, detail="Agent not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注销agent时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"注销失败: {str(e)}")

@app.get("/api/agents/info/{agent_id}")
async def get_agent_info(agent_id: str):
    """获取agent详细信息"""
    try:
        if agent_id in agents_storage:
            return agents_storage[agent_id]
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取agent信息时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}")

@app.get("/api/platform/stats")
async def get_platform_stats():
    """获取平台统计信息"""
    try:
        active_agents = sum(1 for agent in agents_storage.values() if agent.get("status") == "active")
        return {
            "total_agents": len(agents_storage),
            "active_agents": active_agents,
            "platform_status": "running",
            "last_updated": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"获取平台统计信息时发生错误: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")

# 启动函数
def start_server():
    """启动服务器"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 启动稳定的A2A平台")
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
            reload=False  # 禁用热重载确保稳定性
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 服务器被用户停止")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()
