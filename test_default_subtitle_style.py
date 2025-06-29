"""
测试默认字幕样式配置
"""

import asyncio
import json
from auto_generate_video_mcp_modular import mcp

async def test_default_subtitle_style():
    """测试默认字幕样式"""
    print("=== 测试默认字幕样式配置 ===")
    
    # 测试参数
    text = "{2000ms}欢迎观看{1500ms}本视频教程{1000ms}使用新的默认字幕样式"
    video_path = "E:\\project\\py\\auto-video-generator\\demo.mp4"
    
    print(f"测试文本: {text}")
    print(f"视频路径: {video_path}")
    print("使用默认字幕样式配置:")
    print("- 字体大小: 40")
    print("- 字体颜色: white")
    print("- 背景颜色: [0, 0, 0, 0]")
    print()
    
    try:
        # 调用核心功能，不传递subtitle_style参数，使用默认配置
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path,
            "voice_index": 0,
            "output_path": "output_default_style.mp4"
        })
        
        print("=== 生成结果 ===")
        print(result)
        
        # 解析结果
        try:
            # MCP工具返回的是TextContent对象，需要提取text属性
            if hasattr(result, 'text'):
                result_str = result.text
            else:
                result_str = str(result)
            result_data = json.loads(result_str)
            if result_data.get("status") == "success":
                print("\n✅ 默认字幕样式测试成功!")
                print(f"输出文件: {result_data.get('absolute_output_path')}")
                print(f"使用的配置: {result_data.get('config_used', {}).get('subtitle_style', '默认配置')}")
            else:
                print(f"\n❌ 测试失败: {result}")
        except json.JSONDecodeError:
            print(f"\n❌ 结果解析失败: {result}")
        except Exception as e:
            print(f"\n❌ 结果处理异常: {e}")
            print(f"原始结果: {result}")
            
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")

async def test_custom_subtitle_style():
    """测试自定义字幕样式"""
    print("\n=== 测试自定义字幕样式配置 ===")
    
    # 测试参数
    text = "{2000ms}欢迎观看{1500ms}本视频教程{1000ms}使用自定义字幕样式"
    video_path = "E:\\project\\py\\auto-video-generator\\demo.mp4"
    
    # 自定义字幕样式
    custom_style = {
        "fontSize": 60,
        "color": "yellow",
        "bgColor": [0, 0, 0, 128]
    }
    
    print(f"测试文本: {text}")
    print(f"视频路径: {video_path}")
    print(f"自定义字幕样式: {custom_style}")
    print()
    
    try:
        # 调用核心功能，传递自定义subtitle_style参数
        result = await mcp.call_tool("generate_auto_video_mcp", {
            "text": text,
            "video_path": video_path,
            "voice_index": 0,
            "output_path": "output_custom_style.mp4",
            "subtitle_style": json.dumps(custom_style, ensure_ascii=False)
        })
        
        print("=== 生成结果 ===")
        print(result)
        
        # 解析结果
        try:
            # MCP工具返回的是TextContent对象，需要提取text属性
            if hasattr(result, 'text'):
                result_str = result.text
            else:
                result_str = str(result)
            result_data = json.loads(result_str)
            if result_data.get("status") == "success":
                print("\n✅ 自定义字幕样式测试成功!")
                print(f"输出文件: {result_data.get('absolute_output_path')}")
                print(f"使用的配置: {result_data.get('config_used', {}).get('subtitle_style', '默认配置')}")
            else:
                print(f"\n❌ 测试失败: {result}")
        except json.JSONDecodeError:
            print(f"\n❌ 结果解析失败: {result}")
        except Exception as e:
            print(f"\n❌ 结果处理异常: {e}")
            print(f"原始结果: {result}")
            
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")

async def main():
    """主测试函数"""
    print("开始测试字幕样式配置...")
    print()
    
    # 测试默认字幕样式
    await test_default_subtitle_style()
    
    # 测试自定义字幕样式
    await test_custom_subtitle_style()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main()) 