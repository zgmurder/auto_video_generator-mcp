"""
配置管理模块
集中管理所有模块的配置参数
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

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
    subscription_key: Optional[str] = None
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
    font_size: int = 40
    font_color: str = "white"
    bg_color: tuple = (0, 0, 0, 0)
    margin_x: int = 100
    margin_bottom: int = 50
    font_path: str = "arial.ttf"

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

@dataclass
class SystemConfig:
    """系统配置"""
    max_workers: int = 4
    timeout: int = 300
    cleanup_temp_files: bool = True
    debug_mode: bool = False

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.ffmpeg = FFmpegConfig()
        self.voice = VoiceConfig()
        self.audio = AudioConfig()
        self.subtitle = SubtitleConfig()
        self.video = VideoConfig()
        self.system = SystemConfig()
        
        # 从环境变量加载配置
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # FFmpeg配置
        ffmpeg_path = os.getenv("FFMPEG_PATH")
        if ffmpeg_path:
            self.ffmpeg.ffmpeg_path = ffmpeg_path
        ffprobe_path = os.getenv("FFPROBE_PATH")
        if ffprobe_path:
            self.ffmpeg.ffprobe_path = ffprobe_path
        
        # 语音配置
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        if speech_key:
            self.voice.subscription_key = speech_key
        speech_region = os.getenv("AZURE_SPEECH_REGION")
        if speech_region:
            self.voice.region = speech_region
        
        # 系统配置
        debug_mode = os.getenv("DEBUG_MODE")
        if debug_mode:
            self.system.debug_mode = debug_mode.lower() == "true"
    
    def get_ffmpeg_config(self) -> FFmpegConfig:
        """获取FFmpeg配置"""
        return self.ffmpeg
    
    def get_voice_config(self) -> VoiceConfig:
        """获取语音配置"""
        return self.voice
    
    def get_audio_config(self) -> AudioConfig:
        """获取音频配置"""
        return self.audio
    
    def get_subtitle_config(self) -> SubtitleConfig:
        """获取字幕配置"""
        return self.subtitle
    
    def get_video_config(self) -> VideoConfig:
        """获取视频配置"""
        return self.video
    
    def get_system_config(self) -> SystemConfig:
        """获取系统配置"""
        return self.system
    
    def update_config(self, config_type: str, **kwargs):
        """更新配置
        
        Args:
            config_type: 配置类型 (ffmpeg, voice, audio, subtitle, video, system)
            **kwargs: 要更新的配置项
        """
        config_map = {
            "ffmpeg": self.ffmpeg,
            "voice": self.voice,
            "audio": self.audio,
            "subtitle": self.subtitle,
            "video": self.video,
            "system": self.system
        }
        
        if config_type not in config_map:
            raise ValueError(f"未知的配置类型: {config_type}")
        
        config = config_map[config_type]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                raise ValueError(f"配置项 {key} 不存在于 {config_type} 配置中")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "ffmpeg": self.ffmpeg.__dict__,
            "voice": self.voice.__dict__,
            "audio": self.audio.__dict__,
            "subtitle": self.subtitle.__dict__,
            "video": self.video.__dict__,
            "system": self.system.__dict__
        }
    
    def from_dict(self, config_dict: Dict[str, Any]):
        """从字典加载配置"""
        for config_type, config_data in config_dict.items():
            if hasattr(self, config_type):
                config = getattr(self, config_type)
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
    
    def validate(self) -> Dict[str, list]:
        """验证配置
        
        Returns:
            验证结果，包含错误和警告信息
        """
        errors = []
        warnings = []
        
        # 检查必要的配置
        if not self.voice.subscription_key:
            errors.append("Azure语音服务密钥未配置")
        
        if not os.path.exists(self.ffmpeg.ffmpeg_path):
            errors.append(f"FFmpeg路径不存在: {self.ffmpeg.ffmpeg_path}")
        
        if not os.path.exists(self.ffmpeg.ffprobe_path):
            errors.append(f"FFprobe路径不存在: {self.ffmpeg.ffprobe_path}")
        
        # 检查配置合理性
        if self.subtitle.max_length < 10:
            warnings.append("字幕最大长度过小，可能影响显示效果")
        
        if self.video.width < 640 or self.video.height < 480:
            warnings.append("视频分辨率过低，可能影响质量")
        
        if self.audio.sample_rate < 8000:
            warnings.append("音频采样率过低，可能影响音质")
        
        return {"errors": errors, "warnings": warnings}
    
    def get_config_summary(self) -> str:
        """获取配置摘要"""
        validation = self.validate()
        
        summary = "配置摘要:\n"
        summary += f"FFmpeg: {self.ffmpeg.ffmpeg_path}\n"
        summary += f"语音服务: {self.voice.region}\n"
        summary += f"视频分辨率: {self.video.width}x{self.video.height}\n"
        summary += f"音频格式: {self.audio.format}\n"
        summary += f"字幕字体: {self.subtitle.font_path}\n"
        summary += f"调试模式: {self.system.debug_mode}\n"
        
        if validation["errors"]:
            summary += "\n配置错误:\n"
            for error in validation["errors"]:
                summary += f"  - {error}\n"
        
        if validation["warnings"]:
            summary += "\n配置警告:\n"
            for warning in validation["warnings"]:
                summary += f"  - {warning}\n"
        
        return summary

# 全局配置实例
config = ConfigManager()

def get_config() -> ConfigManager:
    """获取全局配置实例"""
    return config 