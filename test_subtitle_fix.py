#!/usr/bin/env python3
"""
测试字幕生成过程
输出文本分割和timing生成过程
"""

import asyncio
import json
import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auto_video_modules.subtitle_utils import split_timings
from auto_video_modules.voice_utils import get_voice_by_index
from auto_video_modules.audio_utils import synthesize_and_get_durations
from auto_video_modules.mcp_tools import generate_auto_video_mcp

async def test_text_to_timing():
    """测试文本到timing的转换过程"""
    
    # 测试文本
    test_text = "这是一个测试文本，包含多个句子。{5000ms}这是第二句话，用来测试时间标记的处理。{3000ms}这是第三句话，测试智能分割功能。"
    
    print("=" * 60)
    print("文本到Timing转换测试")
    print("=" * 60)
    print(f"原始文本: {test_text}")
    print()
    
    # 1. 创建初始timing结构
    initial_timing = [{"text": test_text, "duration": 0}]
    print("1. 初始timing结构:")
    print(json.dumps(initial_timing, ensure_ascii=False, indent=2))
    print()
    
    # 2. 智能分割文本
    print("2. 智能分割文本:")
    timing = split_timings(
        initial_timing,
        max_chars=50,
        min_chars=5
    )
    print(f"分割后片段数: {len(timing)}")
    for i, segment in enumerate(timing):
        print(f"  片段{i+1}: {segment}")
    print()
    
    # 3. 获取语音音色
    voice = get_voice_by_index(0)
    print(f"3. 语音音色: {voice}")
    print()
    
    # 4. 合成音频并获取时长
    print("4. 合成音频并获取时长:")
    tts_result = await synthesize_and_get_durations(timing, voice)
    audio_path = tts_result["audio_path"]
    segments_with_duration = tts_result["segments"]
    
    print(f"音频文件: {audio_path}")
    print(f"带时长的片段数: {len(segments_with_duration)}")
    for i, segment in enumerate(segments_with_duration):
        print(f"  片段{i+1}: {segment}")
    print()
    
    # 5. 生成字幕时间轴
    print("5. 生成字幕时间轴:")
    subtitle_tuples = []
    cur_time = 0.0
    for seg in segments_with_duration:
        text = seg["text"]
        duration = seg.get("duration", 0)
        start = cur_time
        end = cur_time + duration
        subtitle_tuples.append((text, start, end))
        cur_time = end
        print(f"  时间轴: {text} -> {start:.2f}s - {end:.2f}s (时长: {duration:.2f}s)")
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return {
        "original_text": test_text,
        "initial_timing": initial_timing,
        "split_timing": timing,
        "segments_with_duration": segments_with_duration,
        "subtitle_tuples": subtitle_tuples
    }

async def test_full_video_generation():
    """测试完整的视频生成流程"""
    
    print("=" * 60)
    print("完整视频生成测试")
    print("=" * 60)
    
    # 测试参数
    video_path = "output_video.mp4"  # 使用存在的视频文件
    text = "这是一个测试文本，包含多个句子。{5000ms}这是第二句话，用来测试时间标记的处理。{3000ms}这是第三句话，测试智能分割功能。"
    output_path = "output_test8_cut.mp4"
    
    print(f"视频路径: {video_path}")
    print(f"文本: {text}")
    print(f"输出路径: {output_path}")
    print()
    
    try:
        # 调用MCP工具生成视频
        result = await generate_auto_video_mcp(
            video_path=video_path,
            text=text,
            voice_index=0,
            output_path=output_path
        )
        
        print("生成结果:")
        print(result)
        
        return result
        
    except Exception as e:
        print(f"生成失败: {e}")
        return None

if __name__ == "__main__":
    # 测试文本到timing转换
    result = asyncio.run(test_text_to_timing())
    
    # 保存结果到文件
    with open("timing_test_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print("结果已保存到 timing_test_result.json")
    
    # 测试完整视频生成
    print("\n" + "=" * 60)
    print("开始测试完整视频生成...")
    video_result = asyncio.run(test_full_video_generation()) 