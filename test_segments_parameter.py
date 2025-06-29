"""
测试segments参数传递
验证前端传递segments参数的正确方式
"""

import asyncio
import json
from auto_generate_video_mcp_modular import mcp

async def test_segments_parameter():
    """测试segments参数的不同传递方式"""
    
    # 测试参数
    text = "{2000ms}欢迎观看{1500ms}本视频教程"
    video_path = "E:\\project\\py\\auto-video-generator\\demo.mp4"
    
    print("=== 测试segments参数传递 ===")
    
    # 测试1: 基础参数（无segments）
    print("\n1. 测试基础参数（无segments）")
    try:
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path
        })
        print("✓ 基础参数测试成功")
        print(f"结果: {result[:200]}...")
    except Exception as e:
        print(f"✗ 基础参数测试失败: {e}")
    
    # 测试2: 传递segments参数（字符串格式）
    print("\n2. 测试segments参数（字符串格式）")
    segments_str = '[{"start": "00:00:05", "end": "00:00:15"}]'
    try:
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path,
            "segments": segments_str
        })
        print("✓ segments参数测试成功")
        print(f"结果: {result[:200]}...")
    except Exception as e:
        print(f"✗ segments参数测试失败: {e}")
    
    # 测试3: 传递segments参数（JSON对象格式）
    print("\n3. 测试segments参数（JSON对象格式）")
    segments_obj = [{"start": "00:00:10", "end": "00:00:20"}]
    try:
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path,
            "segments": json.dumps(segments_obj)
        })
        print("✓ segments参数（JSON对象）测试成功")
        print(f"结果: {result[:200]}...")
    except Exception as e:
        print(f"✗ segments参数（JSON对象）测试失败: {e}")
    
    # 测试4: 传递所有复杂参数（确保都是字符串）
    print("\n4. 测试所有复杂参数（字符串格式）")
    try:
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path,
            "segments_mode": "keep",
            "segments": '[{"start": "00:00:05", "end": "00:00:15"}]',
            "subtitle_style": '{"fontSize": 50, "color": "yellow"}',
            "auto_split_config": '{"enable": true, "strategy": "smart", "maxChars": 25}'
        })
        print("✓ 所有复杂参数测试成功")
        print(f"结果: {result[:200]}...")
    except Exception as e:
        print(f"✗ 所有复杂参数测试失败: {e}")
    
    # 测试5: 验证参数解析
    print("\n5. 验证参数解析")
    try:
        # 测试JSON解析
        segments_test = '[{"start": "00:00:05", "end": "00:00:15"}]'
        parsed = json.loads(segments_test)
        print(f"✓ JSON解析成功: {parsed}")
        
        # 测试参数类型
        print(f"✓ segments类型: {type(segments_test)}")
        print(f"✓ 解析后类型: {type(parsed)}")
        
    except Exception as e:
        print(f"✗ 参数解析测试失败: {e}")
    
    # 测试6: 模拟前端调用方式
    print("\n6. 模拟前端调用方式")
    try:
        # 模拟前端传递的参数格式
        frontend_params = {
            "text": text,
            "video_path": video_path,
            "segments_mode": "keep",
            "segments": '[{"start": "00:00:05", "end": "00:00:15"}]',
            "subtitle_style": '{"fontSize": 50, "color": "yellow"}',
            "auto_split_config": '{"enable": true, "strategy": "smart", "maxChars": 25}'
        }
        
        # 确保所有复杂参数都是字符串
        for key, value in frontend_params.items():
            if key in ['segments', 'subtitle_style', 'auto_split_config'] and not isinstance(value, str):
                frontend_params[key] = json.dumps(value)
        
        result = await mcp.call_tool("generate_auto_video_mcp", frontend_params)
        print("✓ 前端调用方式测试成功")
        print(f"结果: {result[:200]}...")
    except Exception as e:
        print(f"✗ 前端调用方式测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_segments_parameter()) 