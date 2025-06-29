#!/usr/bin/env python3
"""
测试异步SSE运行
"""

import asyncio
import aiohttp
import json
import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_sse_connection():
    """测试SSE连接"""
    print("测试SSE连接...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试SSE端点
            async with session.get('http://localhost:8000/sse') as response:
                print(f"SSE连接状态: {response.status}")
                if response.status == 200:
                    print("✅ SSE连接成功")
                    return True
                else:
                    print(f"❌ SSE连接失败: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ SSE连接异常: {e}")
        return False

async def test_mcp_tools():
    """测试MCP工具调用"""
    print("\n测试MCP工具调用...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试获取系统状态
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_system_status_mcp",
                    "arguments": {}
                }
            }
            
            async with session.post('http://localhost:8000/sse', json=payload) as response:
                print(f"工具调用状态: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print("✅ MCP工具调用成功")
                    print(f"结果: {result}")
                    return True
                else:
                    print(f"❌ MCP工具调用失败: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ MCP工具调用异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("异步SSE运行测试")
    print("=" * 60)
    
    # 等待服务器启动
    print("等待服务器启动...")
    await asyncio.sleep(2)
    
    # 测试SSE连接
    sse_ok = await test_sse_connection()
    
    # 测试MCP工具
    if sse_ok:
        tools_ok = await test_mcp_tools()
    else:
        tools_ok = False
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"SSE连接: {'✅ 成功' if sse_ok else '❌ 失败'}")
    print(f"MCP工具: {'✅ 成功' if tools_ok else '❌ 失败'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 