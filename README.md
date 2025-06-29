# 自动视频生成MCP服务器

这是一个基于FastMCP框架的自动视频生成服务器，支持文本转语音、视频剪辑、字幕生成和音视频合成。

## 🆕 新增功能：异步任务管理

为了解决大模型调用时因视频生成时间长而导致的连接超时问题，我们新增了异步任务管理功能，**现在默认使用异步任务处理**：

### 异步功能特性
- **长时间任务处理**：避免连接超时，支持后台处理
- **任务状态查询**：实时监控任务进度
- **并发任务支持**：支持多个任务同时运行
- **任务取消功能**：可取消正在运行的任务

### 默认使用异步任务
现在调用 `generate_auto_video_mcp` 会自动使用异步任务处理，避免连接超时：

```python
# 默认使用异步任务（推荐）
result = await mcp.call_tool("generate_auto_video_mcp", {
    "video_path": "input_video.mp4",
    "text": "视频内容",
    "voice_index": 0
})

# 返回任务ID，需要查询状态
task_info = json.loads(result)
task_id = task_info["task_id"]

# 查询任务状态
status_result = await mcp.call_tool("get_task_status", {
    "task_id": task_id
})
```

### 同步版本（适合短时间任务）
如果需要同步处理短时间任务，可以使用：

```python
# 同步版本（适合短时间任务）
result = await mcp.call_tool("generate_auto_video_sync", {
    "video_path": "input_video.mp4",
    "text": "短文本内容",
    "voice_index": 0
})

# 直接返回结果
print(result)
```

详细使用指南请参考 [ASYNC_USAGE.md](ASYNC_USAGE.md)

## 功能特性

### 核心功能
- **文本转语音**: 支持多种中文语音音色
- **智能字幕分割**: 支持多种分割策略
- **视频片段剪辑**: 支持保留或剪掉指定片段
- **字幕样式定制**: 支持字体、颜色、位置等自定义
- **音视频合成**: 自动合成带字幕的视频

### 配置参数

#### 1. segments_mode (视频片段模式)
- `"keep"`: 保留指定片段
- `"cut"`: 剪掉指定片段

#### 2. segments (视频片段配置)
JSON数组格式，指定视频片段的时间区间：
```json
[
  {"start": "00:00:05", "end": "00:00:15"},
  {"start": "00:00:25", "end": "00:00:35"}
]
```

#### 3. subtitle_style (字幕样式配置)
JSON对象格式，自定义字幕外观：
```json
{
  "fontSize": 40,
  "color": "white",
  "bgColor": [0, 0, 0, 128],
  "marginX": 100,
  "marginBottom": 50,
  "fontPath": "arial.ttf"
}
```

#### 4. auto_split_config (智能分割配置)
JSON对象格式，控制文本分割策略：
```json
{
  "enable": true,
  "strategy": "smart",
  "maxChars": 20,
  "targetDuration": 3.0
}
```

### quality_preset参数
- `"240p"`: 低画质预览 (426x240, 500k) - 适合快速预览
- `"360p"`: 标清画质 (640x360, 800k) - 适合移动设备
- `"480p"`: 标准画质 (854x480, 1.2M) - 适合一般用途
- `"720p"`: 高清画质 (1280x720, 2M) - 默认设置
- `"1080p"`: 全高清 (1920x1080, 4M) - 最高质量

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 启动MCP服务器

```bash
python auto_generate_video_mcp_modular.py
```

服务器将在端口8000上启动，支持SSE传输。

### 2. 基本使用

```python
from auto_video_modules.mcp_tools import get_mcp_instance

mcp = get_mcp_instance()

# 默认使用异步任务（推荐）
result = await mcp.call_tool("generate_auto_video_mcp", {
    "video_path": "input_video.mp4",
    "text": "要转换的文本",
    "voice_index": 0,
    "output_path": "output_video.mp4"
})

# 解析任务ID
import json
task_info = json.loads(result)
task_id = task_info["task_id"]

# 查询任务状态
while True:
    status_result = await mcp.call_tool("get_task_status", {
        "task_id": task_id
    })
    
    status_info = json.loads(status_result)
    if status_info['status'] == 'completed':
        print("任务完成！")
        print(f"结果: {status_info['result']}")
        break
    elif status_info['status'] == 'failed':
        print(f"任务失败: {status_info['error']}")
        break
    
    await asyncio.sleep(5)  # 等待5秒后再次查询

# 同步版本（适合短时间任务）
result = await mcp.call_tool("generate_auto_video_sync", {
    "video_path": "input_video.mp4",
    "text": "短文本内容",
    "output_path": "sync_output.mp4"
})

print(result)  # 直接返回结果
```

### 使用场景

#### 1. 完整视频生成（推荐，默认异步）
当需要为视频添加语音解说和字幕时使用：
```python
result = await mcp.call_tool("generate_auto_video_mcp", {
    "video_path": "input_video.mp4",
    "text": "详细的解说文本内容",
    "voice_index": 0,
    "quality_preset": "720p"
})

# 处理异步任务
task_info = json.loads(result)
task_id = task_info["task_id"]
# ... 查询任务状态
```

#### 2. 仅视频处理（默认异步）
当只需要对视频进行剪辑、画质调整等处理时使用：
```python
result = await mcp.call_tool("generate_auto_video_mcp", {
    "video_path": "input_video.mp4",
    "text": "",  # 空文本
    "segments_mode": "keep",
    "segments": json.dumps([{"start": "00:00:10", "end": "00:00:30"}]),
    "quality_preset": "480p"
})

# 处理异步任务
task_info = json.loads(result)
task_id = task_info["task_id"]
# ... 查询任务状态
```

#### 3. 快速预览（同步版本）
使用低画质快速生成预览版本：
```python
result = await mcp.call_tool("generate_auto_video_sync", {
    "video_path": "input_video.mp4",
    "text": "预览文本",
    "quality_preset": "240p"  # 低画质快速预览
})

print(result)  # 直接返回结果
```

### 3. 高级配置示例

#### 视频片段剪辑
```python
# 保留指定片段（默认异步）
result = await mcp.call_tool("generate_auto_video_mcp", {
    "video_path": "input.mp4",
    "text": "文本内容",
    "segments_mode": "keep",
    "segments": json.dumps([
        {"start": "00:00:05", "end": "00:00:15"},
        {"start": "00:00:25", "end": "00:00:35"}
    ])
})

# 处理异步任务
task_info = json.loads(result)
task_id = task_info["task_id"]
# ... 查询任务状态

# 剪掉指定片段（默认异步）
result = await mcp.call_tool("generate_auto_video_mcp", {
    "video_path": "input.mp4",
    "text": "文本内容",
    "segments_mode": "cut",
    "segments": json.dumps([
        {"start": "00:00:10", "end": "00:00:20"}
    ])
})

# 处理异步任务
task_info = json.loads(result)
task_id = task_info["task_id"]
# ... 查询任务状态
```

#### 自定义字幕样式
```python
result = await mcp.call_tool("generate_auto_video_mcp", {
    "video_path": "input.mp4",
    "text": "文本内容",
    "subtitle_style": json.dumps({
        "fontSize": 50,
        "color": "yellow",
        "bgColor": [0, 0, 0, 128],
        "marginX": 150,
        "marginBottom": 80
    })
})

# 处理异步任务
task_info = json.loads(result)
task_id = task_info["task_id"]
# ... 查询任务状态
```

#### 智能文本分割
```python
# 智能分割（默认异步）
result = await mcp.call_tool("generate_auto_video_mcp", {
    "video_path": "input.mp4",
    "text": "文本内容",
    "auto_split_config": json.dumps({
        "enable": True,
        "strategy": "smart",
        "maxChars": 15
    })
})

# 处理异步任务
task_info = json.loads(result)
task_id = task_info["task_id"]
# ... 查询任务状态

# 按时长分割（默认异步）
result = await mcp.call_tool("generate_auto_video_mcp", {
    "video_path": "input.mp4",
    "text": "文本内容",
    "auto_split_config": json.dumps({
        "enable": True,
        "strategy": "duration",
        "targetDuration": 2.0
    })
})

# 处理异步任务
task_info = json.loads(result)
task_id = task_info["task_id"]
# ... 查询任务状态
```

## 可用工具

### 主要工具
- `generate_auto_video`: 自动生成带字幕的视频
- `get_system_status`: 获取系统状态
- `get_available_voice_options`: 获取可用语音选项
- `validate_input_parameters`: 验证输入参数
- `get_generation_estimate`: 获取生成时间估算

### 模块化工具
- **FFmpeg工具**: 视频处理相关
- **语音工具**: 语音音色管理
- **音频工具**: 文本转语音
- **字幕工具**: 字幕生成和处理
- **视频工具**: 视频剪辑和合成

## 测试

运行测试脚本：

```bash
python test_auto_generate_video_modular.py
```

测试包括：
- 各模块功能测试
- 配置参数测试
- 完整视频生成测试
- 系统工具测试

## 配置参数详解

### segments_mode
- **keep**: 保留模式，只使用segments中指定的视频片段
- **cut**: 剪掉模式，使用segments之外的视频片段

### segments格式
```json
[
  {
    "start": "HH:MM:SS",  // 开始时间
    "end": "HH:MM:SS"     // 结束时间
  }
]
```

### subtitle_style参数
- `fontSize`: 字体大小 (默认: 40)
- `color`: 字体颜色 (默认: "white")
- `bgColor`: 背景颜色 [R,G,B,A] (默认: [0,0,0,0])
- `marginX`: 左右边距 (默认: 100)
- `marginBottom`: 底部边距 (默认: 50)
- `fontPath`: 字体文件路径 (默认: "arial.ttf")

### auto_split_config参数
- `enable`: 是否启用智能分割 (默认: true)
- `strategy`: 分割策略
  - `"smart"`: 智能分割 (按句子、逗号、字符数)
  - `"duration"`: 按时长分割
  - `"none"`: 不分割
- `maxChars`: 每行最大字符数 (默认: 20)
- `targetDuration`: 目标时长(秒) (默认: 3.0)

### quality_preset参数
- `"240p"`: 低画质预览 (426x240, 500k) - 适合快速预览
- `"360p"`: 标清画质 (640x360, 800k) - 适合移动设备
- `"480p"`: 标准画质 (854x480, 1.2M) - 适合一般用途
- `"720p"`: 高清画质 (1280x720, 2M) - 默认设置
- `"1080p"`: 全高清 (1920x1080, 4M) - 最高质量

## 注意事项

1. 确保系统已安装FFmpeg
2. 视频文件格式支持: MP4, AVI, MOV等
3. 音频文件格式支持: MP3, WAV等
4. 字幕支持中文和英文
5. 建议使用较短的文本片段以获得更好的效果

## 故障排除

### 常见问题
1. **FFmpeg未找到**: 请安装FFmpeg并确保在PATH中
2. **字体文件未找到**: 使用系统默认字体或指定正确的字体路径
3. **视频生成失败**: 检查输入视频文件格式和路径
4. **音频合成失败**: 检查网络连接和语音服务

### 调试模式
设置环境变量启用详细日志：
```bash
export PYTHONPATH=.
python auto_generate_video_mcp_modular.py
``` 