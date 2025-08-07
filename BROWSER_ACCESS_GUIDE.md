# 浏览器访问指南 - 解决"此网址已被限制"问题

## 🚨 问题描述

当访问 `http://localhost:8000/` 时显示"此网址已被限制"错误。

## 🔍 根本原因

经过诊断发现，主要原因是：

1. **服务器启动问题**: FastAPI 服务器实际未成功启动监听端口
2. **中文安全软件拦截**: 360、腾讯管家等安全软件可能拦截 localhost 访问
3. **浏览器安全策略**: 某些浏览器对 localhost 有安全限制

## ✅ 解决方案

### 方案 1: 使用修复后的启动脚本（推荐）

```bash
# 使用新的启动脚本
python run_platform.py
```

这个脚本会：

- ✅ 自动检查依赖
- ✅ 创建正确的配置文件
- ✅ 测试端口可用性
- ✅ 使用 127.0.0.1 而不是 0.0.0.0
- ✅ 提供详细的启动日志

### 方案 2: 手动启动 FastAPI

```bash
# 直接启动uvicorn
uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

### 方案 3: 使用不同端口

```bash
# 使用8000端口
uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

## 🌐 访问地址测试

按优先级尝试以下地址：

1. **http://127.0.0.1:8000/** （推荐）
2. **http://localhost:8000/**
3. **http://127.0.0.1:8000/health** （健康检查）
4. **http://127.0.0.1:8000/.well-known/agent.json** （Agent 卡片）

## 🛡️ 安全软件设置

### 360 安全卫士

1. 打开 360 安全卫士
2. 进入"防护中心" → "网页防护"
3. 添加 `localhost` 和 `127.0.0.1` 到白名单
4. 或临时关闭网页防护测试

### 腾讯电脑管家

1. 打开腾讯电脑管家
2. 进入"实时防护" → "网页防护"
3. 添加例外网站: `localhost:8000`
4. 或临时关闭网页防护

### Windows Defender

1. 打开 Windows 安全中心
2. 进入"病毒和威胁防护"
3. 添加排除项: 项目文件夹路径

## 🔥 防火墙设置

### Windows 防火墙

```cmd
# 添加端口例外（以管理员身份运行）
netsh advfirewall firewall add rule name="JEECG A2A Platform" dir=in action=allow protocol=TCP localport=8000

# 或临时关闭防火墙测试
netsh advfirewall set allprofiles state off
```

### 检查防火墙状态

```cmd
netsh advfirewall show allprofiles state
```

## 🌏 浏览器设置

### Chrome 浏览器

1. 地址栏输入: `chrome://settings/content/insecureContent`
2. 添加 `http://localhost:8000` 到允许列表
3. 或使用无痕模式测试

### Firefox 浏览器

1. 地址栏输入: `about:config`
2. 搜索: `network.dns.disableIPv6`
3. 设置为 `true`

### Edge 浏览器

1. 设置 → 隐私、搜索和服务
2. 安全性 → 关闭"阻止潜在不需要的应用"
3. 或使用 InPrivate 模式

## 🔧 命令行测试

### 测试连接

```bash
# 测试端口连通性
telnet localhost 6000

# 使用curl测试
curl http://localhost:8000/
curl http://127.0.0.1:8000/health

# 检查端口监听
netstat -an | findstr :8000
```

### PowerShell 测试

```powershell
# 测试TCP连接
Test-NetConnection -ComputerName localhost -Port 6000

# 检查进程
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

## 📱 移动设备访问

如果需要从手机等设备访问：

1. 查看本机 IP 地址:

```cmd
ipconfig | findstr IPv4
```

2. 修改启动参数:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

3. 手机浏览器访问: `http://[你的IP]:8000`

## 🚀 快速验证脚本

创建测试脚本验证服务状态：

```python
import requests
import socket

def test_connection():
    # 测试端口
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 6000))
    if result == 0:
        print("✅ 端口8000正在监听")
    else:
        print("❌ 端口8000未监听")
    sock.close()

    # 测试HTTP
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        print(f"✅ HTTP响应: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTP错误: {e}")

test_connection()
```

## 📞 技术支持

如果以上方案都无法解决问题：

1. **收集信息**:

   - 操作系统版本
   - 浏览器类型和版本
   - 安装的安全软件
   - 完整的错误截图

2. **联系支持**:
   - 提供 `python diagnose_server.py` 的完整输出
   - 提供服务器启动的完整日志
   - 说明已尝试的解决方案

## 🎯 成功标志

当看到以下信息时，表示问题已解决：

```
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

浏览器能够正常显示 JEECG A2A Platform 的聊天界面。
