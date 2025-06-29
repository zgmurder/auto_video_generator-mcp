"""
测试字幕样式配置
验证颜色和背景是否正确应用
"""

import asyncio
import json
from auto_generate_video_mcp_modular import mcp

async def test_subtitle_style():
    """测试字幕样式配置"""
    
    # 测试参数
    text = "{2000ms}欢迎观看{1500ms}本视频教程"
    video_path = "E:\\project\\py\\auto-video-generator\\demo.mp4"
    
    print("=== 测试字幕样式配置 ===")
    
    # 测试1: 黄色字体，半透明黑色背景
    print("\n1. 测试黄色字体，半透明黑色背景")
    subtitle_style = {
        "fontSize": 44,
        "color": "yellow", 
        "bgColor": [0, 0, 0, 128],
        "marginX": 120,
        "marginBottom": 60
    }
    
    try:
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path,
            "subtitle_style": json.dumps(subtitle_style, ensure_ascii=False)
        })
        print("✓ 字幕样式测试成功")
        print(f"结果: {result[:300]}...")
    except Exception as e:
        print(f"✗ 字幕样式测试失败: {e}")
    
    # 测试2: 红色字体，无背景
    print("\n2. 测试红色字体，无背景")
    subtitle_style2 = {
        "fontSize": 50,
        "color": "red",
        "bgColor": [0, 0, 0, 0],
        "marginX": 100,
        "marginBottom": 50
    }
    
    try:
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path,
            "subtitle_style": json.dumps(subtitle_style2, ensure_ascii=False)
        })
        print("✓ 红色字体测试成功")
        print(f"结果: {result[:300]}...")
    except Exception as e:
        print(f"✗ 红色字体测试失败: {e}")
    
    # 测试3: 蓝色字体，半透明白色背景
    print("\n3. 测试蓝色字体，半透明白色背景")
    subtitle_style3 = {
        "fontSize": 48,
        "color": "blue",
        "bgColor": [255, 255, 255, 100],
        "marginX": 150,
        "marginBottom": 80
    }
    
    try:
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path,
            "subtitle_style": json.dumps(subtitle_style3, ensure_ascii=False)
        })
        print("✓ 蓝色字体测试成功")
        print(f"结果: {result[:300]}...")
    except Exception as e:
        print(f"✗ 蓝色字体测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_subtitle_style()) 