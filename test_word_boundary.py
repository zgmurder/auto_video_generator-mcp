#!/usr/bin/env python3
"""
测试词语连贯性分割
验证在分割时是否保持词语的完整性
"""

import asyncio
import json
import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auto_video_modules.subtitle_utils import split_timings

def test_word_boundary_split():
    """测试词语边界分割"""
    
    # 测试用例
    test_cases = [
        {
            "name": "中文词语测试",
            "text": "人工智能技术正在快速发展，机器学习算法变得越来越智能。",
            "max_chars": 10,
            "min_chars": 3
        },
        {
            "name": "中英文混合测试",
            "text": "Python编程语言非常popular，深度学习deep learning技术很advanced。",
            "max_chars": 12,
            "min_chars": 4
        },
        {
            "name": "标点符号测试",
            "text": "这是一个测试文本，包含多个句子！还有问号？以及感叹号！",
            "max_chars": 8,
            "min_chars": 3
        },
        {
            "name": "长句子测试",
            "text": "今天天气很好，我们一起去公园散步，呼吸新鲜空气，享受美好时光。",
            "max_chars": 15,
            "min_chars": 5
        },
        {
            "name": "带静默标记测试",
            "text": "第一句话。{3000ms}第二句话比较长，需要分割。{2000ms}第三句话。",
            "max_chars": 10,
            "min_chars": 3
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
        
        # 创建初始timing结构
        initial_timing = [{"text": text, "duration": 0}]
        
        # 智能分割文本
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
                # 检查是否在词语中间断开
                _check_word_boundary(segment['text'], j+1)
            else:
                print(f"  片段{j+1}: 静默 {segment['delay']}ms")
        
        print()

def _check_word_boundary(text, segment_num):
    """检查文本是否在词语中间断开"""
    # 检查是否以不完整的英文单词结尾
    if text and text[-1].isalpha():
        # 检查是否是单个字母（可能是断开的单词）
        if len(text) == 1 or (len(text) > 1 and not text[-2].isalpha()):
            print(f"    ⚠️  片段{segment_num}可能包含不完整的英文单词")
    
    # 检查是否以不完整的标点符号结尾（除了正常的句末标点）
    if text and text[-1] in '，、；：':
        print(f"    ⚠️  片段{segment_num}以逗号或分号结尾，可能不是最佳分割点")

if __name__ == "__main__":
    test_word_boundary_split() 