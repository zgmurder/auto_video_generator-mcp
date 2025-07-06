﻿# Auto Video Generator MCP

[English](README_EN.md) | [中文](README.md)

一个基于 MCP (Model Context Protocol) 的智能视频生成系统，支持自动添加字幕、语音合成和视频剪辑功能。

##  功能特性

### 核心功能
- **智能视频剪辑**: 支持视频片段保留/剪切模式
- **自动删除重复帧/静止片段**: 一键检测并剪掉无效画面，提升视频精华度（可选参数，默认关闭）
- **自动字幕生成**: 智能文本分割和字幕样式自定义
- **语音合成**: 集成 Azure 语音服务，支持多种音色
- **多画质输出**: 支持 240p 到 1080p 多种画质预设
- **GPU 加速编码**: 支持 AMD AMF、NVIDIA NVENC、Intel QSV 硬件编码加速
- **异步任务处理**: 支持长时间任务的异步处理
- **时间标记控制**: 支持在文本中使用时间标记控制静默时间

### 技术特性
- **模块化架构**: 清晰的模块分离，易于维护和扩展
- **MCP 协议**: 基于 FastMCP 的标准化接口
- **配置管理**: 灵活的配置系统，支持环境变量
- **任务管理**: 完整的任务状态跟踪和管理
- **临时文件清理**: 自动清理处理过程中的临时文件

##  系统要求

### 软件依赖
- Python 3.8+
- FFmpeg (需要预先安装并配置到系统 PATH)
- Windows 系统 (字体路径配置)

### Python 依赖
```
httpx>=0.24.0
fastmcp>=0.1.0
azure-cognitiveservices-speech>=1.31.0
pydub>=0.25.1
moviepy>=1.0.3
opencv-python>=4.8.0
Pillow>=10.0.0
jieba>=0.42.1
```

##  安装配置

### 1. 克隆项目
```bash
git clone https://github.com/zgmurder/auto_video_generator-mcp.git
cd auto-video-generator-mcp
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
# FFmpeg 路径配置 (可选)
export FFMPEG_PATH="path/to/ffmpeg"
export FFPROBE_PATH="path/to/ffprobe"

# 调试模式 (可选)
export DEBUG_MODE="true"
```

### 4. 启动服务器
```bash
python auto_generate_video_mcp_modular.py
```

服务器将在 `http://localhost:8000/sse` 启动。

##  使用指南

### 基本使用

#### 1. 简单视频生成
```python
# 生成带字幕和语音的视频
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="欢迎观看本视频，这是AI自动生成的解说。",
    voice_index=0,
    output_path="output.mp4"
)
```

#### 2. 自定义画质
```python
# 生成高清视频
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="高清视频内容",
    quality_preset="1080p"
)
```

#### 3. 视频片段处理
```python
# 保留指定片段 - 注意：segments必须是JSON字符串格式
segments = '[{"start": "00:00:05", "end": "00:00:15"}]'  # JSON字符串
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="片段解说",
    segments_mode="keep",
    segments=segments  # 传递JSON字符串，不是字典对象
)

# 剪切指定片段
segments = '[{"start": "00:00:10", "end": "00:00:20"}, {"start": "00:00:30", "end": "00:00:40"}]'
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="剪切片段解说",
    segments_mode="cut",
    segments=segments  # JSON字符串格式
)
```

### 高级功能

#### 1. 时间标记控制
```python
# 使用时间标记控制静默时间
text = "{5s}欢迎观看{5000ms}本视频由AI自动剪辑并添加智能字幕和语音解说。{2s}感谢您的观看！"
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text=text
)
```

#### 2. 自定义字幕样式
```python
# 自定义字幕样式 - 注意：subtitle_style必须是JSON字符串格式
subtitle_style = '{"fontSize": 60, "color": "yellow", "bgColor": [0, 0, 0, 128]}'  # JSON字符串
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="自定义字幕样式",
    subtitle_style=subtitle_style  # 传递JSON字符串，不是字典对象
)

# 更多字幕样式示例
subtitle_style = '{"fontSize": 50, "color": "white", "bgColor": [0, 0, 0, 30], "marginX": 100, "marginBottom": 50}'
```

#### 3. 异步任务处理
```python
# 创建异步任务
task_id = await generate_auto_video_async(
    video_path="input.mp4",
    text="长时间处理任务"
)

# 查询任务状态
status = await get_task_status(task_id)

# 取消任务
await cancel_task(task_id)
```

#### 4. 自动删除重复帧/静止片段
```python
# 自动检测并剪掉视频中的静止/无聊片段（如长时间无动作画面）
# 方法1：使用配置文件中的参数
import json
with open("best_motion_clip_params.json", "r", encoding="utf-8") as f:
    motion_params = json.load(f)
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    output_path="output_motion_clip.mp4",
    enable_motion_clip=True,  # 启用自动静止片段检测
    motion_clip_params=json.dumps(motion_params)  # 转换为JSON字符串
)

# 方法2：直接传入JSON字符串参数
motion_params = '{"motion_threshold": 0.1, "min_static_duration": 2.0, "sample_step": 1}'  # JSON字符串
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    output_path="output_motion_clip.mp4",
    enable_motion_clip=True,
    motion_clip_params=motion_params  # 直接传递JSON字符串
)
```

#### 5. 极致GPU加速编码
```python
# 使用极致GPU优化进行视频编码，将显卡性能发挥到最大
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="极致GPU加速视频处理",
    enable_gpu_acceleration=True,  # 启用极致GPU加速
    gpu_type="auto",  # 自动检测GPU类型，或指定"amd"/"nvidia"/"intel"
    quality_preset="1080p"
)

# 获取系统性能信息
performance_info = await get_system_performance_info_mcp()

# 优化视频处理参数
optimized_config = await optimize_video_processing_mcp("input.mp4", "1080p")

# GPU性能基准测试
benchmark_result = await benchmark_gpu_performance_mcp()
```

> **重要说明**：
> - **JSON参数格式**: 所有配置参数（`segments`, `subtitle_style`, `auto_split_config`, `motion_clip_params`）都必须使用JSON字符串格式传递，不能直接传递字典对象。
> - **时间格式**: 视频片段时间格式为 "HH:MM:SS"，例如 "00:00:05" 表示5秒。
> - **运动检测**: `enable_motion_clip=True` 时，系统会自动分析视频，检测并剪掉所有静止/重复帧片段。
> - **GPU优化**: `enable_gpu_acceleration=True` 时，系统会启用极致GPU优化，自动检测硬件配置并优化编码参数。
> - **极致GPU优化**: 包括多线程处理、内存优化、编码器调优、异步处理、缓存优化等。
> - **兼容性**: 不影响原有字幕、语音等功能，完全兼容。

##  JSON参数格式说明

### 重要提醒
所有配置参数都必须使用**JSON字符串格式**传递，不能直接传递字典对象。这是为了确保MCP协议的兼容性和数据传递的准确性。

### 参数格式示例

#### 1. 视频片段配置 (`segments`)
```json
[
  {"start": "00:00:05", "end": "00:00:15"},
  {"start": "00:00:30", "end": "00:00:45"}
]
```
**传递方式**: `segments='[{"start": "00:00:05", "end": "00:00:15"}]'`

#### 2. 字幕样式配置 (`subtitle_style`)
```json
{
  "fontSize": 50,
  "color": "white",
  "bgColor": [0, 0, 0, 30],
  "fontPath": "C:\\Windows\\Fonts\\msyh.ttc",
  "marginX": 100,
  "marginBottom": 50
}
```
**传递方式**: `subtitle_style='{"fontSize": 50, "color": "white"}'`

**支持的字段名格式**:
- 字体大小: `fontSize`, `font_size`, `size`
- 字体颜色: `color`, `font_color`, `fontColor`, `text_color`, `textColor`
- 背景颜色: `bgColor`, `bg_color`, `background_color`, `backgroundColor`
- 字体路径: `fontPath`, `font_path`, `font`
- 左右边距: `marginX`, `margin_x`, `margin`
- 底部边距: `marginBottom`, `margin_bottom`, `bottom_margin`
- 字幕高度: `height`, `subtitle_height`

**颜色格式支持**:
- 颜色名称: `"white"`, `"black"`, `"red"`, `"yellow"` 等
- 十六进制: `"#000000"`, `"#FFFFFF"` 等
- RGB数组: `[255, 255, 255]`
- RGBA数组: `[0, 0, 0, 30]` (最后一个数字是透明度)
- 透明背景: `"transparent"`

#### 3. 智能分割配置 (`auto_split_config`)
```json
{
  "max_chars_per_line": 20,
  "max_duration_per_segment": 5.0,
  "min_duration_per_segment": 1.0
}
```
**传递方式**: `auto_split_config='{"max_chars_per_line": 20, "max_duration_per_segment": 5.0}'`

#### 4. 运动检测配置 (`motion_clip_params`)
```json
{
  "motion_threshold": 0.1,
  "min_static_duration": 2.0,
  "sample_step": 1
}
```
**传递方式**: `motion_clip_params='{"motion_threshold": 0.1, "min_static_duration": 2.0}'`

### 常见错误示例
```python
# ❌ 错误：直接传递字典对象
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    segments=[{"start": "00:00:05", "end": "00:00:15"}]  # 错误！
)

# ✅ 正确：传递JSON字符串
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    segments='[{"start": "00:00:05", "end": "00:00:15"}]'  # 正确！
)

# ✅ 正确：支持多种字段名格式
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="测试字幕样式",
    subtitle_style='{"font_color": "#000000", "background_color": "transparent", "font_size": 36}'  # 支持多种字段名
)
```

##  配置说明

### 画质预设
| 预设 | 分辨率 | 比特率 | 适用场景 |
|------|--------|--------|----------|
| 240p | 426240 | 500k | 快速预览 |
| 360p | 640360 | 800k | 移动设备 |
| 480p | 854480 | 1.2M | 一般用途 |
| 720p | 1280720 | 2M | 默认设置 |
| 1080p | 19201080 | 4M | 最高质量 |

### 语音音色
- `voice_index=0`: zh-CN-XiaoxiaoNeural (默认)
- `voice_index=1-4`: 其他 Azure 语音音色

### 字幕样式配置
```json
{
    "fontSize": 50,
    "color": "white",
    "bgColor": [0, 0, 0, 30],
    "fontPath": "C:\\Windows\\Fonts\\msyh.ttc",
    "marginX": 100,
    "marginBottom": 50
}
```

##  MCP 工具函数说明

本项目基于 Model Context Protocol (MCP) 构建，提供了一套完整的视频生成工具函数。所有函数都通过 FastMCP 框架暴露为标准化接口，支持异步调用和任务管理。

### 核心视频生成函数

#### `generate_auto_video_mcp`
**主要视频生成接口**，支持完整的视频处理流程，包括语音合成、字幕生成、视频剪辑等。

**参数说明:**
- `video_path` (str): 输入视频文件路径 (必传)
- `text` (str): 要转换为语音的文本内容 (可选，为空时仅进行视频处理)
- `voice_index` (int): 语音音色索引，范围 0-4 (默认: 0)
  - 0: zh-CN-XiaoxiaoNeural (默认女声)
  - 1-4: 其他 Azure 语音音色
- `output_path` (str): 输出视频文件路径 (默认: "output_video.mp4")
- `segments_mode` (str): 视频片段处理模式 (默认: "keep")
  - "keep": 保留指定片段
  - "cut": 剪切指定片段
- `segments` (str): **视频片段配置，必须是JSON字符串格式** (可选)
  ```json
  [
    {"start": "00:00:05", "end": "00:00:15"}, 
    {"start": "00:00:30", "end": "00:00:45"}
  ]
  ```
  **注意**: 时间格式为 "HH:MM:SS"，必须使用JSON字符串格式传递
- `subtitle_style` (str): **字幕样式配置，必须是JSON字符串格式** (可选)
  ```json
  {
    "fontSize": 50,
    "color": "white",
    "bgColor": [0, 0, 0, 30],
    "fontPath": "C:\\Windows\\Fonts\\msyh.ttc",
    "marginX": 100,
    "marginBottom": 50
  }
  ```
  **注意**: 必须使用JSON字符串格式传递，不能直接传递字典对象
- `auto_split_config` (str): **智能文本分割配置，必须是JSON字符串格式** (可选)
  ```json
  {
    "max_chars_per_line": 20,
    "max_duration_per_segment": 5.0,
    "min_duration_per_segment": 1.0
  }
  ```
  **注意**: 必须使用JSON字符串格式传递
- `quality_preset` (str): 输出视频画质预设 (默认: "720p")
  - 支持: "240p", "360p", "480p", "720p", "1080p"
- `enable_motion_clip` (bool): 是否启用自动静止片段检测 (默认: False)
- `motion_clip_params` (str): **运动检测参数配置，必须是JSON字符串格式** (可选)
  ```json
  {
    "motion_threshold": 0.1,
    "min_static_duration": 2.0,
    "sample_step": 1
  }
  ```
  **注意**: 必须使用JSON字符串格式传递，不能直接传递字典对象

**返回值:** JSON 字符串，包含处理结果和状态信息

**使用示例:**
```python
# 基本使用
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="欢迎观看本视频，这是AI自动生成的解说。",
    voice_index=0,
    output_path="output.mp4",
    quality_preset="1080p"
)

# 带JSON参数的高级使用
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="欢迎观看本视频，这是AI自动生成的解说。",
    voice_index=0,
    output_path="output.mp4",
    quality_preset="1080p",
    segments='[{"start": "00:00:05", "end": "00:00:15"}]',  # JSON字符串
    segments_mode="keep",
    subtitle_style='{"fontSize": 60, "color": "yellow", "bgColor": [0, 0, 0, 128]}',  # JSON字符串
    auto_split_config='{"max_chars_per_line": 25, "max_duration_per_segment": 4.0}',  # JSON字符串
    enable_motion_clip=True,
    motion_clip_params='{"motion_threshold": 0.15, "min_static_duration": 1.5, "sample_step": 2}'  # JSON字符串
)
```

#### `generate_auto_video_sync`
**同步视频生成接口**，适合短时间任务，会阻塞直到处理完成。

**参数:** 与 `generate_auto_video_mcp` 相同

**特点:**
- 同步执行，等待处理完成
- 适合短视频或快速处理
- 直接返回最终结果

#### `generate_auto_video_async`
**异步视频生成接口**，适合长时间任务，立即返回任务ID。

**参数:** 与 `generate_auto_video_mcp` 相同

**返回值:** 任务ID字符串

**特点:**
- 异步执行，不阻塞调用
- 适合长视频或复杂处理
- 需要通过任务管理接口查询状态

### 任务管理函数

#### `get_task_status(task_id: str)`
获取指定任务的详细状态信息。

**参数:**
- `task_id` (str): 任务ID

**返回值:** JSON 字符串，包含任务状态、进度、结果等信息
```json
{
  "task_id": "uuid-string",
  "status": "pending|running|completed|failed",
  "progress": 75,
  "result": "output_video.mp4",
  "error": null,
  "start_time": "2024-01-01T10:00:00",
  "created_at": "2024-01-01T09:55:00"
}
```

#### `list_all_tasks()`
列出系统中所有任务的概览信息。

**返回值:** JSON 字符串，包含所有任务的列表
```json
[
  {
    "task_id": "uuid-1",
    "status": "completed",
    "progress": 100,
    "created_at": "2024-01-01T09:55:00"
  },
  {
    "task_id": "uuid-2", 
    "status": "running",
    "progress": 45,
    "created_at": "2024-01-01T10:00:00"
  }
]
```

#### `cancel_task(task_id: str)`
取消正在运行的任务。

**参数:**
- `task_id` (str): 要取消的任务ID

**返回值:** 操作结果字符串

### 系统信息查询函数

#### `get_system_status()`
获取系统整体状态信息，包括配置、依赖、资源等。

**返回值:** JSON 字符串，包含系统状态
```json
{
  "ffmpeg_available": true,
  "azure_speech_configured": true,
  "font_available": true,
  "temp_directory": "C:\\temp",
  "max_concurrent_tasks": 5,
  "active_tasks": 2
}
```

#### `get_available_voice_options()`
获取所有可用的语音选项列表。

**返回值:** JSON 字符串，包含语音选项
```json
[
  {
    "index": 0,
    "name": "zh-CN-XiaoxiaoNeural",
    "description": "默认女声",
    "language": "zh-CN"
  },
  {
    "index": 1,
    "name": "zh-CN-YunxiNeural", 
    "description": "男声",
    "language": "zh-CN"
  }
]
```

### 参数验证函数

#### `validate_input_parameters(text: str, video_path: str, voice_index: int = 0)`
验证输入参数的有效性和完整性。

**参数:**
- `text` (str): 要验证的文本内容
- `video_path` (str): 要验证的视频文件路径
- `voice_index` (int): 要验证的语音索引

**返回值:** JSON 字符串，包含验证结果
```json
{
  "valid": true,
  "errors": [],
  "warnings": ["视频文件较大，建议使用异步处理"],
  "video_info": {
    "duration": 120.5,
    "resolution": "1920x1080",
    "format": "mp4"
  }
}
```

#### `get_generation_estimate(text: str, video_path: str)`
根据输入参数估算视频生成所需时间。

**参数:**
- `text` (str): 文本内容
- `video_path` (str): 视频文件路径

**返回值:** JSON 字符串，包含时间估算

#### `detect_video_motion_mcp(video_path: str, config_path: str = "best_motion_clip_params.json")`
**独立的运动检测工具**，用于分析视频中的静止片段。

**参数:**
- `video_path` (str): 要分析的视频文件路径
- `config_path` (str): 运动检测配置文件路径 (默认: "best_motion_clip_params.json")

**返回值:** JSON 字符串，包含检测结果
```json
{
  "video_path": "input.mp4",
  "config": {
    "motion_threshold": 0.1,
    "min_static_duration": 2.0,
    "sample_step": 1
  },
  "static_segments": [
    {
      "start": 5.2,
      "end": 8.5,
      "duration": 3.3
    }
  ],
  "timestamps": [
    {
      "start": "00:00:05.200",
      "end": "00:00:08.500"
    }
  ],
  "summary": {
    "total_segments": 5,
    "total_static_time": 15.6,
    "average_segment_duration": 3.12
  }
}
```

#### `optimize_video_motion_params_mcp(video_path: str, target_min_duration: float = 50.0, target_max_duration: float = 70.0)`
**运动检测参数优化工具**，自动寻找最佳参数以达到目标视频时长。

**参数:**
- `video_path` (str): 要优化的视频文件路径
- `target_min_duration` (float): 目标最小时长 (秒)
- `target_max_duration` (float): 目标最大时长 (秒)

**返回值:** JSON 字符串，包含优化结果
```json
{
  "success": true,
  "optimal_config": {
    "motion_threshold": 0.15,
    "min_static_duration": 1.5,
    "sample_step": 2
  },
  "message": "找到最优参数并已保存到配置文件"
}
```
```json
{
  "estimated_time": 180,
  "time_unit": "seconds",
  "factors": {
    "video_duration": 120,
    "text_length": 500,
    "processing_complexity": "medium"
  },
  "recommendation": "建议使用异步处理"
}
```

#### `get_system_performance_info_mcp()`
**系统性能信息工具**，获取详细的硬件配置和性能数据。

**返回值:** JSON 字符串，包含系统性能信息
```json
{
  "cpu": {
    "count": 12,
    "frequency": 2500.0,
    "usage": 21.3
  },
  "memory": {
    "total": 31,
    "available": 5,
    "usage": 81.2
  },
  "gpu": {
    "name": "AMD Radeon RX 580",
    "memory": 8,
    "driver": "22.40.00.01"
  }
}
```

#### `optimize_video_processing_mcp(video_path: str, target_quality: str = "720p")`
**视频处理优化工具**，根据系统配置自动优化处理参数。

**参数:**
- `video_path` (str): 要优化的视频文件路径
- `target_quality` (str): 目标画质预设

**返回值:** JSON 字符串，包含优化配置
```json
{
  "encoder": "hevc_amf",
  "preset": "speed",
  "quality": 18,
  "threads": 16,
  "buffer_size": 2048,
  "async_depth": 6,
  "bframes": 3,
  "ref_frames": 4,
  "enable_cache": true,
  "cache_size": 4096
}
```

#### `benchmark_gpu_performance_mcp()`
**GPU性能基准测试工具**，评估当前系统的视频处理能力。

**返回值:** JSON 字符串，包含性能测试结果
```json
{
  "processing_time": 3.45,
  "speed_multiplier": 2.90,
  "encoder": "hevc_amf",
  "threads": 16,
  "async_depth": 6,
  "performance_rating": "极佳 ⭐⭐⭐⭐⭐"
}
```

### 工具函数调用流程

#### 基本使用流程
1. **参数验证**: 使用 `validate_input_parameters()` 验证输入
2. **时间估算**: 使用 `get_generation_estimate()` 估算处理时间
3. **选择接口**: 根据估算时间选择同步或异步接口
4. **任务监控**: 异步任务使用 `get_task_status()` 监控进度
5. **结果获取**: 从返回结果中获取输出文件路径

#### 高级使用流程
1. **系统检查**: 使用 `get_system_status()` 检查系统状态
2. **语音选择**: 使用 `get_available_voice_options()` 选择合适的语音
3. **批量处理**: 使用 `list_all_tasks()` 管理多个任务
4. **异常处理**: 使用 `cancel_task()` 处理异常情况

### 错误处理

所有工具函数都包含完善的错误处理机制：

- **参数错误**: 返回详细的错误描述和修正建议
- **文件错误**: 检查文件存在性和格式有效性
- **系统错误**: 检查依赖项和系统资源
- **网络错误**: 处理 Azure 语音服务连接问题
- **处理错误**: 提供详细的错误日志和恢复建议

### 性能优化建议

1. **短视频 (< 30秒)**: 使用 `generate_auto_video_sync`
2. **长视频 (> 30秒)**: 使用 `generate_auto_video_async`
3. **批量处理**: 合理控制并发任务数量
4. **资源监控**: 定期检查系统状态和资源使用情况

##  项目结构

```
auto-video-generator-mcp/
 auto_generate_video_mcp_modular.py  # 主服务器文件
 auto_video_modules/                 # 核心模块目录
    __init__.py                     # 模块初始化
    config.py                       # 配置管理
    ffmpeg_utils.py                 # FFmpeg 工具
    mcp_tools.py                    # MCP 工具接口
    motion_detection_utils.py       # 运动检测工具
    gpu_optimization_utils.py       # GPU优化工具
    subtitle_utils.py               # 字幕处理
    video_utils.py                  # 视频处理
    voice_utils.py                  # 语音处理
 requirements.txt                    # Python 依赖
 README.md                          # 中文文档（默认）
 README_EN.md                       # 英文文档
```

##  故障排除

### 常见问题

#### 1. FFmpeg 未找到
**错误**: `FFmpeg not found in system PATH`
**解决**: 确保 FFmpeg 已安装并添加到系统 PATH，或设置 `FFMPEG_PATH` 环境变量。

#### 2. Azure 语音服务错误
**错误**: `Azure Speech Service authentication failed`
**解决**: 检查 `AZURE_SPEECH_KEY` 和 `AZURE_SPEECH_REGION` 环境变量配置。

#### 3. 字体文件未找到
**错误**: `Font file not found`
**解决**: 确保系统安装了微软雅黑字体，或修改 `config.py` 中的字体路径。

#### 4. 内存不足
**错误**: `Memory error during video processing`
**解决**: 使用较低的画质预设，或减少并发任务数量。

### 调试模式
设置环境变量 `DEBUG_MODE=true` 启用详细日志输出。

##  贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

##  许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

##  支持

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至项目维护者
- 查看项目 Wiki 获取更多信息

##  更新日志

### v3.0.0
- 重构为模块化架构
- 添加异步任务处理
- 支持多种画质预设
- 改进配置管理系统

### v2.0.0
- 添加智能文本分割
- 支持时间标记控制
- 改进字幕样式配置

### v1.0.0
- 初始版本发布
- 基础视频生成功能
- Azure 语音服务集成

##  使用场景示例

### 1. 教育视频制作
```python
# 为教学视频添加解说
result = await generate_auto_video_mcp(
    video_path="lecture.mp4",
    text="欢迎来到今天的课程。我们将学习人工智能的基础知识。首先，让我们了解什么是机器学习。",
    voice_index=0,
    quality_preset="720p",
    subtitle_style='{"fontSize": 60, "color": "white", "bgColor": [0, 0, 0, 50]}'  # JSON字符串
)
```

### 2. 产品演示视频
```python
# 产品功能演示
result = await generate_auto_video_mcp(
    video_path="product_demo.mp4",
    text="这款产品具有以下特点：{2s}第一，操作简单易用。{1s}第二，功能强大全面。{1s}第三，性价比极高。",
    voice_index=1,
    subtitle_style='{"fontSize": 60, "color": "yellow", "bgColor": [0, 0, 0, 30]}'  # JSON字符串
)
```

### 3. 视频剪辑和优化
```python
# 仅进行视频处理，不添加语音
result = await generate_auto_video_mcp(
    video_path="raw_video.mp4",
    text="",  # 空文本，只进行视频处理
    segments_mode="cut",
    segments='[{"start": "00:00:10", "end": "00:00:20"}]',  # JSON字符串
    quality_preset="1080p",
    enable_gpu_acceleration=True  # 启用极致GPU优化
)
```

##  大模型调用指南

### 重要提醒
当大模型调用本系统的工具函数时，**所有配置参数都必须使用JSON字符串格式**，不能直接传递字典对象。

### 正确的调用方式

#### 1. 基本视频生成
```python
# ✅ 正确：所有参数都是字符串格式
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="欢迎观看本视频",
    voice_index=0,
    output_path="output.mp4",
    quality_preset="720p"
)
```

#### 2. 带JSON参数的调用
```python
# ✅ 正确：JSON参数使用字符串格式
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="视频内容",
    segments='[{"start": "00:00:05", "end": "00:00:15"}]',  # JSON字符串
    subtitle_style='{"fontSize": 50, "color": "white"}',  # JSON字符串
    motion_clip_params='{"motion_threshold": 0.1, "min_static_duration": 2.0}',  # JSON字符串
    enable_gpu_acceleration=True
)
```

#### 3. 错误示例
```python
# ❌ 错误：直接传递字典对象
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    segments=[{"start": "00:00:05", "end": "00:00:15"}],  # 错误！
    subtitle_style={"fontSize": 50, "color": "white"},  # 错误！
    motion_clip_params={"motion_threshold": 0.1}  # 错误！
)
```

### JSON字符串构建方法
```python
import json

# 方法1：使用json.dumps()
segments = json.dumps([{"start": "00:00:05", "end": "00:00:15"}])
subtitle_style = json.dumps({"fontSize": 50, "color": "white"})

# 方法2：直接写字符串
segments = '[{"start": "00:00:05", "end": "00:00:15"}]'
subtitle_style = '{"fontSize": 50, "color": "white"}'
```

##  最佳实践

### 1. 性能优化
- 对于长视频，建议使用异步任务处理
- 根据需求选择合适的画质预设
- 定期清理临时文件

### 2. 文本处理
- 合理使用时间标记控制节奏
- 避免过长的单段文本
- 利用智能分割功能优化字幕显示

### 3. 错误处理
- 始终检查输入参数的有效性
- 监控任务状态，及时处理异常
- 使用调试模式排查问题

##  特色功能

### 智能文本分割
系统会自动将长文本分割成适合显示的字幕片段，确保良好的观看体验。

### 时间标记语法
支持在文本中使用时间标记来控制静默时间：
- `{5s}` - 5秒静默
- `{5000ms}` - 5000毫秒静默
- `{2.5s}` - 2.5秒静默

### 多任务并发
支持同时处理多个视频生成任务，提高工作效率。

### 实时状态监控
提供完整的任务状态跟踪，实时了解处理进度。
