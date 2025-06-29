#!/usr/bin/env python3
"""
测试新的字幕分割逻辑
根据maxLength和minLength进行分割，保留静默功能
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

async def test_new_split_logic():
    """测试新的分割逻辑"""
    
    # 测试用例
    test_cases = [
        {
            "name": "短文本测试",
            "text": "这是一个短文本。",
            "max_chars": 20,
            "min_chars": 5
        },
        {
            "name": "长文本测试",
            "text": "这是一个很长的文本，用来测试根据字符数分割的功能，应该会被分割成多个片段。",
            "max_chars": 15,
            "min_chars": 5
        },
        {
            "name": "带静默标记测试",
            "text": "第一段文本。{5000ms}第二段文本，比较长，应该会被分割。{3000ms}第三段文本。",
            "max_chars": 12,
            "min_chars": 3
        },
        {
            "name": "边界测试",
            "text": "这段文本正好二十个字符长度。",
            "max_chars": 20,
            "min_chars": 5
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"测试用例 {i+1}: {test_case['name']}")
        print(f"{'='*60}")
        
        text = test_case['text']
        max_chars = test_case['max_chars']
        min_chars = test_case['min_chars']
        
        print(f"原始文本: {text}")
        print(f"最大字符数: {max_chars}")
        print(f"最小字符数: {min_chars}")
        print(f"文本长度: {len(text)}")
        print()
        
        # 1. 创建初始timing结构
        initial_timing = [{"text": text, "duration": 0}]
        
        # 2. 智能分割文本
        print("分割结果:")
        timing = split_timings(
            initial_timing,
            max_chars=max_chars,
            min_chars=min_chars
        )
        
        print(f"分割后片段数: {len(timing)}")
        for j, segment in enumerate(timing):
            if segment['text']:
                print(f"  片段{j+1}: '{segment['text']}' (长度: {len(segment['text'])})")
            else:
                print(f"  片段{j+1}: 静默 {segment['delay']}ms")
        
        # 3. 测试音频合成（可选）
        if i == 2:  # 只对带静默标记的测试用例进行音频合成测试
            print("\n音频合成测试:")
            voice = get_voice_by_index(0)
            tts_result = await synthesize_and_get_durations(timing, voice)
            segments_with_duration = tts_result["segments"]
            
            print(f"音频片段数: {len(segments_with_duration)}")
            for j, segment in enumerate(segments_with_duration):
                if segment['text']:
                    print(f"  音频片段{j+1}: '{segment['text']}' (时长: {segment['duration']:.2f}s)")
                else:
                    print(f"  音频片段{j+1}: 静默 (时长: {segment['duration']:.2f}s)")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_new_split_logic()) 