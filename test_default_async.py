#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试默认异步功能
验证 generate_auto_video_mcp 默认使用异步任务
"""

import asyncio
import json
import time
from auto_video_modules.mcp_tools import get_mcp_instance

async def test_default_async():
    """测试默认异步功能"""
    
    print("🚀 测试默认异步功能...")
    print("验证 generate_auto_video_mcp 默认使用异步任务处理")
    
    # 获取MCP实例
    mcp = get_mcp_instance()
    
    # 1. 测试默认异步任务
    print("\n📝 步骤1: 调用 generate_auto_video_mcp（默认异步）...")
    
    result = await mcp.call_tool("generate_auto_video_mcp", {
        "video_path": "test_video.mp4",
        "text": "这是一个测试默认异步功能的视频。我们将验证默认使用异步任务处理，避免长时间等待导致的连接超时问题。",
        "voice_index": 0,
        "output_path": "default_async_test.mp4",
        "quality_preset": "480p"  # 使用较低画质加快测试
    })
    
    print(f"返回结果: {result}")
    
    # 检查是否返回任务ID（异步任务特征）
    try:
        task_info = json.loads(result)
        if "task_id" in task_info:
            print("✅ 确认：generate_auto_video_mcp 默认使用异步任务")
            task_id = task_info["task_id"]
            print(f"任务ID: {task_id}")
        else:
            print("❌ 错误：未返回任务ID，可能不是异步任务")
            return
    except json.JSONDecodeError:
        print("❌ 错误：返回结果不是有效的JSON格式")
        return
    
    # 2. 查询任务状态
    print("\n📊 步骤2: 查询任务状态...")
    
    status_result = await mcp.call_tool("get_task_status", {
        "task_id": task_id
    })
    
    status_info = json.loads(status_result)
    print(f"任务状态: {status_info['status']}")
    print(f"进度: {status_info['progress']}%")
    print(f"创建时间: {status_info['created_at']}")
    
    # 3. 等待任务完成
    print("\n⏳ 步骤3: 等待任务完成...")
    
    start_time = time.time()
    check_count = 0
    
    while True:
        check_count += 1
        status_result = await mcp.call_tool("get_task_status", {
            "task_id": task_id
        })
        
        status_info = json.loads(status_result)
        elapsed_time = time.time() - start_time
        
        print(f"第{check_count}次查询 - 耗时: {elapsed_time:.1f}秒")
        print(f"  状态: {status_info['status']}")
        print(f"  进度: {status_info['progress']}%")
        
        if status_info['status'] == 'completed':
            print("✅ 任务完成！")
            print(f"  总耗时: {elapsed_time:.1f}秒")
            print(f"  结果: {status_info['result']}")
            break
        elif status_info['status'] == 'failed':
            print(f"❌ 任务失败: {status_info['error']}")
            break
        elif status_info['status'] == 'cancelled':
            print("🚫 任务已取消")
            break
        else:
            print(f"  等待中... 5秒后再次查询")
            await asyncio.sleep(5)
    
    print("\n🎉 默认异步功能测试完成！")

async def test_sync_version():
    """测试同步版本功能"""
    
    print("\n🔄 测试同步版本功能...")
    print("验证 generate_auto_video_sync 使用同步处理")
    
    # 获取MCP实例
    mcp = get_mcp_instance()
    
    # 测试同步版本
    print("\n📝 调用 generate_auto_video_sync（同步版本）...")
    
    start_time = time.time()
    
    result = await mcp.call_tool("generate_auto_video_sync", {
        "video_path": "test_video.mp4",
        "text": "短文本测试。",
        "voice_index": 0,
        "output_path": "sync_test.mp4",
        "quality_preset": "240p"  # 使用最低画质加快测试
    })
    
    elapsed_time = time.time() - start_time
    
    print(f"同步处理耗时: {elapsed_time:.1f}秒")
    print(f"返回结果: {result}")
    
    # 检查是否直接返回结果（同步任务特征）
    try:
        result_info = json.loads(result)
        if "task_id" in result_info:
            print("❌ 错误：同步版本返回了任务ID，应该是直接结果")
        else:
            print("✅ 确认：generate_auto_video_sync 使用同步处理")
    except json.JSONDecodeError:
        print("✅ 确认：generate_auto_video_sync 使用同步处理（返回非JSON结果）")
    
    print("\n🎉 同步版本功能测试完成！")

async def main():
    """主测试函数"""
    
    print("=" * 60)
    print("默认异步功能测试")
    print("=" * 60)
    
    try:
        # 测试默认异步功能
        await test_default_async()
        
        # 测试同步版本
        await test_sync_version()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 