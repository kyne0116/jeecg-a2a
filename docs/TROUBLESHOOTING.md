# JEECG A2A Platform 故障排除指南

## 🔧 常见问题及解决方案

### 1. 重复按钮/消息问题

**症状：** 聊天界面中出现重复的"介绍一下你能干什么"按钮或消息

**原因：** 
- 前端消息重复渲染
- 后端重复发送相同消息

**解决方案：** ✅ 已修复
- 添加了前端消息去重机制
- 改进了后端消息发送逻辑
- 实现了唯一消息ID跟踪

### 2. Agent响应状态异常

**症状：** 显示"Agent is typing..."但没有实际响应

**原因：**
- Typing indicator控制逻辑问题
- WebSocket消息处理异常

**解决方案：** ✅ 已修复
- 添加了30秒自动超时机制
- 改进了状态更新逻辑
- 增强了错误处理

### 3. JSON序列化错误

**症状：** 后台报错 "Object of type datetime is not JSON serializable"

**原因：** datetime对象无法直接JSON序列化

**解决方案：** ✅ 已修复
- 添加了`serialize_for_json`函数
- 自动转换datetime为ISO格式字符串
- 改进了WebSocket消息发送逻辑

### 4. 没有可用代理

**症状：** 后台警告 "No active agents available"

**原因：** 没有注册或启动代理服务

**解决方案：** ✅ 已修复
- 添加了自动代理注册机制
- 提供了清晰的错误提示
- 创建了代理状态检查功能

## 🚀 快速启动指南

### 方法1：使用启动脚本（推荐）

```bash
python3 scripts/start_with_agent.py
```

### 方法2：手动启动

1. **启动平台：**
   ```bash
   python3 main.py
   ```

2. **启动代理服务：**
   ```bash
   # 在另一个终端中启动代理
   python3 agent_server.py
   ```

3. **访问界面：**
   打开浏览器访问 `http://localhost:6000`

## 🔍 故障诊断步骤

### 1. 检查代理状态

在聊天界面中点击"检查代理状态"按钮，或发送消息查看系统响应。

### 2. 查看日志

```bash
tail -f logs/platform.log
```

### 3. 手动注册代理

访问 `/chat/agents` 页面手动注册代理服务。

### 4. 重启服务

如果问题持续，尝试重启平台和代理服务：

```bash
# 停止所有服务
pkill -f "python3.*main.py"
pkill -f "python3.*agent_server.py"

# 重新启动
python3 scripts/start_with_agent.py
```

## 📊 系统要求

- Python 3.8+
- 代理服务运行在 http://127.0.0.1:8888
- 网络连接正常

## 🆘 获取帮助

如果问题仍然存在：

1. 检查控制台错误信息
2. 查看平台日志文件
3. 确认代理服务状态
4. 尝试重启所有服务

## 📝 更新日志

### v1.0.1 (最新)
- ✅ 修复重复消息问题
- ✅ 修复JSON序列化错误
- ✅ 改进代理状态处理
- ✅ 增强用户体验
- ✅ 添加自动代理注册
- ✅ 改进错误提示
