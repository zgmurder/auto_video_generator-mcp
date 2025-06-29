# SSE异步运行说明

## 概述

自动视频生成MCP服务器支持SSE（Server-Sent Events）方式运行，提供异步通信能力。

## 启动服务器

### 方式1：直接启动
```bash
python auto_generate_video_mcp_modular.py
```

### 方式2：后台运行
```bash
# Windows
start /B python auto_generate_video_mcp_modular.py

# Linux/Mac
nohup python auto_generate_video_mcp_modular.py &
```

## 服务器信息

- **地址**: http://localhost:8000/sse
- **协议**: SSE (Server-Sent Events)
- **支持**: 异步调用、并发处理

## 异步客户端示例

### Python异步客户端

```python
import asyncio
import aiohttp
import json

async def call_mcp_tool():
    async with aiohttp.ClientSession() as session:
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
            if response.status == 200:
                result = await response.json()
                print(f"结果: {result}")
            else:
                print(f"错误: {response.status}")

# 运行
asyncio.run(call_mcp_tool())
```

### JavaScript异步客户端

```javascript
async function callMCPTool() {
    const payload = {
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: {
            name: "get_system_status_mcp",
            arguments: {}
        }
    };
    
    try {
        const response = await fetch('http://localhost:8000/sse', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('结果:', result);
        } else {
            console.error('错误:', response.status);
        }
    } catch (error) {
        console.error('异常:', error);
    }
}

// 调用
callMCPTool();
```

## 并发调用示例

```python
import asyncio
import aiohttp

async def concurrent_calls():
    async with aiohttp.ClientSession() as session:
        # 创建多个并发任务
        tasks = []
        for i in range(5):
            payload = {
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": "tools/call",
                "params": {
                    "name": "get_system_status_mcp",
                    "arguments": {}
                }
            }
            
            task = session.post('http://localhost:8000/sse', json=payload)
            tasks.append(task)
        
        # 并发执行
        responses = await asyncio.gather(*tasks)
        
        # 处理结果
        for i, response in enumerate(responses):
            if response.status == 200:
                result = await response.json()
                print(f"调用 {i+1} 成功: {result}")
            else:
                print(f"调用 {i+1} 失败: {response.status}")

# 运行
asyncio.run(concurrent_calls())
```

## 可用工具

### 核心功能
- `generate_auto_video_mcp`: 智能剪辑视频并自动添加字幕、语音

### 配置获取工具
- `get_system_status_mcp`: 获取系统状态信息
- `get_available_voice_options_mcp`: 获取可用的语音选项
- `validate_input_parameters_mcp`: 验证输入参数
- `get_generation_estimate_mcp`: 获取生成时间估算
- `get_all_available_tools`: 获取所有可用的工具列表

## 测试脚本

### 基本功能测试
```bash
python test_async_client.py
```

### 词语边界分割测试
```bash
python test_word_boundary.py
```

### 完整视频生成测试
```bash
python test_subtitle_fix.py
```

## 性能特点

1. **异步处理**: 支持非阻塞的异步调用
2. **并发支持**: 可以同时处理多个请求
3. **实时响应**: 使用SSE协议提供实时通信
4. **资源优化**: 高效利用系统资源

## 注意事项

1. 确保服务器已启动并监听8000端口
2. 客户端需要支持异步HTTP请求
3. 长时间运行的任务会阻塞其他请求
4. 建议在生产环境中使用负载均衡

## 故障排除

### 连接失败
- 检查服务器是否启动
- 确认端口8000未被占用
- 检查防火墙设置

### 调用失败
- 验证JSON-RPC格式
- 检查工具名称是否正确
- 确认参数格式

### 性能问题
- 监控服务器资源使用
- 考虑使用连接池
- 优化并发数量 