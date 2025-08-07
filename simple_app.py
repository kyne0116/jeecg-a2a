"""
Simplified A2A Platform Application.

This is a completely rewritten, stable version of the A2A platform
focused on reliability and core functionality.
"""

import logging
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.simple_settings import settings
from api.simple_routes import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    debug=settings.DEBUG
)

# CORS middleware - simplified configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],  # Allow all for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Static files
static_dir = Path(settings.STATIC_DIR)
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Mounted static files from {static_dir}")

# Templates
templates_dir = Path(settings.TEMPLATES_DIR)
if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))
    logger.info(f"Loaded templates from {templates_dir}")
else:
    templates = None
    logger.warning(f"Templates directory not found: {templates_dir}")


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Chat interface page."""
    if templates:
        return templates.TemplateResponse("chat.html", {"request": request})
    else:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>A2A Platform - Agent Management</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; text-align: center; margin-bottom: 30px; }
                .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
                .button:hover { background: #0056b3; }
                .input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin: 5px 0; }
                .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
                .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                .agent-list { margin-top: 20px; }
                .agent-item { padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 JEECG A2A Platform</h1>
                
                <div class="section">
                    <h2>Agent Registration</h2>
                    <input type="text" id="agentUrl" class="input" placeholder="Enter agent URL (e.g., http://127.0.0.1:8888)" value="http://127.0.0.1:8888">
                    <button class="button" onclick="registerAgent()">Register Agent</button>
                    <button class="button" onclick="loadAgents()">Refresh Agent List</button>
                    <div id="status"></div>
                </div>
                
                <div class="section">
                    <h2>Registered Agents</h2>
                    <div id="agentList" class="agent-list">
                        <p>Loading agents...</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Platform Status</h2>
                    <button class="button" onclick="checkHealth()">Check Health</button>
                    <div id="healthStatus"></div>
                </div>
            </div>
            
            <script>
                // Load agents on page load
                window.onload = function() {
                    loadAgents();
                    checkHealth();
                };
                
                async function registerAgent() {
                    const url = document.getElementById('agentUrl').value;
                    const statusDiv = document.getElementById('status');
                    
                    if (!url) {
                        statusDiv.innerHTML = '<div class="status error">Please enter an agent URL</div>';
                        return;
                    }
                    
                    try {
                        statusDiv.innerHTML = '<div class="status">Registering agent...</div>';
                        
                        const response = await fetch('/api/agents/register', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                url: url,
                                force_refresh: false
                            })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            statusDiv.innerHTML = `<div class="status success">✅ ${result.message}</div>`;
                            loadAgents(); // Refresh agent list
                        } else {
                            statusDiv.innerHTML = `<div class="status error">❌ ${result.message}</div>`;
                        }
                    } catch (error) {
                        statusDiv.innerHTML = `<div class="status error">❌ Error: ${error.message}</div>`;
                    }
                }
                
                async function loadAgents() {
                    const agentListDiv = document.getElementById('agentList');
                    
                    try {
                        agentListDiv.innerHTML = '<p>Loading agents...</p>';
                        
                        const response = await fetch('/api/agents');
                        const agents = await response.json();
                        
                        if (agents.length === 0) {
                            agentListDiv.innerHTML = '<p>No agents registered yet.</p>';
                        } else {
                            let html = '';
                            agents.forEach(agent => {
                                html += `
                                    <div class="agent-item">
                                        <h3>${agent.name}</h3>
                                        <p><strong>URL:</strong> ${agent.url}</p>
                                        <p><strong>Version:</strong> ${agent.version}</p>
                                        <p><strong>Status:</strong> ${agent.status}</p>
                                        <p><strong>Capabilities:</strong> ${agent.capabilities.length}</p>
                                        <button class="button" onclick="unregisterAgent('${agent.id}')">Unregister</button>
                                    </div>
                                `;
                            });
                            agentListDiv.innerHTML = html;
                        }
                    } catch (error) {
                        agentListDiv.innerHTML = `<p class="error">Error loading agents: ${error.message}</p>`;
                    }
                }
                
                async function unregisterAgent(agentId) {
                    if (!confirm('Are you sure you want to unregister this agent?')) {
                        return;
                    }
                    
                    try {
                        const response = await fetch(`/api/agents/unregister/${agentId}`, {
                            method: 'DELETE'
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            loadAgents(); // Refresh agent list
                        } else {
                            alert('Failed to unregister agent');
                        }
                    } catch (error) {
                        alert(`Error: ${error.message}`);
                    }
                }
                
                async function checkHealth() {
                    const healthDiv = document.getElementById('healthStatus');
                    
                    try {
                        const response = await fetch('/health');
                        const health = await response.json();
                        
                        healthDiv.innerHTML = `
                            <div class="status success">
                                <strong>Status:</strong> ${health.status}<br>
                                <strong>Registered Agents:</strong> ${health.statistics.registered_agents}<br>
                                <strong>Platform:</strong> ${health.platform.name} v${health.platform.version}
                            </div>
                        `;
                    } catch (error) {
                        healthDiv.innerHTML = `<div class="status error">Health check failed: ${error.message}</div>`;
                    }
                }
            </script>
        </body>
        </html>
        """)


@app.get("/", response_class=RedirectResponse)
async def root_redirect():
    """Redirect root to chat page."""
    return RedirectResponse(url="/chat")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup."""
    logger.info("🚀 Starting JEECG A2A Platform...")
    logger.info(f"📍 Server: {settings.HOST}:{settings.PORT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    logger.info(f"🌐 CORS origins: {len(settings.CORS_ORIGINS)} configured")
    logger.info("✅ Platform started successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown."""
    logger.info("🛑 Shutting down JEECG A2A Platform...")
    logger.info("✅ Platform shutdown complete")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 JEECG A2A Platform")
    print(f"📍 Starting server on {settings.HOST}:{settings.PORT}")
    print(f"🔗 Access: http://{settings.HOST}:{settings.PORT}")
    print("=" * 60)
    
    uvicorn.run(
        "simple_app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
