"""
自动视频生成模块包
提供完整的视频生成功能，包括语音合成、字幕生成、视频处理等
"""

# 核心模块
from . import ffmpeg_utils
from . import voice_utils
from . import audio_utils
from . import subtitle_utils
from . import video_utils
from . import mcp_tools
from . import video_processing_utils

# 版本信息
__version__ = "2.0.0"
__author__ = "Auto Video Generator Team"
__description__ = "模块化自动视频生成系统"

# 模块列表
__all__ = [
    # 核心模块
    "ffmpeg_utils",
    "voice_utils", 
    "audio_utils",
    "subtitle_utils",
    "video_utils",
    "mcp_tools",
    "video_processing_utils",

    # 版本信息
    "__version__",
    "__author__",
    "__description__"
] 