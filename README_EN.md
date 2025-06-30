# Auto Video Generator MCP

**English** | [中文](README_CN.md)

A smart video generation system based on MCP (Model Context Protocol), supporting automatic subtitle generation, voice synthesis, and video editing.

##  Features

### Core Features
- **Smart Video Editing**: Support video segment keep/cut modes
- **Automatic Subtitle Generation**: Intelligent text splitting and subtitle style customization
- **Voice Synthesis**: Integrated Azure Speech Service with multiple voice options
- **Multi-Quality Output**: Support 240p to 1080p quality presets
- **Async Task Processing**: Support long-running task processing
- **Time Mark Control**: Support time marks in text to control silence duration

### Technical Features
- **Modular Architecture**: Clear module separation for easy maintenance and extension
- **MCP Protocol**: Standardized interface based on FastMCP
- **Configuration Management**: Flexible configuration system with environment variable support
- **Task Management**: Complete task status tracking and management
- **Temporary File Cleanup**: Automatic cleanup of temporary files during processing

##  System Requirements

### Software Dependencies
- Python 3.8+
- FFmpeg (pre-installed and configured in system PATH)
- Windows system (font path configuration)

### Python Dependencies
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

##  Installation & Configuration

### 1. Clone Project
```bash
git clone https://github.com/zgmurder/auto_video_generator-mcp.git
cd auto-video-generator-mcp
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Azure Speech Service Configuration
export AZURE_SPEECH_KEY="your_azure_speech_key"
export AZURE_SPEECH_REGION="eastasia"

# FFmpeg Path Configuration (Optional)
export FFMPEG_PATH="path/to/ffmpeg"
export FFPROBE_PATH="path/to/ffprobe"

# Debug Mode (Optional)
export DEBUG_MODE="true"
```

### 4. Start Server
```bash
python auto_generate_video_mcp_modular.py
```

The server will start at `http://localhost:8000/sse`.

##  Usage Guide

### Basic Usage

#### 1. Simple Video Generation
```python
# Generate video with subtitles and voice
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="Welcome to this video, this is AI-generated commentary.",
    voice_index=0,
    output_path="output.mp4"
)
```

#### 2. Custom Quality
```python
# Generate HD video
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="HD video content",
    quality_preset="1080p"
)
```

#### 3. Video Segment Processing
```python
# Keep specified segments
segments = '[{"start": "00:00:05", "end": "00:00:15"}]'
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="Segment commentary",
    segments_mode="keep",
    segments=segments
)
```

### Advanced Features

#### 1. Time Mark Control
```python
# Use time marks to control silence duration
text = "{5s}Welcome to watch{5000ms}this video is automatically edited by AI and adds intelligent subtitles and voice commentary.{2s}Thank you for watching!"
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text=text
)
```

#### 2. Custom Subtitle Style
```python
subtitle_style = '{"fontSize": 60, "color": "yellow", "bgColor": [0, 0, 0, 128]}'
result = await generate_auto_video_mcp(
    video_path="input.mp4",
    text="Custom subtitle style",
    subtitle_style=subtitle_style
)
```

#### 3. Async Task Processing
```python
# Create async task
task_id = await generate_auto_video_async(
    video_path="input.mp4",
    text="Long processing task"
)

# Query task status
status = await get_task_status(task_id)

# Cancel task
await cancel_task(task_id)
```

##  Configuration

### Quality Presets
| Preset | Resolution | Bitrate | Use Case |
|--------|------------|---------|----------|
| 240p | 426240 | 500k | Quick Preview |
| 360p | 640360 | 800k | Mobile Devices |
| 480p | 854480 | 1.2M | General Use |
| 720p | 1280720 | 2M | Default Setting |
| 1080p | 19201080 | 4M | Highest Quality |

### Voice Options
- `voice_index=0`: zh-CN-XiaoxiaoNeural (Default)
- `voice_index=1-4`: Other Azure voice options

### Subtitle Style Configuration
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

##  API Interfaces

### Core Function Interfaces

#### `generate_auto_video_mcp`
Main video generation interface with async task support.

**Parameters:**
- `video_path` (str): Video file path (required)
- `text` (str): Text to convert (optional)
- `voice_index` (int): Voice index 0-4 (default: 0)
- `output_path` (str): Output video path (default: "output_video.mp4")
- `segments_mode` (str): Video segment mode "keep" or "cut" (default: "keep")
- `segments` (str): Video segment configuration JSON string (optional)
- `subtitle_style` (str): Subtitle style configuration JSON string (optional)
- `auto_split_config` (str): Auto-split configuration JSON string (optional)
- `quality_preset` (str): Quality preset (default: "720p")

#### `generate_auto_video_sync`
Synchronous video generation interface, suitable for short tasks.

#### `generate_auto_video_async`
Asynchronous video generation interface, suitable for long tasks.

### Task Management Interfaces

#### `get_task_status(task_id)`
Get task status and progress information.

#### `list_all_tasks()`
List all tasks and their status.

#### `cancel_task(task_id)`
Cancel running task.

### Configuration Query Interfaces

#### `get_system_status()`
Get system status information.

#### `get_available_voice_options()`
Get available voice options.

#### `validate_input_parameters(text, video_path, voice_index)`
Validate input parameter validity.

#### `get_generation_estimate(text, video_path)`
Get generation time estimate.

##  Project Structure

```
auto-video-generator-mcp/
 auto_generate_video_mcp_modular.py  # Main server file
 auto_video_modules/                 # Core modules directory
    __init__.py                     # Module initialization
    config.py                       # Configuration management
    ffmpeg_utils.py                 # FFmpeg utilities
    mcp_tools.py                    # MCP tool interfaces
    subtitle_utils.py               # Subtitle processing
    video_utils.py                  # Video processing
    voice_utils.py                  # Voice processing
 requirements.txt                    # Python dependencies
 README.md                          # Chinese documentation (default)
 README_EN.md                       # English documentation
```

##  Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found
**Error**: `FFmpeg not found in system PATH`
**Solution**: Ensure FFmpeg is installed and added to system PATH, or set `FFMPEG_PATH` environment variable.

#### 2. Azure Speech Service Error
**Error**: `Azure Speech Service authentication failed`
**Solution**: Check `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` environment variable configuration.

#### 3. Font File Not Found
**Error**: `Font file not found`
**Solution**: Ensure Microsoft YaHei font is installed, or modify font path in `config.py`.

#### 4. Memory Insufficient
**Error**: `Memory error during video processing`
**Solution**: Use lower quality preset, or reduce concurrent task count.

### Debug Mode
Set environment variable `DEBUG_MODE=true` to enable detailed log output.

##  Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Support

For questions or suggestions, please contact us through:

- Submit Issue
- Send email to project maintainer
- Check project Wiki for more information

##  Changelog

### v3.0.0
- Refactored to modular architecture
- Added async task processing
- Support multiple quality presets
- Improved configuration management system

### v2.0.0
- Added intelligent text splitting
- Support time mark control
- Improved subtitle style configuration

### v1.0.0
- Initial version release
- Basic video generation functionality
- Azure Speech Service integration
