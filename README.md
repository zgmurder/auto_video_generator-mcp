# Auto Video Generator MCP

[English](README_EN.md) | [中文](README.md)

一个基于 MCP (Model Context Protocol) 的智能视频生成系统，支持自动添加字幕、语音合成和视频剪辑功能。

##  功能特性

### 核心功能
- **智能视频剪辑**: 支持视频片段保留/剪切模式
- **自动删除重复帧/静止片段**: 一键检测并剪掉无效画面，提升视频精华度（可选参数，默认关闭）
- **自动字幕生成**: 智能文本分割和字幕样式自定义
- **语音合成**: 集成 Azure 语音服务，支持多种音色
- **多画质输出**: 支持 240p 到 1080p 多种画质预设
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
# Azure 语音服务配置
export AZURE_SPEECH_KEY="your_azure_speech_key"
export AZURE_SPEECH_REGION="eastasia"

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
# 保留指定片段
segments = '[{"start": "00:00:05", "end": "00:00:15"}]'
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="片段解说",
    segments_mode="keep",
    segments=segments
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
subtitle_style = '{"fontSize": 60, "color": "yellow", "bgColor": [0, 0, 0, 128]}'
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="自定义字幕样式",
    subtitle_style=subtitle_style
)
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
import json
with open("best_motion_clip_params.json", "r", encoding="utf-8") as f:
    motion_params = json.load(f)
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    output_path="output_motion_clip.mp4",
    enable_motion_clip=True,  # 启用自动静止片段检测
    motion_clip_params=motion_params  # 可选，传入推荐参数或自定义
)
```

> **说明**：
> - `enable_motion_clip=True` 时，系统会自动分析视频，检测并剪掉所有静止/重复帧片段。
> - `motion_clip_params` 可选，支持自定义运动阈值、最小静止时长、采样步长等，推荐直接用 `best_motion_clip_params.json`。
> - 不影响原有字幕、语音等功能，完全兼容。

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

##  API 接口

### 核心功能接口

#### `generate_auto_video_mcp`
主要视频生成接口，支持异步任务处理。

**参数:**
- `video_path` (str): 视频文件路径 (必传)
- `text` (str): 要转换的文本 (可选)
- `voice_index` (int): 语音音色索引 0-4 (默认: 0)
- `output_path` (str): 输出视频路径 (默认: "output_video.mp4")
- `segments_mode` (str): 视频片段模式 "keep" 或 "cut" (默认: "keep")
- `segments` (str): 视频片段配置 JSON 字符串 (可选)
- `subtitle_style` (str): 字幕样式配置 JSON 字符串 (可选)
- `auto_split_config` (str): 智能分割配置 JSON 字符串 (可选)
- `quality_preset` (str): 画质预设 (默认: "720p")
- `enable_motion_clip` (bool): 是否自动检测并剪掉静止/重复帧片段（默认 False）
- `motion_clip_params` (dict): 运动检测参数（可选，推荐用 best_motion_clip_params.json）

#### `generate_auto_video_sync`
同步视频生成接口，适合短时间任务。

#### `generate_auto_video_async`
异步视频生成接口，适合长时间任务。

### 任务管理接口

#### `get_task_status(task_id)`
获取任务状态和进度信息。

#### `list_all_tasks()`
列出所有任务及其状态。

#### `cancel_task(task_id)`
取消正在运行的任务。

### 配置查询接口

#### `get_system_status()`
获取系统状态信息。

#### `get_available_voice_options()`
获取可用的语音选项。

#### `validate_input_parameters(text, video_path, voice_index)`
验证输入参数的有效性。

#### `get_generation_estimate(text, video_path)`
获取生成时间估算。

##  项目结构

```
auto-video-generator-mcp/
 auto_generate_video_mcp_modular.py  # 主服务器文件
 auto_video_modules/                 # 核心模块目录
    __init__.py                     # 模块初始化
    config.py                       # 配置管理
    ffmpeg_utils.py                 # FFmpeg 工具
    mcp_tools.py                    # MCP 工具接口
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
    quality_preset="720p"
)
```

### 2. 产品演示视频
```python
# 产品功能演示
result = await generate_auto_video_mcp(
    video_path="product_demo.mp4",
    text="这款产品具有以下特点：{2s}第一，操作简单易用。{1s}第二，功能强大全面。{1s}第三，性价比极高。",
    voice_index=1,
    subtitle_style='{"fontSize": 60, "color": "yellow"}'
)
```

### 3. 视频剪辑和优化
```python
# 仅进行视频处理，不添加语音
result = await generate_auto_video_mcp(
    video_path="raw_video.mp4",
    text="",  # 空文本，只进行视频处理
    segments_mode="cut",
    segments='[{"start": "00:00:10", "end": "00:00:20"}]',
    quality_preset="1080p"
)
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
