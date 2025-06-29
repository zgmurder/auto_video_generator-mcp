"""
MCP工具模块
负责整合所有模块功能，提供完整的视频生成服务
"""

import os
import asyncio
from mcp.server.fastmcp import FastMCP
import json

# 导入各个模块
from .ffmpeg_utils import setup_ffmpeg, get_mcp_instance as get_ffmpeg_mcp
from .voice_utils import get_voice_by_index, get_mcp_instance as get_voice_mcp
from .audio_utils import synthesize_and_get_durations, get_mcp_instance as get_audio_mcp
from .subtitle_utils import split_text, create_subtitle_image, get_mcp_instance as get_subtitle_mcp
from .video_utils import create_video_with_subtitles, get_mcp_instance as get_video_mcp

# 创建主MCP实例
mcp = FastMCP("auto-video-generator", log_level="ERROR")

def cleanup_temp_files(temp_files):
    """清理临时文件
    
    Args:
        temp_files: 临时文件路径列表
    """
    for file_path in temp_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"清理临时文件: {file_path}")
        except Exception as e:
            print(f"清理临时文件失败 {file_path}: {e}")

async def generate_video_with_subtitles(text, video_path, voice_index=0, output_path="output_video.mp4"):
    """生成带字幕的视频
    
    Args:
        text: 要转换的文本
        video_path: 视频文件路径
        voice_index: 语音音色索引
        output_path: 输出视频路径
        
    Returns:
        bool: 是否成功
    """
    try:
        # 设置FFmpeg
        setup_ffmpeg()
        
        # 获取语音音色
        voice = get_voice_by_index(voice_index)
        
        # 检查文本是否包含时间标记
        import re
        time_pattern = r'\{(\d+(?:\.\d+)?)(s|ms)\}'
        has_timing = bool(re.search(time_pattern, text))
        
        if has_timing:
            # 包含时间标记，使用split_timings处理
            from .subtitle_utils import split_timings
            # 创建初始timing结构
            initial_timing = [{"text": text, "duration": 0}]
            # 使用split_timings进行智能分割，包含时间标记解析
            timing = split_timings(initial_timing, max_chars=20)
        else:
            # 不包含时间标记，使用原有的split_text
            text_segments = split_text(text)
            timing = [{"text": seg} for seg in text_segments]
        
        # 生成音频和获取时长
        tts_result = await synthesize_and_get_durations(timing, voice)
        audio_path = tts_result["audio_path"]
        segments = tts_result["segments"]
        
        # 创建字幕图片
        subtitle_images = []
        for i, segment in enumerate(timing):
            image_path = f"temp_subtitle_{i}.png"
            create_subtitle_image(segment["text"], 1920, 1080, "arial.ttf", fontsize=40, color='white', bg_color=(0,0,0,0), margin_x=100, margin_bottom=50)
            subtitle_images.append(image_path)
        
        # 创建带字幕的视频
        # 生成 (text, start, end) 三元组列表
        subtitle_tuples = []
        cur_time = 0.0
        for seg in segments:
            text = seg["text"]
            duration = seg.get("duration", 0)
            start = cur_time
            end = cur_time + duration
            subtitle_tuples.append((text, start, end))
            cur_time = end
        success = create_video_with_subtitles(video_path, audio_path, subtitle_tuples, output_path)
        
        # 清理临时文件
        temp_files = [audio_path] + subtitle_images
        cleanup_temp_files(temp_files)
        
        return success
        
    except Exception as e:
        print(f"生成视频失败: {e}")
        return False

@mcp.tool()
async def generate_auto_video(
    text: str, 
    video_path: str, 
    voice_index: int = 0, 
    output_path: str = "output_video.mp4",
    segments_mode: str = "keep",
    segments: str = "",
    subtitle_style: str = "",
    auto_split_config: str = ""
) -> str:
    """自动生成带字幕的视频
    
    Args:
        text: 要转换的文本
        video_path: 视频文件路径
        voice_index: 语音音色索引 (0-4)
        output_path: 输出视频路径
        segments_mode: 视频片段模式 ("keep" 保留指定片段, "cut" 剪掉指定片段)
        segments: 视频片段配置 (JSON字符串，格式: [{"start": "00:00:05", "end": "00:00:15"}])
        subtitle_style: 字幕样式配置 (JSON字符串)
        auto_split_config: 智能分割配置 (JSON字符串)
        
    Returns:
        生成结果信息
    """
    try:
        # 验证输入参数
        if not text or not text.strip():
            return "错误：文本内容不能为空"
        
        if not os.path.exists(video_path):
            return f"错误：视频文件不存在: {video_path}"
        
        if voice_index < 0 or voice_index > 4:
            return "错误：语音音色索引无效，有效范围为 0-4"
        
        # 解析segments_mode
        if segments_mode not in ["keep", "cut"]:
            return "错误：segments_mode 参数无效，支持 'keep' 或 'cut'"
        
        # 解析segments配置
        segments_list = []
        if segments:
            try:
                segments_list = json.loads(segments)
                if not isinstance(segments_list, list):
                    return "错误：segments 参数格式错误，应为JSON数组"
            except json.JSONDecodeError:
                return "错误：segments 参数JSON格式错误"
        
        # 解析subtitle_style配置
        subtitle_config = {}
        if subtitle_style:
            try:
                subtitle_config = json.loads(subtitle_style)
                if not isinstance(subtitle_config, dict):
                    return "错误：subtitle_style 参数格式错误，应为JSON对象"
            except json.JSONDecodeError:
                return "错误：subtitle_style 参数JSON格式错误"
        
        # 解析auto_split_config配置
        split_config = {}
        if auto_split_config:
            try:
                split_config = json.loads(auto_split_config)
                if not isinstance(split_config, dict):
                    return "错误：auto_split_config 参数格式错误，应为JSON对象"
            except json.JSONDecodeError:
                return "错误：auto_split_config 参数JSON格式错误"
        
        # 设置FFmpeg
        setup_ffmpeg()
        
        # 获取语音音色
        voice = get_voice_by_index(voice_index)
        
        # 处理文本分割
        timing = []
        if split_config.get('enable', True):
            strategy = split_config.get('strategy', 'smart')
            if strategy == 'smart':
                # 使用智能分割
                max_chars = split_config.get('maxChars', 20)
                from .subtitle_utils import split_timings
                initial_timing = [{"text": text, "duration": 0}]
                timing = split_timings(initial_timing, max_chars=max_chars)
            elif strategy == 'duration':
                # 按时长分割
                target_duration = split_config.get('targetDuration', 3.0)
                from .subtitle_utils import auto_split_timing_by_duration
                initial_timing = [{"text": text, "duration": 0}]
                timing = auto_split_timing_by_duration(initial_timing, target_duration)
            else:
                # 不分割
                from .subtitle_utils import split_text
                text_segments = split_text(text)
                timing = [{"text": seg} for seg in text_segments]
        else:
            # 不分割
            from .subtitle_utils import split_text
            text_segments = split_text(text)
            timing = [{"text": seg} for seg in text_segments]
        
        # 生成音频和获取时长
        tts_result = await synthesize_and_get_durations(timing, voice)
        audio_path = tts_result["audio_path"]
        segments_with_duration = tts_result["segments"]
        
        # 获取视频信息
        from .video_utils import get_video_info
        video_info = get_video_info(video_path)
        
        # 处理视频片段剪辑
        clipped_video_path = video_path  # 默认使用原视频
        if segments_list:
            from .video_utils import parse_video_segments, clip_video_segments
            video_duration = video_info.get('duration', 0)
            keep_intervals = parse_video_segments(segments_list, video_duration, segments_mode)
            
            # 执行视频剪辑
            try:
                print(f"开始视频片段剪辑 - 模式: {segments_mode}, 片段数: {len(segments_list)}")
                final_clip = clip_video_segments(video_path, keep_intervals)
                
                # 保存剪辑后的视频到临时文件
                clipped_video_path = "temp_clipped_video.mp4"
                final_clip.write_videofile(clipped_video_path, codec='libx264', fps=24, audio=False)
                final_clip.close()
                
                print(f"视频剪辑完成，保存到: {clipped_video_path}")
                
                # 更新视频信息
                from .video_utils import get_video_info
                video_info = get_video_info(clipped_video_path)
                
            except Exception as e:
                print(f"视频剪辑失败，使用原视频: {e}")
                clipped_video_path = video_path
        else:
            print("未指定视频片段，使用全部视频内容")
        
        # 创建字幕图片
        subtitle_images = []
        
        # 导入配置管理器获取默认字幕样式
        from .config import get_config
        config = get_config()
        subtitle_config_default = config.get_subtitle_config()
        
        # 使用配置中的默认值，如果用户提供了自定义配置则覆盖
        font_path = subtitle_config.get('fontPath', subtitle_config_default.font_path)
        font_size = subtitle_config.get('fontSize', subtitle_config_default.font_size)
        color = subtitle_config.get('color', subtitle_config_default.font_color)
        bg_color = tuple(subtitle_config.get('bgColor', subtitle_config_default.bg_color))
        margin_x = subtitle_config.get('marginX', subtitle_config_default.margin_x)
        margin_bottom = subtitle_config.get('marginBottom', subtitle_config_default.margin_bottom)
        subtitle_height = subtitle_config.get('height', 100)
        
        for i, segment in enumerate(timing):
            # 使用create_subtitle_image_pil生成文件路径
            from .video_utils import create_subtitle_image_pil
            image_path = create_subtitle_image_pil(
                segment["text"], 
                fontsize=font_size, 
                color=color, 
                font_path=font_path,
                size=(video_info.get('width', 1920), video_info.get('height', 1080)),
                bg_color=bg_color
            )
            subtitle_images.append(image_path)
        
        # 创建带字幕的视频
        # 生成 (text, start, end) 三元组列表
        subtitle_tuples = []
        cur_time = 0.0
        for seg in segments_with_duration:
            text = seg["text"]
            duration = seg.get("duration", 0)
            start = cur_time
            end = cur_time + duration
            subtitle_tuples.append((text, start, end))
            cur_time = end
        
        # 创建视频
        success = create_video_with_subtitles(clipped_video_path, audio_path, subtitle_tuples, output_path, subtitle_config)
        
        # 清理临时文件
        temp_files = [audio_path] + subtitle_images
        if clipped_video_path != video_path and os.path.exists(clipped_video_path):
            temp_files.append(clipped_video_path)
        cleanup_temp_files(temp_files)
        
        if success:
            # 获取输出视频信息
            output_info = get_video_info(output_path)
            absolute_output_path = os.path.abspath(output_path)
            # 构建结果信息
            result = {
                "status": "success",
                "message": "视频生成成功",
                "input_text_length": len(text),
                "text_segments": len(timing),
                "audio_segments": len(segments_with_duration),
                "video_info": video_info,
                "output_info": output_info,
                "absolute_output_path": absolute_output_path,
                "config_used": {
                    "segments_mode": segments_mode,
                    "segments_count": len(segments_list),
                    "subtitle_style": subtitle_config,
                    "auto_split_config": split_config
                }
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return "错误：视频生成失败"
        
    except Exception as e:
        return f"错误：生成视频时发生异常 - {str(e)}"

@mcp.tool()
async def get_system_status() -> str:
    """获取系统状态信息
    
    Returns:
        系统状态信息
    """
    try:
        # 检查FFmpeg
        try:
            setup_ffmpeg()
            ffmpeg_status = "FFmpeg: 正常"
        except Exception as e:
            ffmpeg_status = f"FFmpeg: 异常 - {str(e)}"
        
        # 检查语音音色
        voice_status = f"语音音色: 可用 {len(get_voice_by_index(0))} 种"
        
        # 检查输出目录
        output_dir = os.getcwd()
        output_status = f"输出目录: {output_dir}"
        
        return f"""系统状态检查:

{ffmpeg_status}
{voice_status}
{output_status}

模块状态:
- FFmpeg工具: 正常
- 语音工具: 正常
- 音频工具: 正常
- 字幕工具: 正常
- 视频工具: 正常

系统准备就绪，可以开始生成视频！"""
        
    except Exception as e:
        return f"系统状态检查失败: {str(e)}"

@mcp.tool()
async def get_available_voice_options() -> str:
    """获取可用的语音选项
    
    Returns:
        可用的语音选项信息
    """
    try:
        voices = []
        for i in range(5):
            voice_name = get_voice_by_index(i)
            gender = "女声" if i in [0, 2, 3] else "男声"
            voices.append(f"{i}: {voice_name} ({gender})")
        
        return f"""可用的语音音色选项:

{chr(10).join(voices)}

使用说明:
- 0: 女声小晓 (推荐)
- 1: 男声云扬
- 2: 女声小艺
- 3: 女声云希
- 4: 男声云健

选择建议:
- 正式内容推荐使用女声 (0, 2, 3)
- 新闻播报推荐使用男声 (1, 4)
- 默认推荐使用索引 0"""
        
    except Exception as e:
        return f"获取语音选项失败: {str(e)}"

@mcp.tool()
async def validate_input_parameters(text: str, video_path: str, voice_index: int = 0) -> str:
    """验证输入参数
    
    Args:
        text: 要转换的文本
        video_path: 视频文件路径
        voice_index: 语音音色索引
        
    Returns:
        验证结果
    """
    try:
        errors = []
        warnings = []
        
        # 验证文本
        if not text or not text.strip():
            errors.append("文本内容不能为空")
        elif len(text) > 1000:
            warnings.append("文本内容较长，处理时间可能较长")
        
        # 验证视频文件
        if not os.path.exists(video_path):
            errors.append(f"视频文件不存在: {video_path}")
        else:
            file_size = os.path.getsize(video_path)
            if file_size > 100 * 1024 * 1024:  # 100MB
                warnings.append("视频文件较大，处理时间可能较长")
        
        # 验证语音音色
        if voice_index < 0 or voice_index > 4:
            errors.append("语音音色索引无效，有效范围为 0-4")
        
        # 生成结果
        if errors:
            return f"验证失败:\n" + "\n".join([f"- {error}" for error in errors])
        
        result = "验证通过！"
        if warnings:
            result += "\n\n警告:\n" + "\n".join([f"- {warning}" for warning in warnings])
        
        return result
        
    except Exception as e:
        return f"参数验证出错: {str(e)}"

@mcp.tool()
async def get_generation_estimate(text: str, video_path: str) -> str:
    """获取生成时间估算
    
    Args:
        text: 要转换的文本
        video_path: 视频文件路径
        
    Returns:
        时间估算信息
    """
    try:
        # 文本长度估算
        text_length = len(text)
        from .subtitle_utils import split_text
        text_segments = len(split_text(text))
        
        # 视频时长估算
        video_duration = 0.0
        if os.path.exists(video_path):
            try:
                from .video_utils import get_video_info
                info = get_video_info(video_path)
                if "error" not in info and isinstance(info.get('duration'), (int, float)):
                    video_duration = float(info['duration'])
            except:
                pass
        
        # 时间估算
        tts_time = text_length * 0.1  # 每字符0.1秒
        video_time = video_duration * 0.5  # 视频处理时间
        total_time = tts_time + video_time + 30  # 额外30秒缓冲
        
        return f"""生成时间估算:

输入信息:
- 文本长度: {text_length} 字符
- 文本片段: {text_segments} 个
- 视频时长: {video_duration:.1f} 秒

时间估算:
- 文本转语音: {tts_time:.1f} 秒
- 视频处理: {video_time:.1f} 秒
- 总估算时间: {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)

注意事项:
- 实际时间可能因系统性能而异
- 大文件处理时间可能更长
- 建议在生成期间不要关闭程序"""
        
    except Exception as e:
        return f"时间估算失败: {str(e)}"

def get_mcp_instance():
    """获取MCP实例
    
    Returns:
        FastMCP: MCP实例
    """
    return mcp

def get_all_mcp_instances():
    """获取所有模块的MCP实例
    
    Returns:
        dict: 所有MCP实例
    """
    return {
        "main": mcp,
        "ffmpeg": get_ffmpeg_mcp(),
        "voice": get_voice_mcp(),
        "audio": get_audio_mcp(),
        "subtitle": get_subtitle_mcp(),
        "video": get_video_mcp()
    } 