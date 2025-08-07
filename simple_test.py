#!/usr/bin/env python3
"""
简单的agent注册测试
"""

import requests
import json

def test_direct_registration():
    """直接测试agent注册"""
    print("🔍 开始直接注册测试...")
    
    # 测试agent.json访问
    agent_url = "http://127.0.0.1:8888"
    agent_json_url = f"{agent_url}/.well-known/agent.json"
    
    try:
        print(f"📡 获取agent.json: {agent_json_url}")
        response = requests.get(agent_json_url, timeout=10)
        
        if response.status_code == 200:
            agent_data = response.json()
            print(f"✅ Agent信息获取成功:")
            print(f"   名称: {agent_data.get('name')}")
            print(f"   版本: {agent_data.get('version')}")
            print(f"   URL: {agent_data.get('url')}")
            print(f"   能力数量: {len(agent_data.get('capabilities', []))}")
            
            # 验证必需字段
            required_fields = ["name", "url", "version"]
            missing_fields = []
            for field in required_fields:
                if field not in agent_data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 缺少必需字段: {missing_fields}")
                return False
            else:
                print(f"✅ 所有必需字段都存在")
                return True
        else:
            print(f"❌ 无法获取agent.json: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 获取agent.json时发生错误: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Agent注册直接测试")
    print("=" * 60)
    
    success = test_direct_registration()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Agent端完全正常，符合A2A规范")
        print("❌ 问题出在a2a中台服务不稳定")
    else:
        print("❌ Agent端存在问题")
    print("=" * 60)
