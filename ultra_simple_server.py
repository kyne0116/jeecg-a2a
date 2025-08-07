#!/usr/bin/env python3
"""
Ultra simple A2A server for testing.
"""

import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(title="Ultra Simple A2A Platform", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
agents: Dict[str, Dict[str, Any]] = {}

class AgentRegistrationRequest(BaseModel):
    url: str
    force_refresh: bool = False

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "platform": {
            "name": "Ultra Simple A2A Platform",
            "version": "1.0.0"
        },
        "statistics": {
            "registered_agents": len(agents)
        }
    }

@app.get("/api/agents")
async def get_agents():
    """Get all agents."""
    return list(agents.values())

@app.post("/api/agents/register")
async def register_agent(request: AgentRegistrationRequest):
    """Register agent."""
    try:
        logger.info(f"Registering agent: {request.url}")
        
        # Fetch agent.json
        agent_json_url = f"{request.url.rstrip('/')}/.well-known/agent.json"
        response = requests.get(agent_json_url, timeout=10)
        
        if response.status_code != 200:
            return {
                "success": False,
                "message": f"Failed to fetch agent.json: HTTP {response.status_code}"
            }
        
        agent_data = response.json()
        
        # Generate ID
        agent_id = f"agent_{len(agents) + 1}"
        
        # Store agent
        agent_info = {
            "id": agent_id,
            "name": agent_data.get("name", "Unknown"),
            "url": request.url,
            "version": agent_data.get("version", "1.0.0"),
            "description": agent_data.get("description", ""),
            "capabilities": len(agent_data.get("capabilities", [])),
            "status": "active",
            "registered_at": datetime.now().isoformat()
        }
        
        agents[agent_id] = agent_info
        
        logger.info(f"Agent registered successfully: {agent_info['name']}")
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent '{agent_info['name']}' registered successfully",
            "agent_card": agent_info
        }
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return {
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }

@app.delete("/api/agents/unregister/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister agent."""
    if agent_id in agents:
        agent = agents.pop(agent_id)
        return {"success": True, "message": f"Agent {agent['name']} unregistered"}
    else:
        raise HTTPException(status_code=404, detail="Agent not found")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Ultra Simple A2A Platform",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "agents": "/api/agents",
            "register": "/api/agents/register",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Ultra Simple A2A Platform")
    print("📍 Starting on http://127.0.0.1:9000")
    print("🔗 Health: http://127.0.0.1:9000/health")
    print("🔗 Docs: http://127.0.0.1:9000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )
