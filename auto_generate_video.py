import json
import asyncio
import edge_tts
from moviepy.audio.io.AudioFileClip import AudioFileClip
import subprocess
import sys
import os
from tqdm import tqdm
import time
import argparse

def resource_path(relative_path):
    # 兼容 PyInstaller 打包和源码运行
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# 将 ffmpeg/bin 加入 PATH，确保 pydub 子进程能找到 ffmpeg/ffprobe/ffplay
ffmpeg_dir = resource_path("ffmpeg/bin")
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# ffmpeg 路径
ffmpeg_path = resource_path("ffmpeg/bin/ffmpeg.exe")
ffprobe_path = resource_path("ffmpeg/bin/ffprobe.exe")


# 设置 pydub 的 ffmpeg 路径
from pydub import AudioSegment
AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

ffplay_path = resource_path("ffmpeg/bin/ffplay.exe")
from pydub import AudioSegment
AudioSegment.ffplay = ffplay_path

import moviepy
from moviepy.config import change_settings
change_settings({"FFMPEG_BINARY": ffmpeg_path})

def get_voice_by_index(idx):
    voices = [
        "zh-CN-XiaoxiaoNeural",  # 0 女
        "zh-CN-YunyangNeural",   # 1 男
        "zh-CN-XiaoyiNeural",    # 2 女
        "zh-CN-YunxiNeural",     # 3 女
        "zh-CN-YunjianNeural"    # 4 男
    ]
    if idx < 0 or idx >= len(voices):
        print(f"activeTimbre超出范围，使用默认音色: {voices[0]}")
        return voices[0]
    return voices[idx]

async def synthesize_and_get_durations(timing, voice):
    from pydub import AudioSegment
    audio_segments = []
    durations = []
    for idx, t in enumerate(tqdm(timing, desc="合成音频", ascii=True)):
        text = t['text']
        delay = t.get('delay', 0)
        if text.strip() == "" and delay > 0:
            silence = AudioSegment.silent(duration=delay)
            temp_audio = f"_temp_silence_{idx}.mp3"
            silence.export(temp_audio, format="mp3")
            audio_segments.append(temp_audio)
            durations.append(delay / 1000)
            tqdm.write(f"第{idx+1}条：空白静默 {delay}ms")
            continue
        temp_audio = f"_temp_{idx}.mp3"
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(temp_audio)
        tts_audio = AudioSegment.from_file(temp_audio, format="mp3")
        audio_segments.append(temp_audio)
        durations.append(tts_audio.duration_seconds)
    # 合并所有音频片段
    combined = AudioSegment.empty()
    for seg in audio_segments:
        combined += AudioSegment.from_file(seg)
    audio_mp3_path = resource_path("audio.mp3")
    combined.export(audio_mp3_path, format="mp3")
    for seg in audio_segments:
        os.remove(seg)
    print("已合成音频 audio.mp3，并自动获取每条字幕的朗读时长（未写回config.json）")
    # 保存 durations.json
    with open('durations_data.json', 'w', encoding='utf-8') as f:
        json.dump(durations, f)
    print("已生成 durations_data.json 文件")
    return durations

# ========== 视频生成逻辑合并 ===========
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import opencc

def create_subtitle_image(text, width, height, font_path, fontsize=40, color='black', bg_color=(0,0,0,0), margin_x=100, margin_bottom=50):
    # 繁体转简体
    converter = opencc.OpenCC('t2s')
    text = converter.convert(text)
    img = Image.new('RGBA', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, fontsize)
    max_text_width = width - 2 * margin_x
    avg_char_width = font.getlength('测')
    max_chars_per_line = max(int(max_text_width // avg_char_width), 1)
    # 只取第一行，超长截断
    if len(text) > max_chars_per_line:
        text = text[:max_chars_per_line] + '...'
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - w) // 2
    y = height - h - margin_bottom
    draw.text((x, y), text, font=font, fill=color)
    return np.array(img)

def split_timings(timing, max_chars=20):
    """
    智能分割timing，支持多种分割策略：
    1. 按句子分割（句号、问号、感叹号）
    2. 按逗号分割
    3. 按字符数分割
    4. 智能时长分配
    """
    new_timings = []
    
    for t in timing:
        txt = t['text'].strip()
        duration = t.get('duration', 0)
        delay = t.get('delay', 0)
        
        # 处理空白静默
        if txt == "" and (delay > 0 or duration > 0):
            new_timings.append({'text': txt, 'duration': duration, 'delay': delay})
            continue
            
        # 如果文本为空，跳过
        if not txt:
            continue
            
        # 策略1：按句子分割（句号、问号、感叹号）
        sentences = []
        current_sentence = ""
        for char in txt:
            current_sentence += char
            if char in '。？！.!?':
                sentences.append(current_sentence.strip())
                current_sentence = ""
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
            
        # 如果按句子分割后只有一句，尝试按逗号分割
        if len(sentences) <= 1:
            sentences = []
            current_sentence = ""
            for char in txt:
                current_sentence += char
                if char in '，,；;':
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
            if current_sentence.strip():
                sentences.append(current_sentence.strip())
                
        # 如果按逗号分割后只有一句，按字符数分割
        if len(sentences) <= 1:
            sentences = [txt[i:i+max_chars] for i in range(0, len(txt), max_chars)]
            
        # 智能时长分配
        if len(sentences) == 1:
            new_timings.append({'text': txt, 'duration': duration, 'delay': delay})
        else:
            # 根据句子长度比例分配时长
            total_chars = sum(len(s) for s in sentences)
            for sentence in sentences:
                if total_chars > 0:
                    sentence_duration = (len(sentence) / total_chars) * duration
                else:
                    sentence_duration = duration / len(sentences)
                new_timings.append({
                    'text': sentence, 
                    'duration': sentence_duration,
                    'delay': 0  # 子句不设置delay
                })
    
    return new_timings

def auto_split_timing_by_duration(timing, target_duration_per_segment=3.0):
    """
    根据目标时长自动分割timing
    target_duration_per_segment: 每个片段的目标时长（秒）
    """
    new_timings = []
    current_segment = []
    current_duration = 0
    
    for t in timing:
        txt = t['text'].strip()
        duration = t.get('duration', 0)
        delay = t.get('delay', 0)
        
        # 处理空白静默
        if txt == "" and (delay > 0 or duration > 0):
            # 如果当前片段不为空，先保存当前片段
            if current_segment:
                new_timings.append({
                    'text': ' '.join([item['text'] for item in current_segment]),
                    'duration': current_duration,
                    'delay': 0
                })
                current_segment = []
                current_duration = 0
            # 添加静默
            new_timings.append({'text': txt, 'duration': duration, 'delay': delay})
            continue
            
        # 如果文本为空，跳过
        if not txt:
            continue
            
        # 检查是否需要开始新片段
        if current_duration + duration > target_duration_per_segment and current_segment:
            # 保存当前片段
            new_timings.append({
                'text': ' '.join([item['text'] for item in current_segment]),
                'duration': current_duration,
                'delay': 0
            })
            current_segment = []
            current_duration = 0
            
        # 添加到当前片段
        current_segment.append({'text': txt, 'duration': duration})
        current_duration += duration
    
    # 保存最后一个片段
    if current_segment:
        new_timings.append({
            'text': ' '.join([item['text'] for item in current_segment]),
            'duration': current_duration,
            'delay': 0
        })
    
    return new_timings

def to_seconds(t):
    if t is None:
        return None
    h, m, s = map(float, t.split(':'))
    return h*3600 + m*60 + s

def generate_video(config, timing):
    video_path = config['video']
    output_path = config['output']
    segments = config['segments']
    segments_mode = config.get('segmentsMode', 'keep')  # 'keep' 或 'cut'
    
    # 读取字幕样式配置
    style = config.get('subtitleStyle', {})
    font_path = style.get('fontPath', './simhei.ttf')
    font_size = style.get('fontSize', 40)
    color = style.get('color', 'white')
    bg_color = tuple(style.get('bgColor', [0,0,0,0]))
    margin_x = style.get('marginX', 100)
    margin_bottom = style.get('marginBottom', 50)
    subtitle_height = style.get('height', 100)
    
    # 读取智能分割配置
    split_config = config.get('autoSplit', {})
    enable_auto_split = split_config.get('enable', True)
    split_strategy = split_config.get('strategy', 'smart')  # 'smart', 'duration', 'none'
    max_chars = split_config.get('maxChars', 20)
    target_duration = split_config.get('targetDuration', 3.0)

    # 注入duration
    if os.path.exists('durations_data.json'):
        with open('durations_data.json', 'r', encoding='utf-8') as f:
            durations = json.load(f)
        for i, d in enumerate(durations):
            if i < len(timing):
                timing[i]['duration'] = d
        print('已注入每条字幕的duration')

    # 检查音频文件是否存在
    audio_file_path = resource_path("audio.mp3")
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

    # 加载视频，获取总时长
    print("正在加载视频文件...")
    video = VideoFileClip(video_path)
    video_duration = video.duration
    print(f"视频总时长: {video_duration:.2f} 秒")

    # 检查segments是否为空数组
    if not segments:
        print("segments为空数组，使用全部视频内容")
        keep_intervals = [(0, video_duration)]
        print(f"使用全部视频区间: (0, {video_duration:.2f})")
    else:
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

    # 智能处理字幕分割
    print("正在处理字幕分割...")
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
    
    # 计算每条字幕的出现时间
    subtitle_clips = []
    cur_time = 0
    print("正在生成字幕图片...")
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
            
        img_arr = create_subtitle_image(txt, final_clip.w, subtitle_height, font_path, fontsize=font_size, color=color, bg_color=bg_color, margin_x=margin_x, margin_bottom=margin_bottom)
        img_clip = (ImageClip(img_arr)
                    .set_position(('center', 'bottom'))
                    .set_start(cur_time)
                    .set_end(cur_time + duration))
        subtitle_clips.append(img_clip)
        cur_time += duration

    # 合成视频和字幕
    print("正在合成视频和字幕...")
    video_with_subs = CompositeVideoClip([final_clip, *subtitle_clips])
    # 设置音频为 audio.mp3
    print("正在加载音频文件...")
    audio_clip = AudioFileClip(audio_file_path)
    
    # 检查音频时长，如果超过视频时长则物理截断并保存新文件
    video_duration = final_clip.duration
    audio_duration = audio_clip.duration
    print(f"视频时长: {video_duration:.2f} 秒")
    print(f"音频时长: {audio_duration:.2f} 秒")
    trimmed_audio_path = None
    if audio_duration > video_duration:
        print(f"音频时长超过视频时长，将音频物理截断并保存为新文件，时长 {video_duration:.2f} 秒")
        trimmed_audio_path = "audio_trimmed.mp3"
        audio_clip.close()
        import subprocess
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
        "-shortest",
        "-to", str(video_duration),
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print('处理完成! 输出文件:', output_path)
    
    # 清理中间文件
    import time
    time.sleep(1)  # 等待文件释放
    for temp_file in [temp_video_path, "audio.mp3", "durations_data.json"]:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f"已删除中间文件 {temp_file}")
            except PermissionError:
                print(f"警告：无法删除 {temp_file}，文件可能被其他程序占用")
    if trimmed_audio_path and os.path.exists(trimmed_audio_path):
        try:
            os.remove(trimmed_audio_path)
            print("已删除中间文件 audio_trimmed.mp3")
        except PermissionError:
            print("警告：无法删除 audio_trimmed.mp3，文件可能被其他程序占用")

# ========== 主流程入口 ===========
if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='自动生成带字幕视频工具')
    parser.add_argument('--video', '-v', help='输入视频文件名')
    parser.add_argument('--output', '-o', help='输出视频文件名')
    parser.add_argument('--timbre', '-t', type=int, choices=[0,1,2,3,4], help='语音音色 (0:女声小晓, 1:男声云扬, 2:女声小艺, 3:女声云希, 4:男声云健)')
    parser.add_argument('--font-size', type=int, help='字幕字体大小')
    parser.add_argument('--font-color', help='字幕字体颜色 (white/black/red/yellow等)')
    parser.add_argument('--bg-color', help='字幕背景颜色 (格式: R,G,B,A 例如: 0,0,0,128)')
    parser.add_argument('--margin-x', type=int, help='字幕左右边距')
    parser.add_argument('--margin-bottom', type=int, help='字幕底部边距')
    parser.add_argument('--subtitle-height', type=int, help='字幕区域高度')
    parser.add_argument('--auto-split', choices=['enable', 'disable'], help='是否启用智能分割')
    parser.add_argument('--split-strategy', choices=['smart', 'duration', 'none'], help='分割策略')
    parser.add_argument('--max-chars', type=int, help='每行最大字符数')
    parser.add_argument('--target-duration', type=float, help='目标时长(秒)')
    parser.add_argument('--segments-mode', choices=['keep', 'cut'], help='视频片段模式')
    parser.add_argument('--use-full-video', action='store_true', help='使用全部视频内容(设置segments为空)')
    parser.add_argument('--config', '-c', default='config.json', help='配置文件路径 (默认: config.json)')
    
    args = parser.parse_args()
    
    # 加载配置文件
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到配置文件 '{args.config}'")
        print("请确保配置文件存在，或使用 --config 参数指定正确的配置文件路径")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误：配置文件 '{args.config}' 格式不正确")
        print(f"JSON解析错误: {e}")
        sys.exit(1)
    
    # 使用命令行参数覆盖配置文件
    if args.video:
        config['video'] = args.video
        print(f"使用命令行参数设置视频文件: {args.video}")
    
    if args.output:
        config['output'] = args.output
        print(f"使用命令行参数设置输出文件: {args.output}")
    
    if args.timbre is not None:
        config['activeTimbre'] = args.timbre
        print(f"使用命令行参数设置语音音色: {args.timbre}")
    
    if args.use_full_video:
        config['segments'] = []
        print("使用命令行参数设置：使用全部视频内容")
    
    if args.segments_mode:
        config['segmentsMode'] = args.segments_mode
        print(f"使用命令行参数设置视频片段模式: {args.segments_mode}")
    
    # 覆盖字幕样式设置
    if any([args.font_size, args.font_color, args.bg_color, args.margin_x, args.margin_bottom, args.subtitle_height]):
        if 'subtitleStyle' not in config:
            config['subtitleStyle'] = {}
        
        if args.font_size:
            config['subtitleStyle']['fontSize'] = args.font_size
            print(f"使用命令行参数设置字体大小: {args.font_size}")
        
        if args.font_color:
            config['subtitleStyle']['color'] = args.font_color
            print(f"使用命令行参数设置字体颜色: {args.font_color}")
        
        if args.bg_color:
            try:
                bg_color = [int(x.strip()) for x in args.bg_color.split(',')]
                config['subtitleStyle']['bgColor'] = bg_color
                print(f"使用命令行参数设置背景颜色: {bg_color}")
            except ValueError:
                print(f"警告：背景颜色格式错误 '{args.bg_color}'，应为 R,G,B,A 格式")
        
        if args.margin_x:
            config['subtitleStyle']['marginX'] = args.margin_x
            print(f"使用命令行参数设置左右边距: {args.margin_x}")
        
        if args.margin_bottom:
            config['subtitleStyle']['marginBottom'] = args.margin_bottom
            print(f"使用命令行参数设置底部边距: {args.margin_bottom}")
        
        if args.subtitle_height:
            config['subtitleStyle']['height'] = args.subtitle_height
            print(f"使用命令行参数设置字幕区域高度: {args.subtitle_height}")
    
    # 覆盖智能分割设置
    if any([args.auto_split, args.split_strategy, args.max_chars, args.target_duration]):
        if 'autoSplit' not in config:
            config['autoSplit'] = {}
        
        if args.auto_split:
            config['autoSplit']['enable'] = (args.auto_split == 'enable')
            print(f"使用命令行参数设置智能分割: {'启用' if args.auto_split == 'enable' else '禁用'}")
        
        if args.split_strategy:
            config['autoSplit']['strategy'] = args.split_strategy
            print(f"使用命令行参数设置分割策略: {args.split_strategy}")
        
        if args.max_chars:
            config['autoSplit']['maxChars'] = args.max_chars
            print(f"使用命令行参数设置最大字符数: {args.max_chars}")
        
        if args.target_duration:
            config['autoSplit']['targetDuration'] = args.target_duration
            print(f"使用命令行参数设置目标时长: {args.target_duration}秒")
    
    # 检查必要的配置项
    if 'video' not in config:
        print("错误：配置文件中缺少 'video' 字段")
        print("请在配置文件中设置视频文件名，或使用 --video 参数指定")
        sys.exit(1)
    
    if 'timing' not in config:
        print("错误：配置文件中缺少 'timing' 字段")
        print("请在配置文件中设置字幕内容")
        sys.exit(1)
    
    # 设置默认值
    if 'output' not in config:
        config['output'] = 'output1.mp4'
    
    if 'activeTimbre' not in config:
        config['activeTimbre'] = 0
    
    print(f"\n=== 配置信息 ===")
    print(f"输入视频: {config['video']}")
    print(f"输出视频: {config['output']}")
    print(f"语音音色: {config['activeTimbre']}")
    print(f"字幕条数: {len(config['timing'])}")
    print(f"视频片段: {'使用全部视频' if not config.get('segments') else f'{len(config.get('segments', []))}个片段'}")
    print("=" * 20 + "\n")
    
    # 安装依赖
    import importlib.util
    if importlib.util.find_spec('pydub') is None:
        print('正在安装pydub...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pydub'])
    
    # 执行主流程
    active_timbre = config.get('activeTimbre', 0)
    timing = config['timing']
    voice = get_voice_by_index(active_timbre)
    
    # 合成音频并获取每条字幕的朗读时长
    durations = asyncio.run(synthesize_and_get_durations(timing, voice))
    
    # 直接调用视频生成逻辑
    generate_video(config, timing)
    print("全部流程已完成，只保留最终视频！")