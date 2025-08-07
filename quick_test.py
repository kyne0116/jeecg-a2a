#!/usr/bin/env python3
"""
Quick test for agent registration.
"""

import requests
import json

def test_registration():
    """Test agent registration directly."""
    try:
        print("🔍 Testing agent registration...")
        
        # Test health first
        print("1. Testing health...")
        health_response = requests.get("http://127.0.0.1:9000/health", timeout=5)
        print(f"   Health status: {health_response.status_code}")
        
        if health_response.status_code != 200:
            print("❌ Health check failed")
            return False
        
        # Test registration
        print("2. Testing registration...")
        register_data = {
            "url": "http://127.0.0.1:8888",
            "force_refresh": False
        }
        
        register_response = requests.post(
            "http://127.0.0.1:9000/api/agents/register",
            json=register_data,
            timeout=30
        )
        
        print(f"   Registration status: {register_response.status_code}")
        
        if register_response.status_code == 200:
            result = register_response.json()
            print(f"   Registration result: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("success"):
                print("✅ Agent registration successful!")
                
                # Test agent list
                print("3. Testing agent list...")
                agents_response = requests.get("http://127.0.0.1:9000/api/agents", timeout=5)
                if agents_response.status_code == 200:
                    agents = agents_response.json()
                    print(f"   Registered agents: {len(agents)}")
                    for agent in agents:
                        print(f"   - {agent.get('name')} ({agent.get('url')})")
                
                return True
            else:
                print(f"❌ Registration failed: {result.get('message')}")
                return False
        else:
            print(f"❌ Registration API failed: {register_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Quick Agent Registration Test")
    print("=" * 50)
    
    success = test_registration()
    
    print("=" * 50)
    if success:
        print("✅ Test PASSED - Agent registration working!")
    else:
        print("❌ Test FAILED")
    print("=" * 50)
