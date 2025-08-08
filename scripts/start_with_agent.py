#!/usr/bin/env python3
"""
启动JEECG A2A Platform并自动注册默认代理的脚本
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.platform import platform
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_platform_with_agent():
    """启动平台并注册默认代理"""
    try:
        logger.info("🚀 启动JEECG A2A Platform...")
        
        # 启动平台
        await platform.start()
        logger.info("✅ 平台启动成功")
        
        # 等待一下让平台完全启动
        await asyncio.sleep(2)
        
        # 尝试注册默认代理
        default_agents = [
            "http://127.0.0.1:8888",
            "http://localhost:8888"
        ]
        
        registered_count = 0
        for agent_url in default_agents:
            try:
                logger.info(f"🔗 尝试注册代理: {agent_url}")
                result = await platform.register_agent(agent_url)
                
                if result.success:
                    logger.info(f"✅ 代理注册成功: {result.agent_card.name}")
                    registered_count += 1
                else:
                    logger.warning(f"⚠️ 代理注册失败: {result.message}")
                    
            except Exception as e:
                logger.warning(f"⚠️ 无法连接到代理 {agent_url}: {e}")
        
        if registered_count > 0:
            logger.info(f"🎉 成功注册 {registered_count} 个代理")
        else:
            logger.warning("⚠️ 没有代理注册成功，请手动启动代理服务")
            logger.info("💡 提示：请确保代理服务在 http://127.0.0.1:8888 运行")
        
        # 显示平台信息
        platform_info = platform.get_platform_info()
        logger.info("📊 平台状态:")
        logger.info(f"   - 代理数量: {platform_info.get('agents_count', 0)}")
        logger.info(f"   - 平台版本: {settings.PLATFORM_VERSION}")
        logger.info(f"   - 访问地址: http://{settings.HOST}:{settings.PORT}")
        
        logger.info("🌐 平台已启动，可以开始使用聊天界面")
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(60)
                # 定期检查平台状态
                agents = await platform.list_agents()
                active_count = len([a for a in agents if a.status == "active"])
                if active_count == 0:
                    logger.warning("⚠️ 当前没有活跃的代理，请检查代理服务状态")
                    
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信号，正在关闭平台...")
            await platform.stop()
            logger.info("✅ 平台已停止")
            
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    print("🚀 JEECG A2A Platform 启动器")
    print("=" * 50)
    print("此脚本将启动平台并尝试自动注册默认代理")
    print("请确保代理服务已在 http://127.0.0.1:8888 运行")
    print("=" * 50)
    
    try:
        asyncio.run(start_platform_with_agent())
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
