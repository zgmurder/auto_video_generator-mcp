#!/usr/bin/env python3
"""
测试字幕功能是否正常
"""

import asyncio
import json
from auto_generate_video_mcp_modular import mcp

async def test_subtitle():
    """测试字幕功能"""
    print("=== 测试字幕功能 ===")
    
    # 测试基础参数
    result = await mcp.call_tool("generate_auto_video_mcp", {
        "video_path": "test_video.mp4",
        "text": "这是一个测试字幕，用于验证功能是否正常。",
        "voice_index": 0,
        "output_path": "test_output.mp4"
    })
    
    print(f"测试结果: {result}")
    
    # 测试字幕样式参数
    result2 = await mcp.call_tool("generate_auto_video_mcp", {
        "video_path": "test_video.mp4", 
        "text": "测试自定义字幕样式：白色字体，半透明黑色背景。",
        "voice_index": 0,
        "output_path": "test_output_styled.mp4",
        "subtitle_style": json.dumps({
            "fontSize": 50,
            "color": "white", 
            "bgColor": [0, 0, 0, 30],
            "fontPath": "arial.ttf"
        })
    })
    
    print(f"样式测试结果: {result2}")

if __name__ == "__main__":
    asyncio.run(test_subtitle()) 