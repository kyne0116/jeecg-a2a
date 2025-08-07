"""
Configuration settings for JEECG A2A Platform.
"""

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=9000, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Platform Configuration
    PLATFORM_NAME: str = Field(default="JEECG A2A Platform", env="PLATFORM_NAME")
    PLATFORM_VERSION: str = Field(default="1.0.0", env="PLATFORM_VERSION")
    PLATFORM_DESCRIPTION: str = Field(
        default="Enterprise A2A Protocol Platform", 
        env="PLATFORM_DESCRIPTION"
    )
    
    # Agent Configuration
    AGENT_TIMEOUT: int = Field(default=30, env="AGENT_TIMEOUT")
    MAX_CONCURRENT_TASKS: int = Field(default=100, env="MAX_CONCURRENT_TASKS")
    AGENT_HEALTH_CHECK_INTERVAL: int = Field(default=60, env="AGENT_HEALTH_CHECK_INTERVAL")
    AUTO_DISCOVERY_ENABLED: bool = Field(default=True, env="AUTO_DISCOVERY_ENABLED")
    
    # AI Provider Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    
    # Database Configuration
    DATABASE_URL: str = Field(default="sqlite:///./jeecg_a2a.db", env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Security Configuration
    SECRET_KEY: str = Field(default="your_secret_key_here", env="SECRET_KEY")
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:9000"],
        env="CORS_ORIGINS"
    )

    # Dynamic Agent Management Configuration
    ENABLE_DYNAMIC_CORS: bool = Field(default=True, env="ENABLE_DYNAMIC_CORS")
    AGENT_WHITELIST_ENABLED: bool = Field(default=True, env="AGENT_WHITELIST_ENABLED")
    AGENT_WHITELIST_FILE: str = Field(default="./config/agent_whitelist.json", env="AGENT_WHITELIST_FILE")
    AGENT_AUTO_DISCOVERY: bool = Field(default=False, env="AGENT_AUTO_DISCOVERY")
    AGENT_REGISTRATION_TOKEN: Optional[str] = Field(default=None, env="AGENT_REGISTRATION_TOKEN")

    # Network Security Configuration
    ALLOWED_NETWORKS: List[str] = Field(
        default=["127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
        env="ALLOWED_NETWORKS"
    )
    BLOCK_PUBLIC_AGENTS: bool = Field(default=True, env="BLOCK_PUBLIC_AGENTS")
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Chat UI Configuration
    CHAT_HISTORY_LIMIT: int = Field(default=1000, env="CHAT_HISTORY_LIMIT")
    SESSION_TIMEOUT: int = Field(default=3600, env="SESSION_TIMEOUT")
    ENABLE_FILE_UPLOAD: bool = Field(default=True, env="ENABLE_FILE_UPLOAD")
    MAX_FILE_SIZE: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    WS_MAX_CONNECTIONS: int = Field(default=1000, env="WS_MAX_CONNECTIONS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the platform."""
        return f"http://{self.HOST}:{self.PORT}"
    
    @property
    def agent_card_url(self) -> str:
        """Get the agent card URL."""
        return f"{self.base_url}/.well-known/agent.json"
    
    def is_ai_enabled(self) -> bool:
        """Check if any AI provider is configured."""
        return any([
            self.OPENAI_API_KEY,
            self.ANTHROPIC_API_KEY,
            self.GOOGLE_API_KEY
        ])


# Global settings instance
settings = Settings()
