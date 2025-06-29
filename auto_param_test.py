#!/usr/bin/env python3
"""
自动化参数测试脚本
从必传参数开始，逐步增加参数，测试到全部参数
"""

import asyncio
import json
from auto_video_modules.mcp_tools import get_mcp_instance

async def auto_test_generate_auto_video():
    mcp = get_mcp_instance()
    video_path = r"E:\project\py\auto-video-generator\demo.mp4"
    text = "{2000ms}欢迎观看{1500ms}本视频教程"

    print("开始自动化参数测试...")
    print(f"视频路径: {video_path}")
    print(f"文本内容: {text}")
    print("=" * 60)

    # 1. 只传必传参数
    print("\n【1. 只传必传参数】")
    try:
        result = await mcp.call_tool("generate_auto_video", {
            "text": text,
            "video_path": video_path
        })
        print("✓ 测试成功")
        print(f"结果: {result}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 2. 增加 voice_index
    print("\n【2. 增加 voice_index】")
    try:
        result = await mcp.call_tool("generate_auto_video", {
            "text": text,
            "video_path": video_path,
            "voice_index": 1
        })
        print("✓ 测试成功")
        print(f"结果: {result}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 3. 增加 output_path
    print("\n【3. 增加 output_path】")
    try:
        result = await mcp.call_tool("generate_auto_video", {
            "text": text,
            "video_path": video_path,
            "voice_index": 1,
            "output_path": "output_test3.mp4"
        })
        print("✓ 测试成功")
        print(f"结果: {result}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 4. 增加 segments_mode
    print("\n【4. 增加 segments_mode】")
    try:
        result = await mcp.call_tool("generate_auto_video", {
            "text": text,
            "video_path": video_path,
            "voice_index": 1,
            "output_path": "output_test4.mp4",
            "segments_mode": "keep"
        })
        print("✓ 测试成功")
        print(f"结果: {result}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 5. 增加 segments
    print("\n【5. 增加 segments】")
    try:
        segments_str = '[{"start": "00:00:05", "end": "00:00:15"}]'
        result = await mcp.call_tool("generate_auto_video", {
            "text": text,
            "video_path": video_path,
            "voice_index": 1,
            "output_path": "output_test5.mp4",
            "segments_mode": "keep",
            "segments": segments_str
        })
        print("✓ 测试成功")
        print(f"结果: {result}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 6. 增加 subtitle_style
    print("\n【6. 增加 subtitle_style】")
    try:
        subtitle_style_str = '{"fontSize": 44, "color": "yellow", "bgColor": [0, 0, 0, 128], "marginX": 120, "marginBottom": 60}'
        result = await mcp.call_tool("generate_auto_video", {
            "text": text,
            "video_path": video_path,
            "voice_index": 1,
            "output_path": "output_test6.mp4",
            "segments_mode": "keep",
            "segments": segments_str,
            "subtitle_style": subtitle_style_str
        })
        print("✓ 测试成功")
        print(f"结果: {result}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 7. 增加 auto_split_config
    print("\n【7. 增加 auto_split_config】")
    try:
        auto_split_config_str = '{"enable": true, "strategy": "duration", "targetDuration": 2.0, "maxChars": 18}'
        result = await mcp.call_tool("generate_auto_video", {
            "text": text,
            "video_path": video_path,
            "voice_index": 1,
            "output_path": "output_test7.mp4",
            "segments_mode": "keep",
            "segments": segments_str,
            "subtitle_style": subtitle_style_str,
            "auto_split_config": auto_split_config_str
        })
        print("✓ 测试成功")
        print(f"结果: {result}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 8. 测试不同参数组合
    print("\n【8. 测试不同参数组合】")
    try:
        # 测试cut模式
        result = await mcp.call_tool("generate_auto_video", {
            "text": text,
            "video_path": video_path,
            "voice_index": 2,
            "output_path": "output_test8_cut.mp4",
            "segments_mode": "cut",
            "segments": '[{"start": "00:00:10", "end": "00:00:20"}]',
            "subtitle_style": '{"fontSize": 50, "color": "red", "bgColor": [255, 255, 255, 100]}',
            "auto_split_config": '{"enable": true, "strategy": "smart", "maxChars": 15}'
        })
        print("✓ 测试成功")
        print(f"结果: {result}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    print("\n" + "=" * 60)
    print("自动化参数测试完成！")

if __name__ == "__main__":
    asyncio.run(auto_test_generate_auto_video()) 