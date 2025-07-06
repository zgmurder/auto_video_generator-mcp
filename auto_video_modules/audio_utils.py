"""
音频工具模块
负责TTS合成、音频处理和时长计算
"""

import json
import os
import edge_tts
from tqdm import tqdm
from pydub import AudioSegment
from mcp.server.fastmcp import FastMCP
import asyncio

# 创建MCP实例
mcp = FastMCP("audio-utils", log_level="ERROR")

async def synthesize_and_get_durations(timing, voice):
    """异步合成音频并获取每条字幕的朗读时长（主流程必须 await）"""
    audio_segments = []
    durations = []
    segments = []
    
    for idx, t in enumerate(tqdm(timing, desc="合成音频", ascii=True)):
        text = t['text']
        delay = t.get('delay', 0)
        
        if text.strip() == "" and delay > 0:
            # 处理空白静默
            silence = AudioSegment.silent(duration=delay)
            temp_audio = f"_temp_silence_{idx}.mp3"
            silence.export(temp_audio, format="mp3")
            audio_segments.append(temp_audio)
            durations.append(delay / 1000)
            segments.append({"text": text, "duration": delay / 1000, "delay": delay})
            tqdm.write(f"第{idx+1}条：空白静默 {delay}ms")
            continue
        
        # 合成TTS音频
        temp_audio = f"_temp_{idx}.mp3"
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(temp_audio)
        
        # 获取音频时长
        tts_audio = AudioSegment.from_file(temp_audio, format="mp3")
        audio_segments.append(temp_audio)
        durations.append(tts_audio.duration_seconds)
        segments.append({"text": text, "duration": tts_audio.duration_seconds})
    
    # 合并所有音频片段
    combined = AudioSegment.empty()
    for seg in audio_segments:
        combined += AudioSegment.from_file(seg)
    
    # 导出合并后的音频
    audio_mp3_path = "audio.mp3"
    combined.export(audio_mp3_path, format="mp3")
    
    # 清理临时文件
    for seg in audio_segments:
        os.remove(seg)
    
    print("已合成音频 audio.mp3，并自动获取每条字幕的朗读时长")
    
    # 保存时长数据
    with open('durations_data.json', 'w', encoding='utf-8') as f:
        json.dump(durations, f)
    print("已生成 durations_data.json 文件")
    
    return {"audio_path": audio_mp3_path, "segments": segments}

async def synthesize_text_to_audio(text, voice, output_path="temp_audio.mp3"):
    """异步将单个文本合成音频"""
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)
    
    # 获取音频时长
    audio = AudioSegment.from_file(output_path, format="mp3")
    return audio.duration_seconds

def load_durations_from_file(file_path="durations_data.json"):
    """从文件加载时长数据
    
    Args:
        file_path: 时长数据文件路径
        
    Returns:
        list: 时长数据列表，如果文件不存在返回None
    """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_durations_to_file(durations, file_path="durations_data.json"):
    """保存时长数据到文件
    
    Args:
        durations: 时长数据列表
        file_path: 保存文件路径
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(durations, f)

def create_silence_audio(duration_ms, output_path="silence.mp3"):
    """创建静默音频
    
    Args:
        duration_ms: 静默时长（毫秒）
        output_path: 输出文件路径
        
    Returns:
        str: 输出文件路径
    """
    silence = AudioSegment.silent(duration=duration_ms)
    silence.export(output_path, format="mp3")
    return output_path

async def text_to_speech(text, voice, output_file):
    """异步将文本转换为语音"""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        print(f"音频生成成功: {output_file}")
        return True
    except Exception as e:
        print(f"音频生成失败: {e}")
        return False

def get_audio_duration(audio_file):
    """获取音频文件时长
    
    Args:
        audio_file: 音频文件路径
        
    Returns:
        float: 音频时长（秒）
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_file)
        return len(audio) / 1000.0  # 转换为秒
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return 0.0

def validate_audio_file(audio_file):
    """验证音频文件是否存在且有效
    
    Args:
        audio_file: 音频文件路径
        
    Returns:
        bool: 文件是否有效
    """
    if not os.path.exists(audio_file):
        return False
    
    try:
        from pydub import AudioSegment
        AudioSegment.from_file(audio_file)
        return True
    except Exception:
        return False

def get_audio_info(audio_file):
    """获取音频文件信息
    
    Args:
        audio_file: 音频文件路径
        
    Returns:
        dict: 音频文件信息
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_file)
        
        info = {
            "file_path": audio_file,
            "duration_seconds": len(audio) / 1000.0,
            "sample_rate": audio.frame_rate,
            "channels": audio.channels,
            "frame_width": audio.frame_width,
            "file_size_mb": os.path.getsize(audio_file) / (1024 * 1024)
        }
        
        return info
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def convert_text_to_speech(text: str, voice: str, output_file: str) -> str:
    """将文本转换为语音文件
    
    Args:
        text: 要转换的文本
        voice: 语音音色名称
        output_file: 输出音频文件路径
        
    Returns:
        转换结果信息
    """
    try:
        success = text_to_speech(text, voice, output_file)
        if success:
            duration = get_audio_duration(output_file)
            return f"文本转语音成功！输出文件: {output_file}, 时长: {duration:.2f}秒"
        else:
            return "文本转语音失败"
    except Exception as e:
        return f"文本转语音时发生错误: {str(e)}"

@mcp.tool()
def get_audio_file_info(audio_file: str) -> str:
    """获取音频文件信息
    
    Args:
        audio_file: 音频文件路径
        
    Returns:
        音频文件信息
    """
    try:
        info = get_audio_info(audio_file)
        if "error" in info:
            return f"获取音频信息失败: {info['error']}"
        
        info_text = f"""音频文件信息:
        
文件路径: {info['file_path']}
时长: {info['duration_seconds']:.2f}秒
采样率: {info['sample_rate']}Hz
声道数: {info['channels']}
位深度: {info['frame_width'] * 8}位
文件大小: {info['file_size_mb']:.2f}MB
"""
        return info_text
    except Exception as e:
        return f"获取音频信息时发生错误: {str(e)}"

@mcp.tool()
def validate_audio_file_tool(audio_file: str) -> str:
    """验证音频文件
    
    Args:
        audio_file: 音频文件路径
        
    Returns:
        验证结果
    """
    try:
        if validate_audio_file(audio_file):
            duration = get_audio_duration(audio_file)
            return f"音频文件验证通过！文件有效，时长: {duration:.2f}秒"
        else:
            return f"音频文件验证失败: {audio_file} 不存在或格式无效"
    except Exception as e:
        return f"验证音频文件时发生错误: {str(e)}"

@mcp.tool()
def get_audio_duration_tool(audio_file: str) -> str:
    """获取音频文件时长
    
    Args:
        audio_file: 音频文件路径
        
    Returns:
        音频时长信息
    """
    try:
        duration = get_audio_duration(audio_file)
        if duration > 0:
            return f"音频时长: {duration:.2f}秒 ({duration/60:.2f}分钟)"
        else:
            return f"无法获取音频时长: {audio_file}"
    except Exception as e:
        return f"获取音频时长时发生错误: {str(e)}"

@mcp.tool()
def list_available_voices() -> str:
    """列出可用的语音音色
    
    Returns:
        可用语音音色列表
    """
    try:
        # 使用asyncio运行异步函数
        voices = asyncio.run(edge_tts.list_voices())
        
        # 过滤中文语音
        chinese_voices = [v for v in voices if v["Locale"].startswith("zh-CN")]
        
        voices_info = "可用的中文语音音色:\n\n"
        for i, voice in enumerate(chinese_voices[:10]):  # 只显示前10个
            voices_info += f"{i+1}. {voice['ShortName']} ({voice['Gender']})\n"
            voices_info += f"   语言: {voice['Locale']}\n"
            voices_info += f"   描述: {voice.get('FriendlyName', 'N/A')}\n\n"
        
        return voices_info
    except Exception as e:
        return f"获取语音音色列表失败: {str(e)}"

def get_mcp_instance():
    """获取MCP实例"""
    return mcp 