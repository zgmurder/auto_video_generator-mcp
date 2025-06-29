#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步视频生成测试脚本
用于测试长时间任务处理功能
"""

import asyncio
import json
import time
from auto_video_modules.mcp_tools import get_mcp_instance

async def test_async_video_generation():
    """测试异步视频生成功能"""
    
    print("🚀 开始测试异步视频生成功能...")
    
    # 获取MCP实例
    mcp = get_mcp_instance()
    
    # 1. 测试创建异步任务
    print("\n📝 步骤1: 创建异步视频生成任务...")
    
    result = await mcp.call_tool("generate_auto_video_async", {
        "video_path": "test_video.mp4",
        "text": "这是一个异步视频生成测试。我们将演示如何使用异步任务来避免长时间等待导致的连接超时问题。通过这种方式，大模型可以在后台处理视频生成，而不会因为超时而中断连接。",
        "voice_index": 0,
        "output_path": "async_test_output.mp4",
        "quality_preset": "480p"  # 使用较低画质加快测试
    })
    
    print(f"创建任务返回结果: {result}")
    
    task_info = json.loads(result)
    task_id = task_info["task_id"]
    print(f"✅ 任务已创建，ID: {task_id}")
    
    # 2. 测试查询任务状态
    print("\n📊 步骤2: 查询任务状态...")
    
    status_result = await mcp.call_tool("get_task_status", {
        "task_id": task_id
    })
    
    status_info = json.loads(status_result)
    print(f"任务状态: {status_info['status']}")
    print(f"进度: {status_info['progress']}%")
    print(f"创建时间: {status_info['created_at']}")
    
    # 3. 测试列出所有任务
    print("\n📋 步骤3: 列出所有任务...")
    
    tasks_result = await mcp.call_tool("list_all_tasks", {})
    tasks_info = json.loads(tasks_result)
    
    print(f"总任务数: {tasks_info['total_tasks']}")
    for task in tasks_info['tasks']:
        print(f"  - 任务ID: {task['task_id']}")
        print(f"    状态: {task['status']}")
        print(f"    进度: {task['progress']}%")
        print(f"    视频路径: {task['video_path']}")
        print(f"    文本长度: {task['text_length']} 字符")
    
    # 4. 等待任务完成（模拟长时间处理）
    print("\n⏳ 步骤4: 等待任务完成...")
    
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
    
    # 5. 测试任务管理功能
    print("\n🔧 步骤5: 测试任务管理功能...")
    
    # 再次列出所有任务
    tasks_result = await mcp.call_tool("list_all_tasks", {})
    tasks_info = json.loads(tasks_result)
    
    print(f"任务完成后的总任务数: {tasks_info['total_tasks']}")
    
    # 测试取消已完成的任务（应该失败）
    if task_id in [t['task_id'] for t in tasks_info['tasks']]:
        cancel_result = await mcp.call_tool("cancel_task", {
            "task_id": task_id
        })
        
        cancel_info = json.loads(cancel_result)
        print(f"尝试取消已完成任务的结果: {cancel_info}")
    
    print("\n🎉 异步视频生成测试完成！")

async def test_multiple_tasks():
    """测试多个并发任务"""
    
    print("\n🔄 开始测试多个并发任务...")
    
    mcp = get_mcp_instance()
    
    # 创建多个任务
    task_ids = []
    for i in range(3):
        print(f"\n创建第{i+1}个任务...")
        
        result = await mcp.call_tool("generate_auto_video_async", {
            "video_path": "test_video.mp4",
            "text": f"这是第{i+1}个并发测试任务。",
            "voice_index": i % 3,
            "output_path": f"concurrent_test_{i+1}.mp4",
            "quality_preset": "240p"  # 使用最低画质加快测试
        })
        
        task_info = json.loads(result)
        task_ids.append(task_info["task_id"])
        print(f"任务{i+1} ID: {task_info['task_id']}")
    
    # 监控所有任务
    print("\n监控所有任务状态...")
    
    completed_tasks = 0
    start_time = time.time()
    
    while completed_tasks < len(task_ids):
        print(f"\n--- 第{int(time.time() - start_time)}秒状态检查 ---")
        
        for i, task_id in enumerate(task_ids):
            status_result = await mcp.call_tool("get_task_status", {
                "task_id": task_id
            })
            
            status_info = json.loads(status_result)
            print(f"任务{i+1}: {status_info['status']} ({status_info['progress']}%)")
            
            if status_info['status'] in ['completed', 'failed', 'cancelled']:
                completed_tasks += 1
        
        if completed_tasks < len(task_ids):
            await asyncio.sleep(3)
    
    print(f"\n✅ 所有{len(task_ids)}个任务已完成！")

async def main():
    """主测试函数"""
    
    print("=" * 60)
    print("异步视频生成MCP服务器测试")
    print("=" * 60)
    
    try:
        # 测试单个异步任务
        await test_async_video_generation()
        
        # 测试多个并发任务
        await test_multiple_tasks()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 