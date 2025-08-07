"""
动态CORS管理器

提供动态CORS配置管理、agent白名单管理、网络安全验证等功能。
"""

import json
import logging
import ipaddress
from typing import List, Set, Optional, Dict, Any
from urllib.parse import urlparse
import asyncio
from pathlib import Path

from config.settings import settings

logger = logging.getLogger(__name__)


class CORSManager:
    """
    动态CORS管理器
    
    功能：
    - 动态CORS配置管理
    - Agent白名单管理
    - 网络安全验证
    - 自动发现机制
    """
    
    def __init__(self):
        """初始化CORS管理器"""
        self.static_origins: Set[str] = set(settings.CORS_ORIGINS)
        self.dynamic_origins: Set[str] = set()
        self.agent_whitelist: Dict[str, Dict[str, Any]] = {}
        self.blocked_origins: Set[str] = set()

        # 加载配置
        self._load_agent_whitelist()

        # 将白名单中的agent添加到动态CORS列表
        self._sync_whitelist_to_cors()

        logger.info("CORS Manager initialized")
    
    def _load_agent_whitelist(self):
        """加载agent白名单配置"""
        try:
            whitelist_file = Path(settings.AGENT_WHITELIST_FILE)
            if whitelist_file.exists():
                with open(whitelist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.agent_whitelist = data.get('agents', {})
                    self.blocked_origins = set(data.get('blocked', []))
                logger.info(f"Loaded {len(self.agent_whitelist)} agents from whitelist")
            else:
                # 创建默认配置文件
                self._create_default_whitelist()
        except Exception as e:
            logger.error(f"Failed to load agent whitelist: {e}")
            self._create_default_whitelist()
    
    def _create_default_whitelist(self):
        """创建默认白名单配置文件"""
        try:
            whitelist_file = Path(settings.AGENT_WHITELIST_FILE)
            whitelist_file.parent.mkdir(parents=True, exist_ok=True)
            
            default_config = {
                "agents": {
                    "http://127.0.0.1:8888": {
                        "name": "CodeGen Expert",
                        "description": "JeecgBoot代码生成专家",
                        "trusted": True,
                        "auto_approved": True,
                        "created_at": "2025-08-07T00:00:00Z"
                    }
                },
                "blocked": [],
                "settings": {
                    "auto_approve_localhost": True,
                    "require_authentication": False,
                    "max_agents": 100
                }
            }
            
            with open(whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            self.agent_whitelist = default_config['agents']
            logger.info("Created default agent whitelist")
            
        except Exception as e:
            logger.error(f"Failed to create default whitelist: {e}")

    def _sync_whitelist_to_cors(self):
        """将白名单中的agent同步到CORS动态源列表"""
        for agent_url in self.agent_whitelist.keys():
            if agent_url not in self.blocked_origins:
                self.dynamic_origins.add(agent_url)
        logger.info(f"Synced {len(self.dynamic_origins)} agents to CORS origins")

    def _save_agent_whitelist(self):
        """保存agent白名单配置"""
        try:
            whitelist_file = Path(settings.AGENT_WHITELIST_FILE)
            
            config = {
                "agents": self.agent_whitelist,
                "blocked": list(self.blocked_origins),
                "settings": {
                    "auto_approve_localhost": True,
                    "require_authentication": False,
                    "max_agents": 100
                }
            }
            
            with open(whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info("Saved agent whitelist")
            
        except Exception as e:
            logger.error(f"Failed to save agent whitelist: {e}")
    
    def is_network_allowed(self, url: str) -> bool:
        """检查网络地址是否被允许"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                return False
            
            # 检查是否为localhost
            if hostname in ['localhost', '127.0.0.1', '::1']:
                return True
            
            # 检查是否在允许的网络范围内
            try:
                ip = ipaddress.ip_address(hostname)
                for network in settings.ALLOWED_NETWORKS:
                    if ip in ipaddress.ip_network(network):
                        return True
                
                # 如果是公网IP且禁止公网agent
                if settings.BLOCK_PUBLIC_AGENTS and ip.is_global:
                    return False
                    
            except ValueError:
                # 不是IP地址，可能是域名
                if settings.BLOCK_PUBLIC_AGENTS:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking network for {url}: {e}")
            return False
    
    def is_agent_whitelisted(self, url: str) -> bool:
        """检查agent是否在白名单中"""
        if not settings.AGENT_WHITELIST_ENABLED:
            return True
        
        return url in self.agent_whitelist
    
    def add_agent_to_whitelist(self, url: str, agent_info: Dict[str, Any]) -> bool:
        """添加agent到白名单"""
        try:
            # 网络安全检查
            if not self.is_network_allowed(url):
                logger.warning(f"Agent URL not in allowed networks: {url}")
                return False
            
            # 检查是否已被阻止
            if url in self.blocked_origins:
                logger.warning(f"Agent URL is blocked: {url}")
                return False
            
            # 添加到白名单
            self.agent_whitelist[url] = {
                "name": agent_info.get("name", "Unknown Agent"),
                "description": agent_info.get("description", ""),
                "trusted": agent_info.get("trusted", False),
                "auto_approved": True,
                "created_at": agent_info.get("created_at", ""),
                "last_seen": agent_info.get("last_seen", "")
            }
            
            # 添加到动态CORS列表
            self.dynamic_origins.add(url)
            
            # 保存配置
            self._save_agent_whitelist()
            
            logger.info(f"Added agent to whitelist: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add agent to whitelist: {e}")
            return False
    
    def remove_agent_from_whitelist(self, url: str) -> bool:
        """从白名单中移除agent"""
        try:
            if url in self.agent_whitelist:
                del self.agent_whitelist[url]
                self.dynamic_origins.discard(url)
                self._save_agent_whitelist()
                logger.info(f"Removed agent from whitelist: {url}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove agent from whitelist: {e}")
            return False
    
    def block_agent(self, url: str, reason: str = "") -> bool:
        """阻止agent"""
        try:
            self.blocked_origins.add(url)
            self.dynamic_origins.discard(url)
            if url in self.agent_whitelist:
                del self.agent_whitelist[url]
            
            self._save_agent_whitelist()
            logger.warning(f"Blocked agent: {url}, reason: {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to block agent: {e}")
            return False
    
    def get_allowed_origins(self) -> List[str]:
        """获取所有允许的CORS源"""
        if settings.ENABLE_DYNAMIC_CORS:
            # 合并静态和动态源
            all_origins = self.static_origins.union(self.dynamic_origins)
            # 移除被阻止的源
            return list(all_origins - self.blocked_origins)
        else:
            return list(self.static_origins)
    
    def validate_agent_registration(self, url: str, agent_card: Dict[str, Any]) -> tuple[bool, str]:
        """验证agent注册请求"""
        try:
            # 1. 网络安全检查
            if not self.is_network_allowed(url):
                return False, "Agent URL not in allowed networks"
            
            # 2. 检查是否被阻止
            if url in self.blocked_origins:
                return False, "Agent URL is blocked"
            
            # 3. 白名单检查
            if settings.AGENT_WHITELIST_ENABLED and not self.is_agent_whitelisted(url):
                return False, "Agent not in whitelist"
            
            # 4. 认证检查（如果启用）
            if settings.AGENT_REGISTRATION_TOKEN:
                # 这里可以添加token验证逻辑
                pass
            
            # 5. Agent卡片验证
            required_fields = ['name', 'version', 'url']
            for field in required_fields:
                if field not in agent_card:
                    return False, f"Missing required field: {field}"
            
            return True, "Validation passed"
            
        except Exception as e:
            logger.error(f"Error validating agent registration: {e}")
            return False, f"Validation error: {str(e)}"
    
    async def auto_discover_agents(self, network_range: str = "192.168.1.0/24") -> List[str]:
        """自动发现网络中的agents"""
        if not settings.AGENT_AUTO_DISCOVERY:
            return []
        
        discovered_agents = []
        try:
            network = ipaddress.ip_network(network_range)
            
            # 这里可以实现网络扫描逻辑
            # 扫描常用端口（8080, 8888, 9000等）查找agent.json
            common_ports = [8080, 8888, 9000, 3000]
            
            for ip in network.hosts():
                for port in common_ports:
                    url = f"http://{ip}:{port}"
                    # 这里可以添加异步HTTP请求检查agent.json
                    # 为了示例，暂时跳过实际实现
                    pass
            
            logger.info(f"Auto-discovered {len(discovered_agents)} agents")
            return discovered_agents
            
        except Exception as e:
            logger.error(f"Error in auto-discovery: {e}")
            return []


# 全局CORS管理器实例
cors_manager = CORSManager()
