"""
安全中间件

提供动态CORS、agent认证、请求限制等安全功能。
"""

import logging
import time
from typing import Dict, Set
from collections import defaultdict, deque
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from .cors_manager import cors_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全中间件
    
    功能：
    - 动态CORS处理
    - 请求频率限制
    - Agent认证验证
    - 安全日志记录
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # 请求频率限制
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque())
        self.blocked_ips: Set[str] = set()
        
        # 配置
        self.rate_limit_requests = 100  # 每分钟最大请求数
        self.rate_limit_window = 60     # 时间窗口（秒）
        self.block_duration = 300       # 阻止时长（秒）
        
        logger.info("Security Middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        start_time = time.time()
        
        try:
            # 1. 获取客户端IP
            client_ip = self._get_client_ip(request)
            
            # 2. 检查IP是否被阻止
            if self._is_ip_blocked(client_ip):
                return self._create_error_response(
                    "IP blocked due to rate limiting", 429
                )
            
            # 3. 请求频率限制
            if not self._check_rate_limit(client_ip):
                self._block_ip(client_ip)
                return self._create_error_response(
                    "Rate limit exceeded", 429
                )
            
            # 4. 处理CORS预检请求
            if request.method == "OPTIONS":
                return await self._handle_preflight(request)
            
            # 5. Agent注册请求特殊处理
            if request.url.path == "/api/agents/register":
                validation_result = await self._validate_agent_registration(request)
                if not validation_result[0]:
                    return self._create_error_response(validation_result[1], 403)
            
            # 6. 执行请求
            response = await call_next(request)
            
            # 7. 添加CORS头
            self._add_cors_headers(response, request)
            
            # 8. 记录请求日志
            process_time = time.time() - start_time
            self._log_request(request, response, process_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return self._create_error_response("Internal server error", 500)
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        try:
            # 检查代理头
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()

            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip

            # 使用客户端IP
            if request.client and hasattr(request.client, 'host') and request.client.host:
                return request.client.host

            # 默认返回localhost
            return "127.0.0.1"
        except Exception as e:
            logger.warning(f"Error getting client IP: {e}")
            return "127.0.0.1"
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """检查IP是否被阻止"""
        return ip in self.blocked_ips
    
    def _check_rate_limit(self, ip: str) -> bool:
        """检查请求频率限制"""
        now = time.time()
        requests = self.request_counts[ip]
        
        # 清理过期请求
        while requests and requests[0] < now - self.rate_limit_window:
            requests.popleft()
        
        # 检查是否超过限制
        if len(requests) >= self.rate_limit_requests:
            return False
        
        # 记录当前请求
        requests.append(now)
        return True
    
    def _block_ip(self, ip: str):
        """阻止IP"""
        self.blocked_ips.add(ip)
        logger.warning(f"Blocked IP due to rate limiting: {ip}")
        
        # 设置定时器解除阻止（简化实现）
        # 在生产环境中应该使用更好的方式管理阻止列表
    
    async def _handle_preflight(self, request: Request) -> Response:
        """处理CORS预检请求"""
        origin = request.headers.get("Origin")
        
        if not origin:
            return Response(status_code=400)
        
        # 检查origin是否被允许
        allowed_origins = cors_manager.get_allowed_origins()
        
        if origin in allowed_origins or "*" in allowed_origins:
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400"
            }
            return Response(status_code=200, headers=headers)
        else:
            return Response(status_code=403)
    
    async def _validate_agent_registration(self, request: Request) -> tuple[bool, str]:
        """验证agent注册请求"""
        try:
            # 获取请求体
            body = await request.body()
            if not body:
                return False, "Empty request body"
            
            import json
            data = json.loads(body)
            agent_url = data.get("url")
            
            if not agent_url:
                return False, "Missing agent URL"
            
            # 使用CORS管理器验证
            return cors_manager.validate_agent_registration(agent_url, {})
            
        except Exception as e:
            logger.error(f"Error validating agent registration: {e}")
            return False, f"Validation error: {str(e)}"
    
    def _add_cors_headers(self, response: Response, request: Request):
        """添加CORS头"""
        origin = request.headers.get("Origin")
        
        if origin:
            allowed_origins = cors_manager.get_allowed_origins()
            
            if origin in allowed_origins or "*" in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    
    def _create_error_response(self, message: str, status_code: int) -> JSONResponse:
        """创建错误响应"""
        return JSONResponse(
            status_code=status_code,
            content={"error": message, "status_code": status_code}
        )
    
    def _log_request(self, request: Request, response: Response, process_time: float):
        """记录请求日志"""
        client_ip = self._get_client_ip(request)
        
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "status_code": response.status_code,
            "process_time": round(process_time, 3),
            "user_agent": request.headers.get("User-Agent", ""),
            "origin": request.headers.get("Origin", "")
        }
        
        if response.status_code >= 400:
            logger.warning(f"Request failed: {log_data}")
        else:
            logger.debug(f"Request processed: {log_data}")


class AgentAuthMiddleware(BaseHTTPMiddleware):
    """
    Agent认证中间件
    
    专门处理agent间的认证和授权
    """
    
    def __init__(self, app):
        super().__init__(app)
        logger.info("Agent Auth Middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """处理agent认证"""
        
        # 检查是否为agent相关的API
        if not request.url.path.startswith("/api/agents/"):
            return await call_next(request)
        
        # 检查认证头
        auth_header = request.headers.get("Authorization")
        
        # 如果配置了注册token，验证token
        if settings.AGENT_REGISTRATION_TOKEN:
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Missing or invalid authorization header"}
                )
            
            token = auth_header.split("Bearer ")[1]
            if token != settings.AGENT_REGISTRATION_TOKEN:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Invalid registration token"}
                )
        
        return await call_next(request)
