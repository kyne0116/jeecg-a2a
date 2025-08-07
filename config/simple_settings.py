"""
Simplified and stable configuration for A2A Platform.
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class SimpleSettings(BaseSettings):
    """
    Simplified application settings for maximum stability.
    """
    
    # Application Configuration
    APP_NAME: str = "JEECG A2A Platform"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Enterprise A2A Protocol Platform"
    DEBUG: bool = True
    
    # Server Configuration
    HOST: str = "0.0.0.0"  # 监听所有接口
    PORT: int = 9000
    RELOAD: bool = False  # 禁用热重载
    
    # Platform Configuration
    MAX_CONCURRENT_TASKS: int = 50  # 降低并发数
    AGENT_TIMEOUT: int = 30
    
    # CORS Configuration - 预设常用地址
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:9000", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:9000",
        "http://127.0.0.1:8888",  # CodeGen Expert agent
        "http://localhost:8888"
    ]
    
    # Agent Management
    AGENT_WHITELIST_FILE: str = "./config/agent_whitelist.json"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Static Files
    STATIC_DIR: str = "ui/static"
    TEMPLATES_DIR: str = "ui/templates"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外字段


# Global settings instance
settings = SimpleSettings()
