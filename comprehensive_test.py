#!/usr/bin/env python3
"""
完整的A2A平台自动化测试脚本
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class A2ATestSuite:
    """A2A平台测试套件"""
    
    def __init__(self):
        self.a2a_base_url = "http://127.0.0.1:9000"
        self.agent_url = "http://127.0.0.1:8888"
        self.test_results = []
        self.registered_agent_id = None
    
    def log(self, message: str, level: str = "INFO"):
        """记录测试日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_result(self, test_name: str, success: bool, message: str = "", details: Any = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.log(f"{status} - {test_name}: {message}")
        
        return success
    
    def test_environment_verification(self) -> bool:
        """环境验证测试"""
        self.log("开始环境验证测试...")
        
        # 测试CodeGen Expert agent
        try:
            response = requests.get(f"{self.agent_url}/.well-known/agent.json", timeout=10)
            if response.status_code == 200:
                agent_data = response.json()
                self.test_result(
                    "CodeGen Expert Agent可用性",
                    True,
                    f"Agent '{agent_data.get('name')}' 正常运行",
                    {"version": agent_data.get("version"), "capabilities": len(agent_data.get("capabilities", []))}
                )
            else:
                return self.test_result("CodeGen Expert Agent可用性", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.test_result("CodeGen Expert Agent可用性", False, f"连接失败: {e}")
        
        # 测试A2A中台
        try:
            response = requests.get(f"{self.a2a_base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.test_result(
                    "A2A中台可用性",
                    True,
                    f"平台状态: {health_data.get('status')}",
                    health_data
                )
            else:
                return self.test_result("A2A中台可用性", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.test_result("A2A中台可用性", False, f"连接失败: {e}")
        
        return True
    
    def test_agent_registration(self) -> bool:
        """Agent注册功能测试"""
        self.log("开始Agent注册功能测试...")
        
        try:
            # 准备注册请求
            register_payload = {
                "url": self.agent_url,
                "force_refresh": False
            }
            
            self.log(f"发送注册请求: {json.dumps(register_payload)}")
            
            # 发送注册请求
            response = requests.post(
                f"{self.a2a_base_url}/api/agents/register",
                json=register_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            self.log(f"注册API响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    self.registered_agent_id = result.get("agent_id")
                    return self.test_result(
                        "Agent注册功能",
                        True,
                        f"Agent '{result.get('agent_card', {}).get('name')}' 注册成功",
                        {"agent_id": self.registered_agent_id, "response": result}
                    )
                else:
                    return self.test_result("Agent注册功能", False, result.get("message", "注册失败"))
            else:
                return self.test_result("Agent注册功能", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            return self.test_result("Agent注册功能", False, f"请求异常: {e}")
    
    def test_agent_list(self) -> bool:
        """Agent列表查询测试"""
        self.log("开始Agent列表查询测试...")
        
        try:
            response = requests.get(f"{self.a2a_base_url}/api/agents", timeout=10)
            
            if response.status_code == 200:
                agents = response.json()
                
                if len(agents) > 0:
                    # 查找我们注册的agent
                    found_agent = None
                    for agent in agents:
                        if agent.get("url") == self.agent_url:
                            found_agent = agent
                            break
                    
                    if found_agent:
                        return self.test_result(
                            "Agent列表查询",
                            True,
                            f"找到注册的Agent: {found_agent.get('name')}",
                            {"total_agents": len(agents), "found_agent": found_agent}
                        )
                    else:
                        return self.test_result("Agent列表查询", False, "未找到注册的Agent")
                else:
                    return self.test_result("Agent列表查询", False, "Agent列表为空")
            else:
                return self.test_result("Agent列表查询", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.test_result("Agent列表查询", False, f"请求异常: {e}")
    
    def test_agent_unregistration(self) -> bool:
        """Agent注销功能测试"""
        self.log("开始Agent注销功能测试...")
        
        if not self.registered_agent_id:
            return self.test_result("Agent注销功能", False, "没有可注销的Agent ID")
        
        try:
            response = requests.delete(
                f"{self.a2a_base_url}/api/agents/unregister/{self.registered_agent_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return self.test_result(
                        "Agent注销功能",
                        True,
                        f"Agent {self.registered_agent_id} 注销成功",
                        result
                    )
                else:
                    return self.test_result("Agent注销功能", False, result.get("message", "注销失败"))
            else:
                return self.test_result("Agent注销功能", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            return self.test_result("Agent注销功能", False, f"请求异常: {e}")
    
    def test_error_handling(self) -> bool:
        """错误处理测试"""
        self.log("开始错误处理测试...")
        
        # 测试无效URL注册
        try:
            invalid_payload = {"url": "http://invalid-url:9999", "force_refresh": False}
            response = requests.post(
                f"{self.a2a_base_url}/api/agents/register",
                json=invalid_payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if not result.get("success"):
                    self.test_result(
                        "无效URL错误处理",
                        True,
                        f"正确处理无效URL: {result.get('message')}",
                        result
                    )
                else:
                    self.test_result("无效URL错误处理", False, "应该拒绝无效URL但却成功了")
            else:
                self.test_result("无效URL错误处理", True, f"正确返回错误状态: {response.status_code}")
                
        except Exception as e:
            self.test_result("无效URL错误处理", True, f"正确抛出异常: {e}")
        
        return True
    
    def test_stability(self) -> bool:
        """稳定性测试"""
        self.log("开始稳定性测试...")
        
        # 多次注册/注销测试
        success_count = 0
        total_tests = 3
        
        for i in range(total_tests):
            self.log(f"稳定性测试轮次 {i+1}/{total_tests}")
            
            # 注册
            try:
                register_response = requests.post(
                    f"{self.a2a_base_url}/api/agents/register",
                    json={"url": self.agent_url, "force_refresh": True},
                    timeout=20
                )
                
                if register_response.status_code == 200:
                    result = register_response.json()
                    if result.get("success"):
                        agent_id = result.get("agent_id")
                        
                        # 注销
                        unregister_response = requests.delete(
                            f"{self.a2a_base_url}/api/agents/unregister/{agent_id}",
                            timeout=10
                        )
                        
                        if unregister_response.status_code == 200:
                            success_count += 1
                            self.log(f"稳定性测试轮次 {i+1} 成功")
                        else:
                            self.log(f"稳定性测试轮次 {i+1} 注销失败")
                    else:
                        self.log(f"稳定性测试轮次 {i+1} 注册失败")
                else:
                    self.log(f"稳定性测试轮次 {i+1} 请求失败")
                    
            except Exception as e:
                self.log(f"稳定性测试轮次 {i+1} 异常: {e}")
            
            time.sleep(1)  # 短暂等待
        
        success_rate = success_count / total_tests
        return self.test_result(
            "稳定性测试",
            success_rate >= 0.8,  # 80%成功率
            f"成功率: {success_rate:.1%} ({success_count}/{total_tests})",
            {"success_count": success_count, "total_tests": total_tests}
        )
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        self.log("=" * 60)
        self.log("开始A2A平台完整自动化测试")
        self.log("=" * 60)
        
        # 执行所有测试
        tests = [
            self.test_environment_verification,
            self.test_agent_registration,
            self.test_agent_list,
            self.test_agent_unregistration,
            self.test_error_handling,
            self.test_stability
        ]
        
        all_passed = True
        for test in tests:
            try:
                if not test():
                    all_passed = False
            except Exception as e:
                self.log(f"测试执行异常: {e}", "ERROR")
                all_passed = False
            
            time.sleep(0.5)  # 测试间隔
        
        # 输出测试总结
        self.log("=" * 60)
        self.log("测试总结")
        self.log("=" * 60)
        
        passed_count = sum(1 for r in self.test_results if r["success"])
        total_count = len(self.test_results)
        
        self.log(f"总测试数: {total_count}")
        self.log(f"通过数: {passed_count}")
        self.log(f"失败数: {total_count - passed_count}")
        self.log(f"成功率: {passed_count/total_count:.1%}")
        
        # 详细结果
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            self.log(f"{status} {result['test_name']}: {result['message']}")
        
        self.log("=" * 60)
        if all_passed:
            self.log("🎉 所有测试通过！A2A平台功能正常！")
        else:
            self.log("❌ 部分测试失败，需要进一步检查")
        self.log("=" * 60)
        
        return all_passed

if __name__ == "__main__":
    test_suite = A2ATestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🚀 测试完成 - 所有功能正常工作！")
    else:
        print("\n⚠️ 测试完成 - 发现问题需要修复")
    
    exit(0 if success else 1)
