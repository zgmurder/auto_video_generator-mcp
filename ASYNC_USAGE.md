# 异步视频生成使用指南

## 问题背景

大模型在调用视频生成时，由于生成时间长（通常需要几分钟到几十分钟），会导致连接超时或中断。为了解决这个问题，我们提供了异步任务管理功能。

## 解决方案

### 1. 异步任务流程

```
创建任务 → 获得任务ID → 查询进度 → 获取结果
```

### 2. 使用步骤

#### 步骤1：创建异步任务

```python
# 调用异步视频生成
result = await mcp.call_tool("generate_auto_video_async", {
    "video_path": "input_video.mp4",
    "text": "这是一个测试视频，用于演示异步生成功能。",
    "voice_index": 0,
    "output_path": "async_output.mp4",
    "quality_preset": "720p"
})

# 解析返回结果
import json
task_info = json.loads(result)
task_id = task_info["task_id"]
print(f"任务已创建，ID: {task_id}")
```

#### 步骤2：查询任务状态

```python
# 查询任务状态
status_result = await mcp.call_tool("get_task_status", {
    "task_id": task_id
})

status_info = json.loads(status_result)
print(f"任务状态: {status_info['status']}")
print(f"进度: {status_info['progress']}%")

# 如果任务完成
if status_info['status'] == 'completed':
    print("任务完成！")
    print(f"结果: {status_info['result']}")
elif status_info['status'] == 'failed':
    print(f"任务失败: {status_info['error']}")
```

#### 步骤3：定期查询（可选）

```python
import asyncio
import time

async def wait_for_task_completion(task_id, check_interval=5):
    """等待任务完成"""
    while True:
        status_result = await mcp.call_tool("get_task_status", {
            "task_id": task_id
        })
        
        status_info = json.loads(status_result)
        
        if status_info['status'] in ['completed', 'failed', 'cancelled']:
            return status_info
        
        print(f"任务进行中... 进度: {status_info['progress']}%")
        await asyncio.sleep(check_interval)

# 使用示例
final_result = await wait_for_task_completion(task_id)
```

### 3. 任务管理功能

#### 列出所有任务

```python
# 查看所有任务
tasks_result = await mcp.call_tool("list_all_tasks", {})
tasks_info = json.loads(tasks_result)
print(f"总任务数: {tasks_info['total_tasks']}")

for task in tasks_info['tasks']:
    print(f"任务ID: {task['task_id']}")
    print(f"状态: {task['status']}")
    print(f"进度: {task['progress']}%")
    print(f"创建时间: {task['created_at']}")
    print("---")
```

#### 取消任务

```python
# 取消正在运行的任务
cancel_result = await mcp.call_tool("cancel_task", {
    "task_id": task_id
})

cancel_info = json.loads(cancel_result)
print(cancel_info['message'])
```

## 使用建议

### 1. 选择合适的工具

- **短时间任务**（< 2分钟）：使用 `generate_auto_video_mcp`（同步版本）
- **长时间任务**（> 2分钟）：使用 `generate_auto_video_async`（异步版本）

### 2. 进度查询频率

- 建议每5-10秒查询一次进度
- 避免过于频繁的查询，以免影响服务器性能

### 3. 错误处理

```python
try:
    # 创建任务
    result = await mcp.call_tool("generate_auto_video_async", params)
    task_info = json.loads(result)
    
    if "error" in task_info:
        print(f"创建任务失败: {task_info['error']}")
        return
    
    # 等待完成
    final_result = await wait_for_task_completion(task_info['task_id'])
    
    if final_result['status'] == 'completed':
        print("任务成功完成！")
    else:
        print(f"任务失败: {final_result.get('error', '未知错误')}")
        
except Exception as e:
    print(f"发生异常: {e}")
```

### 4. 资源清理

任务完成后，建议清理不需要的任务记录：

```python
# 注意：当前版本任务记录会一直保存在内存中
# 如需清理，可以重启服务器
```

## 完整示例

```python
import asyncio
import json
from auto_video_modules.mcp_tools import get_mcp_instance

async def generate_video_async_example():
    """异步视频生成完整示例"""
    
    mcp = get_mcp_instance()
    
    # 1. 创建异步任务
    print("创建视频生成任务...")
    result = await mcp.call_tool("generate_auto_video_async", {
        "video_path": "test_video.mp4",
        "text": "这是一个异步视频生成测试。我们将演示如何使用异步任务来避免长时间等待导致的连接超时问题。",
        "voice_index": 0,
        "output_path": "async_test_output.mp4",
        "quality_preset": "480p"
    })
    
    task_info = json.loads(result)
    task_id = task_info["task_id"]
    print(f"任务已创建，ID: {task_id}")
    
    # 2. 等待任务完成
    print("等待任务完成...")
    while True:
        status_result = await mcp.call_tool("get_task_status", {
            "task_id": task_id
        })
        
        status_info = json.loads(status_result)
        
        if status_info['status'] == 'completed':
            print("✅ 任务完成！")
            print(f"结果: {status_info['result']}")
            break
        elif status_info['status'] == 'failed':
            print(f"❌ 任务失败: {status_info['error']}")
            break
        else:
            print(f"⏳ 任务进行中... 进度: {status_info['progress']}%")
            await asyncio.sleep(5)  # 等待5秒后再次查询

if __name__ == "__main__":
    asyncio.run(generate_video_async_example())
```

## 注意事项

1. **任务持久化**：当前版本任务状态保存在内存中，服务器重启后任务会丢失
2. **并发限制**：建议同时运行的任务数量不超过5个，避免资源竞争
3. **超时设置**：大模型调用时建议设置较长的超时时间（如5-10分钟）
4. **错误重试**：如果任务失败，可以重新创建任务

通过使用异步任务管理，您可以避免长时间等待导致的连接超时问题，同时获得更好的用户体验。 