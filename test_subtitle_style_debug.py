"""
调试字幕样式配置
验证字幕样式参数是否正确传递和使用
"""

import asyncio
import json
from auto_generate_video_mcp_modular import mcp

async def test_subtitle_style_debug():
    """调试字幕样式配置"""
    
    # 测试参数
    text = "{2000ms}欢迎观看{1500ms}本视频教程"
    video_path = "E:\\project\\py\\auto-video-generator\\demo.mp4"
    
    print("=== 调试字幕样式配置 ===")
    
    # 测试：小字号黑色字体，半透明黑色背景
    print("\n测试：小字号黑色字体，半透明黑色背景")
    subtitle_style = {
        "fontSize": 24,
        "color": "black", 
        "bgColor": [0, 0, 0, 128],
        "marginX": 240,
        "marginBottom": 20
    }
    
    try:
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path,
            "subtitle_style": json.dumps(subtitle_style, ensure_ascii=False)
        })
        print("✓ 字幕样式测试成功")
        print(f"结果: {result[:500]}...")
        
        # 解析结果，检查配置是否正确传递
        if isinstance(result, list) and len(result) > 0:
            result_text = result[0].text
            try:
                result_json = json.loads(result_text)
                config_used = result_json.get('config_used', {})
                subtitle_style_used = config_used.get('subtitle_style', {})
                print(f"\n实际使用的字幕样式配置:")
                print(f"fontSize: {subtitle_style_used.get('fontSize')}")
                print(f"color: {subtitle_style_used.get('color')}")
                print(f"bgColor: {subtitle_style_used.get('bgColor')}")
                print(f"marginX: {subtitle_style_used.get('marginX')}")
                print(f"marginBottom: {subtitle_style_used.get('marginBottom')}")
            except json.JSONDecodeError:
                print("无法解析返回的JSON结果")
        
    except Exception as e:
        print(f"✗ 字幕样式测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_subtitle_style_debug()) 