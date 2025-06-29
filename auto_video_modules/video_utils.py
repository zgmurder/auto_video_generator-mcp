"""
视频工具模块
负责视频处理、剪辑、合成和文件管理
"""

import os
import json
import time
import subprocess
import shutil
from tqdm import tqdm
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, ImageClip, TextClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from mcp.server.fastmcp import FastMCP
from PIL import Image, ImageDraw, ImageFont
import tempfile
import numpy as np
import opencc

# 创建MCP实例
mcp = FastMCP("video-utils", log_level="ERROR")

def create_subtitle_image_pil(text, fontsize=40, color='white', font_path=None, size=(1920,1080), bg_color=(0,0,0,0), subtitle_height=100):
    """用PIL生成带透明背景的字幕图片，返回图片路径"""
    # 处理颜色格式
    def parse_color(color_input):
        if isinstance(color_input, str):
            color_map = {
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255),
                'yellow': (255, 255, 0),
                'cyan': (0, 255, 255),
                'magenta': (255, 0, 255),
                'orange': (255, 165, 0),
                'purple': (128, 0, 128),
                'pink': (255, 192, 203),
                'brown': (165, 42, 42),
                'gray': (128, 128, 128),
                'grey': (128, 128, 128)
            }
            return color_map.get(color_input.lower(), (255, 255, 255))
        elif isinstance(color_input, (list, tuple)):
            if len(color_input) == 3:
                return tuple(color_input)
            elif len(color_input) == 4:
                return tuple(color_input)
            else:
                return (255, 255, 255)
        else:
            return (255, 255, 255)
    
    # 解析颜色
    text_color = parse_color(color)
    if isinstance(bg_color, list):
        background_color = tuple(bg_color)
    else:
        background_color = bg_color
    
    # 使用字幕区域高度而不是整个视频高度
    subtitle_size = (size[0], subtitle_height)
    img = Image.new('RGBA', subtitle_size, background_color)
    draw = ImageDraw.Draw(img)
    
    # 字体路径自动检测 - 优先使用支持中文的字体
    if font_path is None or not os.path.exists(font_path):
        # 按优先级排序的中文字体路径
        chinese_fonts = [
            # Windows 中文字体
            r'C:\Windows\Fonts\msyh.ttc',      # 微软雅黑
            r'C:\Windows\Fonts\simhei.ttf',    # 黑体
            r'C:\Windows\Fonts\simsun.ttc',    # 宋体
            r'C:\Windows\Fonts\simkai.ttf',    # 楷体
            r'C:\Windows\Fonts\msjh.ttc',      # 微软正黑
            r'C:\Windows\Fonts\arial.ttf',     # Arial
            # Linux 中文字体
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # 文泉驿正黑
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', # 文泉驿微米黑
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', # Noto Sans CJK
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', # DejaVu Sans
            '/usr/share/fonts/truetype/freefont/FreeMono.ttf', # FreeMono
        ]
        
        for fp in chinese_fonts:
            if os.path.exists(fp):
                font_path = fp
                print(f"自动检测到字体: {font_path}")
                break
        else:
            print("警告: 未找到合适的中文字体，将使用默认字体")
            font_path = None
    
    # 加载字体
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, fontsize)
        else:
            font = ImageFont.load_default()
            print("使用默认字体")
    except Exception as e:
        print(f"字体加载失败: {e}")
        font = ImageFont.load_default()
        print("回退到默认字体")
    
    # 计算文本尺寸
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        # 如果textbbox不存在，使用默认值
        w, h = len(text) * fontsize, fontsize
    
    # 计算文本位置（居中）
    x = (subtitle_size[0] - w) // 2
    y = subtitle_size[1] - h - 60
    
    # 绘制文本
    draw.text((x, y), text, font=font, fill=text_color)
    
    # 保存为临时文件
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(tmp.name, 'PNG')
    
    return tmp.name

def to_seconds(t):
    """将时间字符串转换为秒数
    
    Args:
        t: 时间字符串，格式为 "HH:MM:SS"
        
    Returns:
        float: 秒数，如果输入为None则返回None
    """
    if t is None:
        return None
    h, m, s = map(float, t.split(':'))
    return h*3600 + m*60 + s

def parse_video_segments(segments, video_duration, segments_mode='keep'):
    """解析视频片段配置
    
    Args:
        segments: 片段配置列表
        video_duration: 视频总时长
        segments_mode: 片段模式 ('keep' 或 'cut')
        
    Returns:
        list: 保留的视频区间列表
    """
    if not segments:
        print("segments为空数组，使用全部视频内容")
        return [(0, video_duration)]
    
    # 解析segments区间
    segments_intervals = []
    for seg in segments:
        s = to_seconds(seg['start'])
        e = to_seconds(seg['end'])
        if s is None:
            s = 0
        if e is None:
            e = video_duration
        segments_intervals.append((s, e))
    segments_intervals.sort()
    
    # 根据模式计算最终保留区间
    if segments_mode == 'keep':
        # 保留模式：直接使用segments指定的区间
        keep_intervals = segments_intervals
        print(f"保留模式 - 保留区间: {keep_intervals}")
    elif segments_mode == 'cut':
        # 剪掉模式：计算segments之外的区间
        cut_intervals = segments_intervals
        keep_intervals = []
        last_end = 0
        for s, e in cut_intervals:
            if s > last_end:
                keep_intervals.append((last_end, s))
            last_end = max(last_end, e)
        if last_end < video_duration:
            keep_intervals.append((last_end, video_duration))
        print(f"剪掉模式 - 剪掉区间: {cut_intervals}")
        print(f"剪掉模式 - 保留区间: {keep_intervals}")
    else:
        raise ValueError(f"不支持的segmentsMode: {segments_mode}，支持 'keep' 或 'cut'")
    
    return keep_intervals

def clip_video_segments(video_path, keep_intervals):
    """剪辑视频片段
    
    Args:
        video_path: 视频文件路径
        keep_intervals: 保留区间列表
        
    Returns:
        VideoFileClip: 剪辑后的视频片段
    """
    print("正在加载视频文件...")
    video = VideoFileClip(video_path)
    video_duration = video.duration
    print(f"视频总时长: {video_duration:.2f} 秒")
    
    # 计算预期总时长
    expected_duration = sum(e - s for s, e in keep_intervals)
    print(f"预期保留总时长: {expected_duration:.2f} 秒")
    
    # 剪辑视频片段
    clips = []
    print("正在剪辑保留区间...")
    for s, e in tqdm(keep_intervals, desc="视频剪辑", ascii=True):
        if e - s > 0.05:  # 跳过极短片段
            clips.append(video.subclip(s, e))
    
    if not clips:
        raise ValueError("没有可保留的视频片段，请检查segments配置！")
    
    print("正在合并视频片段...")
    final_clip = concatenate_videoclips(clips)
    print(f"最终视频时长: {final_clip.duration:.2f} 秒")
    
    return final_clip

def find_imagemagick():
    """自动检测ImageMagick可执行文件路径，优先convert.exe"""
    # 优先环境变量
    magick_env = os.environ.get("IMAGEMAGICK_BINARY")
    if magick_env and os.path.isfile(magick_env):
        return magick_env
    # 常见路径，优先convert.exe
    possible_names = ["convert.exe", "magick.exe", "convert", "magick"]
    search_dirs = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        r"C:\ImageMagick",
        r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI",
        r"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI",
        r"/usr/bin",
        r"/usr/local/bin"
    ]
    for d in search_dirs:
        if d and os.path.isdir(d):
            for name in possible_names:
                candidate = os.path.join(d, name)
                if os.path.isfile(candidate):
                    return candidate
    # 系统PATH
    for name in possible_names:
        path = shutil.which(name)
        if path:
            return path
    return None

def merge_audio_video(video_with_subs, audio_file_path, output_path, ffmpeg_path):
    """合并音频和视频
    
    Args:
        video_with_subs: 带字幕的视频
        audio_file_path: 音频文件路径
        output_path: 输出文件路径
        ffmpeg_path: ffmpeg可执行文件路径
    """
    print("正在加载音频文件...")
    audio_clip = AudioFileClip(audio_file_path)
    
    # 检查音频时长，如果超过视频时长则物理截断并保存新文件
    video_duration = video_with_subs.duration
    audio_duration = audio_clip.duration
    print(f"视频时长: {video_duration:.2f} 秒")
    print(f"音频时长: {audio_duration:.2f} 秒")
    
    trimmed_audio_path = None
    if audio_duration > video_duration:
        print(f"音频时长超过视频时长，将音频物理截断并保存为新文件，时长 {video_duration:.2f} 秒")
        trimmed_audio_path = "audio_trimmed.mp3"
        audio_clip.close()
        cmd = [
            ffmpeg_path, "-y",
            "-i", audio_file_path,
            "-ss", "0", "-t", str(video_duration),
            "-c:a", "mp3",
            trimmed_audio_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"音频截断完成，新文件: {trimmed_audio_path}")
        audio_clip = AudioFileClip(trimmed_audio_path)
        print(f"截断后音频时长: {audio_clip.duration:.2f} 秒")
    
    # 生成无音频的视频文件
    temp_video_path = "temp_video.mp4"
    print("正在生成无音频视频...")
    video_with_subs.write_videofile(temp_video_path, codec='libx264', fps=24, audio=False)
    
    # 用ffmpeg合成，确保主轨道为视频，并加-to参数
    print("正在使用ffmpeg合成音视频...")
    audio_file_to_use = trimmed_audio_path if trimmed_audio_path else audio_file_path
    cmd = [
        ffmpeg_path, "-y",
        "-i", temp_video_path,
        "-i", audio_file_to_use,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-to", str(video_duration),
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print('处理完成! 输出文件:', output_path)
    
    return trimmed_audio_path, temp_video_path

def cleanup_temp_files(temp_files):
    """清理临时文件
    
    Args:
        temp_files: 临时文件路径列表
    """
    time.sleep(1)  # 等待文件释放
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f"已删除中间文件 {temp_file}")
            except PermissionError:
                print(f"警告：无法删除 {temp_file}，文件可能被其他程序占用")

def inject_durations_to_timing(timing, durations_file="durations_data.json"):
    """将时长数据注入到timing中
    
    Args:
        timing: 字幕时间列表
        durations_file: 时长数据文件路径
    """
    if os.path.exists(durations_file):
        with open(durations_file, 'r', encoding='utf-8') as f:
            durations = json.load(f)
        for i, d in enumerate(durations):
            if i < len(timing):
                timing[i]['duration'] = d
        print('已注入每条字幕的duration')

async def generate_video(config, timing):
    """生成视频的主函数
    
    Args:
        config: 配置字典
        timing: 字幕时间列表
    """
    from .ffmpeg_utils import check_ffmpeg
    
    video_path = config['video']
    output_path = config['output']
    segments = config.get('segments', [])
    segments_mode = config.get('segmentsMode', 'keep')
    
    # 读取字幕样式配置
    subtitle_style = config.get('subtitleStyle', {})
    
    # 读取智能分割配置
    split_config = config.get('autoSplit', {})
    enable_auto_split = split_config.get('enable', True)
    split_strategy = split_config.get('strategy', 'smart')
    max_chars = split_config.get('maxChars', 20)
    target_duration = split_config.get('targetDuration', 3.0)
    
    # 获取ffmpeg路径
    ffmpeg_path, _ = check_ffmpeg()
    
    # 注入duration
    inject_durations_to_timing(timing)
    
    # 检查音频文件是否存在
    audio_file_path = "audio.mp3"
    if not os.path.exists(audio_file_path):
        print("错误：未检测到 audio.mp3 文件")
        print("请先运行音频合成程序生成音频文件")
        raise FileNotFoundError('未检测到 audio.mp3，请先合成音频')
    
    # 检查源视频文件是否存在
    if not os.path.exists(video_path):
        print(f"错误：找不到源视频文件 '{video_path}'")
        print("请确保：")
        print("1. 视频文件已放置在正确位置")
        print("2. config.json 中的 'video' 字段路径正确")
        print("3. 文件名和扩展名大小写正确")
        raise FileNotFoundError(f"源视频文件不存在: {video_path}")
    
    # 加载视频并获取时长
    video = VideoFileClip(video_path)
    video_duration = video.duration
    video.close()
    
    # 解析视频片段
    keep_intervals = parse_video_segments(segments, video_duration, segments_mode)
    
    # 剪辑视频片段
    final_clip = clip_video_segments(video_path, keep_intervals)
    
    # 智能处理字幕分割
    print("正在处理字幕分割...")
    from .subtitle_utils import split_timings, auto_split_timing_by_duration
    
    if enable_auto_split:
        if split_strategy == 'smart':
            timings = split_timings(timing, max_chars=max_chars)
            print(f"使用智能分割策略，最大字符数: {max_chars}")
        elif split_strategy == 'duration':
            timings = auto_split_timing_by_duration(timing, target_duration)
            print(f"使用时长分割策略，目标时长: {target_duration}秒")
        else:
            timings = timing
            print("禁用自动分割")
    else:
        timings = timing
        print("禁用自动分割")
    
    print(f"原始字幕条数: {len(timing)}, 分割后条数: {len(timings)}")
    
    # 计算每条字幕的出现时间并创建字幕剪辑
    subtitle_clips = []
    cur_time = 0
    print("正在生成字幕图片...")
    
    # 读取字幕样式配置
    font_path = subtitle_style.get('fontPath', './simhei.ttf')
    font_size = subtitle_style.get('fontSize', 40)
    color = subtitle_style.get('color', 'white')
    bg_color = tuple(subtitle_style.get('bgColor', [0,0,0,0]))
    margin_x = subtitle_style.get('marginX', 100)
    margin_bottom = subtitle_style.get('marginBottom', 50)
    subtitle_height = subtitle_style.get('height', 100)
    
    for t in tqdm(timings, desc="字幕生成", ascii=True):
        txt = t['text']
        duration = t.get('duration', 0)
        delay = t.get('delay', 0)
        
        if txt.strip() == "" and (duration > 0 or delay > 0):
            # 推进cur_time，确保后续字幕延后显示
            cur_time += duration + (delay / 1000 if delay > 0 else 0)
            continue
            
        if not txt.strip():
            continue
            
        # 使用PIL生成字幕图片
        img_path = create_subtitle_image_pil(
            txt, 
            fontsize=font_size, 
            color=color, 
            font_path=font_path,
            size=(final_clip.w, subtitle_height),
            bg_color=bg_color
        )
        
        img_clip = (ImageClip(img_path)
                    .set_position(('center', 'bottom'))
                    .set_start(cur_time)
                    .set_end(cur_time + duration))
        subtitle_clips.append(img_clip)
        cur_time += duration
    
    # 合成视频和字幕
    print("正在合成视频和字幕...")
    video_with_subs = CompositeVideoClip([final_clip] + subtitle_clips)
    
    # 使用原始视频时长作为基准
    original_video_duration = video.duration
    audio_duration = audio_clip.duration
    print(f"原始视频时长: {original_video_duration:.2f} 秒")
    print(f"音频时长: {audio_duration:.2f} 秒")
    
    trimmed_audio_path = None
    if audio_duration > original_video_duration:
        print(f"音频时长超过视频时长，将音频物理截断并保存为新文件，时长 {original_video_duration:.2f} 秒")
        trimmed_audio_path = "audio_trimmed.mp3"
        audio_clip.close()
        cmd = [
            ffmpeg_path, "-y",
            "-i", audio_file_path,
            "-ss", "0", "-t", str(original_video_duration),
            "-c:a", "mp3",
            trimmed_audio_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"音频截断完成，新文件: {trimmed_audio_path}")
        audio_clip = AudioFileClip(trimmed_audio_path)
        print(f"截断后音频时长: {audio_clip.duration:.2f} 秒")
    
    # 生成无音频的视频文件
    temp_video_path = "temp_video.mp4"
    print("正在生成无音频视频...")
    video_with_subs.write_videofile(temp_video_path, codec='libx264', fps=24, audio=False)
    
    # 用ffmpeg合成，确保主轨道为视频，并加-to参数
    print("正在使用ffmpeg合成音视频...")
    audio_file_to_use = trimmed_audio_path if trimmed_audio_path else audio_file_path
    cmd = [
        ffmpeg_path, "-y",
        "-i", temp_video_path,
        "-i", audio_file_to_use,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-to", str(original_video_duration),
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print('处理完成! 输出文件:', output_path)
    
    # 清理临时文件
    temp_files = [temp_video_path, "audio.mp3", "durations_data.json"]
    if trimmed_audio_path:
        temp_files.append(trimmed_audio_path)
    cleanup_temp_files(temp_files) 

def validate_video_file(video_path):
    """验证视频文件是否存在且有效
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        bool: 文件是否有效
    """
    if not os.path.exists(video_path):
        return False
    
    try:
        clip = VideoFileClip(video_path)
        clip.close()
        return True
    except Exception:
        return False

def get_video_info(video_path):
    """获取视频文件信息
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        dict: 视频文件信息
    """
    try:
        clip = VideoFileClip(video_path)
        info = {
            "duration": clip.duration,
            "fps": clip.fps,
            "size": clip.size,
            "file_size": os.path.getsize(video_path)
        }
        clip.close()
        return info
    except Exception as e:
        return {"error": str(e)}

def create_video_with_subtitles(video_path, audio_path, subtitle_segments, output_path, subtitle_style=None):
    """用PIL字幕图片合成带字幕视频"""
    try:
        # 加载视频和音频
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        # 导入配置管理器
        from .config import get_config
        config = get_config()
        subtitle_config = config.get_subtitle_config()
        
        # 解析字幕样式配置，使用配置中的默认值
        if subtitle_style is None:
            subtitle_style = {}
        
        font_size = subtitle_style.get('fontSize', subtitle_config.font_size)
        color = subtitle_style.get('color', subtitle_config.font_color)
        bg_color = subtitle_style.get('bgColor', subtitle_config.bg_color)
        font_path = subtitle_style.get('fontPath', subtitle_config.font_path)
        margin_x = subtitle_style.get('marginX', subtitle_config.margin_x)
        margin_bottom = subtitle_style.get('marginBottom', subtitle_config.margin_bottom)
        subtitle_height = subtitle_style.get('height', 100)
        
        # 创建字幕剪辑（PIL图片）
        subtitle_clips = []
        for i, (text, start_time, end_time) in enumerate(subtitle_segments):
            img_path = create_subtitle_image_pil(
                text, 
                fontsize=font_size, 
                color=color, 
                font_path=font_path,
                size=(video.w, video.h),
                bg_color=bg_color,
                subtitle_height=subtitle_height
            )
            img_clip = ImageClip(img_path).set_position(('center', 'bottom')).set_duration(end_time - start_time).set_start(start_time)
            subtitle_clips.append(img_clip)
        
        # 合成视频和字幕
        print("正在合成视频和字幕...")
        video_with_subs = CompositeVideoClip([video] + subtitle_clips)
        
        # 使用原始视频时长作为基准
        original_video_duration = video.duration
        audio_duration = audio.duration
        print(f"原始视频时长: {original_video_duration:.2f} 秒")
        print(f"音频时长: {audio_duration:.2f} 秒")
        
        trimmed_audio_path = None
        if audio_duration > original_video_duration:
            print(f"音频时长超过视频时长，将音频物理截断并保存为新文件，时长 {original_video_duration:.2f} 秒")
            trimmed_audio_path = "audio_trimmed.mp3"
            audio.close()
            from .ffmpeg_utils import check_ffmpeg
            ffmpeg_path, _ = check_ffmpeg()
            cmd = [
                ffmpeg_path, "-y",
                "-i", audio_path,
                "-ss", "0", "-t", str(original_video_duration),
                "-c:a", "mp3",
                trimmed_audio_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"音频截断完成，新文件: {trimmed_audio_path}")
            audio = AudioFileClip(trimmed_audio_path)
            print(f"截断后音频时长: {audio.duration:.2f} 秒")
        
        # 生成无音频的视频文件
        temp_video_path = "temp_video.mp4"
        print("正在生成无音频视频...")
        video_with_subs.write_videofile(temp_video_path, codec='libx264', fps=24, audio=False)
        
        # 用ffmpeg合成，确保主轨道为视频，并加-to参数
        print("正在使用ffmpeg合成音视频...")
        from .ffmpeg_utils import check_ffmpeg
        ffmpeg_path, _ = check_ffmpeg()
        audio_file_to_use = trimmed_audio_path if trimmed_audio_path else audio_path
        cmd = [
            ffmpeg_path, "-y",
            "-i", temp_video_path,
            "-i", audio_file_to_use,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-to", str(original_video_duration),
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print('处理完成! 输出文件:', output_path)
        
        # 清理资源
        video.close()
        audio.close()
        video_with_subs.close()
        
        # 清理临时文件
        temp_files = [temp_video_path]
        if trimmed_audio_path:
            temp_files.append(trimmed_audio_path)
        cleanup_temp_files(temp_files)
        
        print(f"视频生成成功: {output_path}")
        return True
    except Exception as e:
        print(f"视频生成失败: {e}")
        return False

def trim_video(video_path, start_time, end_time, output_path):
    """裁剪视频
    
    Args:
        video_path: 输入视频路径
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        output_path: 输出视频路径
        
    Returns:
        bool: 是否成功
    """
    try:
        video = VideoFileClip(video_path)
        trimmed_video = video.subclip(start_time, end_time)
        trimmed_video.write_videofile(output_path, codec='libx264')
        
        video.close()
        trimmed_video.close()
        
        print(f"视频裁剪成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"视频裁剪失败: {e}")
        return False

def merge_videos(video_paths, output_path):
    """合并多个视频
    
    Args:
        video_paths: 视频文件路径列表
        output_path: 输出视频路径
        
    Returns:
        bool: 是否成功
    """
    try:
        clips = []
        for path in video_paths:
            if validate_video_file(path):
                clip = VideoFileClip(path)
                clips.append(clip)
            else:
                print(f"警告：视频文件无效: {path}")
        
        if not clips:
            print("错误：没有有效的视频文件")
            return False
        
        # 合并视频
        final_clip = clips[0]
        for clip in clips[1:]:
            final_clip = final_clip.concatenate_videoclips([final_clip, clip])
        
        final_clip.write_videofile(output_path, codec='libx264')
        
        # 清理资源
        for clip in clips:
            clip.close()
        final_clip.close()
        
        print(f"视频合并成功: {output_path}")
        return True
        
    except Exception as e:
        print(f"视频合并失败: {e}")
        return False

@mcp.tool()
async def validate_video_file_tool(video_path: str) -> str:
    """验证视频文件
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        验证结果
    """
    try:
        if validate_video_file(video_path):
            info = get_video_info(video_path)
            if "error" not in info:
                return f"""视频文件验证通过

文件信息:
路径: {video_path}
时长: {info['duration']:.2f}秒
帧率: {info['fps']} fps
分辨率: {info['size'][0]}x{info['size'][1]}
文件大小: {info['file_size']} 字节"""
            else:
                return f"视频文件存在但无法读取: {info['error']}"
        else:
            return f"视频文件无效或不存在: {video_path}"
    except Exception as e:
        return f"视频文件验证出错: {str(e)}"

@mcp.tool()
async def get_video_info_tool(video_path: str) -> str:
    """获取视频文件信息
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        视频文件信息
    """
    try:
        if not os.path.exists(video_path):
            return f"错误：视频文件不存在: {video_path}"
        
        info = get_video_info(video_path)
        if "error" in info:
            return f"获取视频信息失败: {info['error']}"
        
        return f"""视频文件信息:

基本信息:
- 文件路径: {video_path}
- 时长: {info['duration']:.2f}秒
- 帧率: {info['fps']} fps
- 分辨率: {info['size'][0]}x{info['size'][1]}
- 文件大小: {info['file_size']} 字节

计算信息:
- 总帧数: {int(info['duration'] * info['fps'])}
- 宽高比: {info['size'][0] / info['size'][1]:.2f}
- 平均码率: {info['file_size'] / info['duration'] / 1024:.2f} KB/s"""
    except Exception as e:
        return f"获取视频信息失败: {str(e)}"

@mcp.tool()
async def trim_video_tool(video_path: str, start_time: float, end_time: float, output_path: str) -> str:
    """裁剪视频
    
    Args:
        video_path: 输入视频路径
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        output_path: 输出视频路径
        
    Returns:
        裁剪结果
    """
    try:
        if not validate_video_file(video_path):
            return f"错误：输入视频文件无效: {video_path}"
        
        if start_time < 0 or end_time <= start_time:
            return "错误：时间参数无效，start_time应大于等于0，end_time应大于start_time"
        
        success = trim_video(video_path, start_time, end_time, output_path)
        if success:
            return f"视频裁剪成功\n输出文件: {output_path}\n裁剪时间: {start_time:.2f}s - {end_time:.2f}s"
        else:
            return "视频裁剪失败"
    except Exception as e:
        return f"视频裁剪出错: {str(e)}"

@mcp.tool()
async def merge_videos_tool(video_paths: str, output_path: str) -> str:
    """合并多个视频
    
    Args:
        video_paths: 视频文件路径，用逗号分隔
        output_path: 输出视频路径
        
    Returns:
        合并结果
    """
    try:
        paths = [path.strip() for path in video_paths.split(',')]
        
        # 验证所有视频文件
        valid_paths = []
        for path in paths:
            if validate_video_file(path):
                valid_paths.append(path)
            else:
                print(f"警告：跳过无效视频文件: {path}")
        
        if not valid_paths:
            return "错误：没有有效的视频文件"
        
        success = merge_videos(valid_paths, output_path)
        if success:
            return f"视频合并成功\n输出文件: {output_path}\n合并了 {len(valid_paths)} 个视频文件"
        else:
            return "视频合并失败"
    except Exception as e:
        return f"视频合并出错: {str(e)}"

@mcp.tool()
async def create_video_with_subtitles_tool(video_path: str, audio_path: str, subtitle_segments: str, output_path: str) -> str:
    """创建带字幕的视频
    
    Args:
        video_path: 视频文件路径
        audio_path: 音频文件路径
        subtitle_segments: 字幕片段，格式：文本,开始时间,结束时间;文本,开始时间,结束时间
        output_path: 输出视频文件路径
        
    Returns:
        创建结果
    """
    try:
        if not validate_video_file(video_path):
            return f"错误：视频文件无效: {video_path}"
        
        if not os.path.exists(audio_path):
            return f"错误：音频文件不存在: {audio_path}"
        
        # 解析字幕片段
        segments = []
        for segment_str in subtitle_segments.split(';'):
            if segment_str.strip():
                parts = segment_str.split(',')
                if len(parts) == 3:
                    text, start_time, end_time = parts
                    segments.append((text.strip(), float(start_time), float(end_time)))
        
        if not segments:
            return "错误：没有有效的字幕片段"
        
        success = create_video_with_subtitles(video_path, audio_path, segments, output_path)
        if success:
            return f"带字幕视频创建成功\n输出文件: {output_path}\n字幕片段数: {len(segments)}"
        else:
            return "带字幕视频创建失败"
    except Exception as e:
        return f"创建带字幕视频出错: {str(e)}"

@mcp.tool()
async def get_video_formats() -> str:
    """获取支持的视频格式
    
    Returns:
        支持的视频格式列表
    """
    return """支持的视频格式:

输入格式:
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- WMV (.wmv)
- FLV (.flv)
- WebM (.webm)

输出格式:
- MP4 (.mp4) - 推荐，兼容性好
- AVI (.avi) - 通用格式
- MOV (.mov) - Apple设备友好

编解码器:
- 视频: H.264 (libx264)
- 音频: AAC (aac)

注意事项:
- 确保系统已安装FFmpeg
- 输出MP4格式兼容性最好
- 大文件处理可能需要较长时间"""

def get_mcp_instance():
    """获取MCP实例
    
    Returns:
        FastMCP: MCP实例
    """
    return mcp 