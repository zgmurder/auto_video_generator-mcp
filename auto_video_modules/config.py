"""
配置管理模块
集中管理所有模块的配置参数
"""

import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class FFmpegConfig:
    """FFmpeg配置"""
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    timeout: int = 30
    log_level: str = "error"

@dataclass
class VoiceConfig:
    """语音配置"""
    subscription_key: str = ""
    region: str = "eastasia"
    speech_synthesis_voice_name: str = "zh-CN-XiaoxiaoNeural"
    speech_synthesis_language: str = "zh-CN"
    speech_synthesis_output_format: str = "Audio-16khz-32kbitrate-Mono-MP3"

@dataclass
class AudioConfig:
    """音频配置"""
    sample_rate: int = 16000
    channels: int = 1
    bitrate: str = "32k"
    format: str = "mp3"
    temp_dir: str = "temp"

@dataclass
class SubtitleConfig:
    """字幕配置"""
    max_length: int = 50
    font_size: int = 50
    font_color: str = "white"
    bg_color: tuple = (0, 0, 0, 30)
    margin_x: int = 100
    margin_bottom: int = 50
    font_path: str = r"C:\Windows\Fonts\msyh.ttc"  # 默认使用微软雅黑

@dataclass
class VideoConfig:
    """视频配置"""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    codec: str = "libx264"
    bitrate: str = "2M"
    output_format: str = "mp4"
    temp_dir: str = "temp"
    quality_preset: str = "720p"  # 画质预设: 240p, 360p, 480p, 720p, 1080p
    
    def get_resolution_by_quality(self, quality: Optional[str] = None) -> tuple:
        """根据画质预设获取分辨率
        
        Args:
            quality: 画质预设，如果为None则使用当前配置
            
        Returns:
            tuple: (width, height) 分辨率
        """
        quality = quality or self.quality_preset
        
        quality_map = {
            "240p": (426, 240),
            "360p": (640, 360),
            "480p": (854, 480),
            "720p": (1280, 720),
            "1080p": (1920, 1080)
        }
        
        return quality_map.get(quality.lower(), (1280, 720))
    
    def get_bitrate_by_quality(self, quality: Optional[str] = None) -> str:
        """根据画质预设获取比特率
        
        Args:
            quality: 画质预设，如果为None则使用当前配置
            
        Returns:
            str: 比特率字符串
        """
        quality = quality or self.quality_preset
        
        bitrate_map = {
            "240p": "500k",
            "360p": "800k",
            "480p": "1.2M",
            "720p": "2M",
            "1080p": "4M"
        }
        
        return bitrate_map.get(quality.lower(), "2M")
    
    def set_quality(self, quality: str):
        """设置画质预设
        
        Args:
            quality: 画质预设 (240p, 360p, 480p, 720p, 1080p)
        """
        valid_qualities = ["240p", "360p", "480p", "720p", "1080p"]
        if quality.lower() not in [q.lower() for q in valid_qualities]:
            raise ValueError(f"不支持的画质: {quality}，支持: {valid_qualities}")
        
        self.quality_preset = quality.lower()
        width, height = self.get_resolution_by_quality(quality)
        self.width = width
        self.height = height
        self.bitrate = self.get_bitrate_by_quality(quality)

@dataclass
class SystemConfig:
    """系统配置"""
    max_workers: int = 10
    timeout: int = 300
    cleanup_temp_files: bool = True
    debug_mode: bool = False

@dataclass
class AutoSplitConfig:
    """智能分割配置"""
    enabled: bool = True  # 默认开启智能分割
    max_length: int = 20
    min_length: int = 5
    split_chars: str = "。！？；，、"
    preserve_punctuation: bool = True

@dataclass
class DuplicateFrameConfig:
    """
    Configuration for detecting and removing duplicate/static frames.
    """
    method: str = 'hist'
    similarity_threshold: float = 0.98
    resize_for_comparison: bool = True
    comparison_size: Tuple[int, int] = (32, 32)

@dataclass
class MainConfig:
    """主配置类"""
    ffmpeg: FFmpegConfig = field(default_factory=FFmpegConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    subtitle: SubtitleConfig = field(default_factory=SubtitleConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    auto_split: AutoSplitConfig = field(default_factory=AutoSplitConfig)
    duplicate_frame: DuplicateFrameConfig = field(default_factory=DuplicateFrameConfig)
    
    workspace: str = "workspace"

    def __post_init__(self):
        # 确保工作区目录存在
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
            
    def get_ffmpeg_config(self) -> FFmpegConfig:
        return self.ffmpeg
        
    def get_voice_config(self) -> VoiceConfig:
        return self.voice
        
    def get_audio_config(self) -> AudioConfig:
        return self.audio
        
    def get_subtitle_config(self) -> SubtitleConfig:
        return self.subtitle
        
    def get_video_config(self) -> VideoConfig:
        return self.video
        
    def get_system_config(self) -> SystemConfig:
        return self.system
        
    def get_auto_split_config(self) -> AutoSplitConfig:
        """获取智能分割配置"""
        return self.auto_split
        
    def get_duplicate_frame_config(self) -> DuplicateFrameConfig:
        """获取重复帧检测配置"""
        return self.duplicate_frame

final_config = MainConfig()

def get_config() -> MainConfig:
    """获取全局配置实例"""
    return final_config 