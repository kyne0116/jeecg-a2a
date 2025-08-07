#!/usr/bin/env python3
"""
Agent注册自动化测试脚本
"""

import requests
import json
import time
from datetime import datetime

def log_message(message):
    """记录日志消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_agent_registration():
    """测试agent注册功能"""
    
    # 测试配置
    a2a_base_url = "http://127.0.0.1:9000"
    agent_url = "http://127.0.0.1:8888"
    
    log_message("开始agent注册自动化测试")
    
    # 1. 测试a2a中台健康状态
    log_message("1. 测试a2a中台健康状态...")
    try:
        response = requests.get(f"{a2a_base_url}/health", timeout=10)
        log_message(f"   a2a中台健康检查: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            log_message(f"   平台状态: {health_data.get('status')}")
        else:
            log_message(f"   错误: a2a中台健康检查失败")
            return False
    except Exception as e:
        log_message(f"   错误: 无法连接a2a中台 - {e}")
        return False
    
    # 2. 测试agent健康状态
    log_message("2. 测试agent健康状态...")
    try:
        response = requests.get(f"{agent_url}/.well-known/agent.json", timeout=10)
        log_message(f"   agent.json访问: {response.status_code}")
        if response.status_code == 200:
            agent_data = response.json()
            log_message(f"   Agent名称: {agent_data.get('name')}")
            log_message(f"   Agent版本: {agent_data.get('version')}")
            log_message(f"   Agent状态: {agent_data.get('status', {}).get('health')}")
        else:
            log_message(f"   错误: agent.json访问失败")
            return False
    except Exception as e:
        log_message(f"   错误: 无法访问agent - {e}")
        return False
    
    # 3. 检查CORS配置
    log_message("3. 检查CORS配置...")
    try:
        response = requests.get(f"{a2a_base_url}/api/agents/whitelist", timeout=10)
        log_message(f"   白名单API访问: {response.status_code}")
        if response.status_code == 200:
            whitelist_data = response.json()
            allowed_origins = whitelist_data.get('allowed_origins', [])
            log_message(f"   允许的CORS源: {allowed_origins}")
            if agent_url in allowed_origins:
                log_message(f"   ✅ agent URL已在CORS白名单中")
            else:
                log_message(f"   ❌ agent URL不在CORS白名单中")
        else:
            log_message(f"   错误: 白名单API访问失败")
    except Exception as e:
        log_message(f"   错误: 无法访问白名单API - {e}")
    
    # 4. 测试agent注册API
    log_message("4. 测试agent注册API...")
    try:
        # 准备注册请求
        register_payload = {
            "url": agent_url,
            "force_refresh": False
        }
        
        log_message(f"   发送注册请求: {json.dumps(register_payload, indent=2)}")
        
        # 发送注册请求
        response = requests.post(
            f"{a2a_base_url}/api/agents/register",
            json=register_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        log_message(f"   注册API响应状态: {response.status_code}")
        log_message(f"   响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            log_message(f"   注册响应: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            if response_data.get('success'):
                log_message(f"   ✅ Agent注册成功!")
                log_message(f"   Agent ID: {response_data.get('agent_id')}")
                log_message(f"   消息: {response_data.get('message')}")
                return True
            else:
                log_message(f"   ❌ Agent注册失败: {response_data.get('message')}")
                return False
        else:
            log_message(f"   ❌ 注册API调用失败")
            log_message(f"   响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        log_message(f"   ❌ 注册请求超时")
        return False
    except requests.exceptions.ConnectionError as e:
        log_message(f"   ❌ 连接错误: {e}")
        return False
    except Exception as e:
        log_message(f"   ❌ 注册过程中发生错误: {e}")
        return False
    
    # 5. 验证注册结果
    log_message("5. 验证注册结果...")
    try:
        response = requests.get(f"{a2a_base_url}/api/agents", timeout=10)
        if response.status_code == 200:
            agents = response.json()
            log_message(f"   当前注册的agents数量: {len(agents)}")
            for agent in agents:
                log_message(f"   - {agent.get('name')} ({agent.get('url')})")
        else:
            log_message(f"   无法获取agents列表: {response.status_code}")
    except Exception as e:
        log_message(f"   验证注册结果时发生错误: {e}")

def test_network_connectivity():
    """测试网络连通性"""
    log_message("开始网络连通性测试")
    
    # 测试从a2a中台到agent的连接
    agent_url = "http://127.0.0.1:8888"
    
    # 测试不同的端点
    endpoints_to_test = [
        "/.well-known/agent.json",
        "/health",
        "/codegen/status"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            full_url = f"{agent_url}{endpoint}"
            log_message(f"测试端点: {full_url}")
            
            response = requests.get(full_url, timeout=10)
            log_message(f"  状态码: {response.status_code}")
            log_message(f"  响应大小: {len(response.content)} bytes")
            
            if response.status_code == 200:
                log_message(f"  ✅ 端点可访问")
            else:
                log_message(f"  ❌ 端点返回错误状态")
                
        except Exception as e:
            log_message(f"  ❌ 端点访问失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Agent注册自动化测试")
    print("=" * 60)
    
    # 执行测试
    success = test_agent_registration()
    
    print("\n" + "=" * 60)
    print("网络连通性测试")
    print("=" * 60)
    
    test_network_connectivity()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成 - Agent注册成功")
    else:
        print("❌ 测试完成 - Agent注册失败")
    print("=" * 60)
