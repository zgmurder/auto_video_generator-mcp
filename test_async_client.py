#!/usr/bin/env python3
"""
异步客户端测试脚本
测试与SSE服务器的异步通信
"""

import asyncio
import aiohttp
import json
import time

async def test_async_mcp_call():
    """测试异步MCP调用"""
    print("=" * 60)
    print("异步MCP客户端测试")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        {
            "name": "获取系统状态",
            "method": "tools/call",
            "params": {
                "name": "get_system_status_mcp",
                "arguments": {}
            }
        },
        {
            "name": "获取语音选项",
            "method": "tools/call",
            "params": {
                "name": "get_available_voice_options_mcp",
                "arguments": {}
            }
        },
        {
            "name": "获取工具列表",
            "method": "tools/call",
            "params": {
                "name": "get_all_available_tools",
                "arguments": {}
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_cases):
            print(f"\n测试 {i+1}: {test_case['name']}")
            print("-" * 40)
            
            payload = {
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": test_case["method"],
                "params": test_case["params"]
            }
            
            try:
                start_time = time.time()
                async with session.post('http://localhost:8000/sse', json=payload) as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    print(f"响应时间: {response_time:.2f}ms")
                    print(f"状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ 调用成功")
                        if "result" in result:
                            print(f"结果: {result['result'][:100]}...")
                        else:
                            print(f"结果: {result}")
                    else:
                        print(f"❌ 调用失败: {response.status}")
                        error_text = await response.text()
                        print(f"错误信息: {error_text}")
                        
            except Exception as e:
                print(f"❌ 异常: {e}")

async def test_concurrent_calls():
    """测试并发调用"""
    print("\n" + "=" * 60)
    print("并发调用测试")
    print("=" * 60)
    
    async def single_call(session, call_id):
        """单个调用"""
        payload = {
            "jsonrpc": "2.0",
            "id": call_id,
            "method": "tools/call",
            "params": {
                "name": "get_system_status_mcp",
                "arguments": {}
            }
        }
        
        try:
            start_time = time.time()
            async with session.post('http://localhost:8000/sse', json=payload) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if response.status == 200:
                    result = await response.json()
                    print(f"调用 {call_id}: ✅ 成功 ({response_time:.2f}ms)")
                    return True
                else:
                    print(f"调用 {call_id}: ❌ 失败 ({response.status})")
                    return False
        except Exception as e:
            print(f"调用 {call_id}: ❌ 异常 ({e})")
            return False
    
    # 并发执行5个调用
    async with aiohttp.ClientSession() as session:
        tasks = [single_call(session, i) for i in range(1, 6)]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(results)
        print(f"\n并发测试结果: {success_count}/5 成功")

async def main():
    """主函数"""
    print("等待服务器启动...")
    await asyncio.sleep(2)
    
    # 测试基本功能
    await test_async_mcp_call()
    
    # 测试并发功能
    await test_concurrent_calls()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 