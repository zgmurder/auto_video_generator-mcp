#!/usr/bin/env python3
"""
异步SSE服务器启动脚本
"""

import asyncio
import uvicorn
from auto_generate_video_mcp_modular import mcp

async def start_sse_server():
    """启动异步SSE服务器"""
    print("启动自动视频生成MCP服务器 v3.0 (异步SSE模式)...")
    print("服务器包含以下功能:")
    print("- 核心视频生成功能")
    print("- 配置获取工具")
    print("\n使用 get_all_available_tools 查看所有可用工具")
    print("服务器将以异步SSE方式运行")
    print("访问地址: http://localhost:8000/sse")
    
    # 配置uvicorn服务器
    config = uvicorn.Config(
        app=mcp.app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
    
    # 创建服务器实例
    server = uvicorn.Server(config)
    
    # 异步启动服务器
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(start_sse_server())
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"服务器启动失败: {e}") 