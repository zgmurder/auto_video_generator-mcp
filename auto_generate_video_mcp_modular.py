"""
模块化自动视频生成MCP服务器
整合所有模块功能，提供完整的视频生成服务
"""

import asyncio
from mcp.server.fastmcp import FastMCP
from typing import Any

# 导入核心功能
from auto_video_modules.mcp_tools import (
    generate_auto_video,
    get_system_status,
    get_available_voice_options,
    validate_input_parameters,
    get_generation_estimate
)

# 创建主MCP服务器
mcp = FastMCP("auto-video-generator", log_level="INFO")

# 核心功能工具
@mcp.tool()
async def generate_auto_video_mcp(
    text: Any, 
    video_path: Any, 
    voice_index: Any = 0, 
    output_path: Any = "output_video.mp4",
    segments_mode: Any = "keep",
    segments: Any = "",
    subtitle_style: Any = "",
    auto_split_config: Any = ""
) -> str:
    """智能剪辑视频并自动添加字幕、语音（主要功能）
    
    Args:
        text: 要转换的文本
        video_path: 视频文件路径
        voice_index: 语音音色索引 (0-4)
        output_path: 输出视频路径
        segments_mode: 视频片段模式 ("keep" 保留指定片段, "cut" 剪掉指定片段)
        segments: 视频片段配置 (JSON字符串，格式: [{"start": "00:00:05", "end": "00:00:15"}])
        subtitle_style: 字幕样式配置 (JSON字符串)
        auto_split_config: 智能分割配置 (JSON字符串)
        
    Returns:
        生成结果信息
    """
    import json
    # 保证所有复杂参数为字符串
    if not isinstance(segments, str):
        segments = json.dumps(segments, ensure_ascii=False)
    if not isinstance(subtitle_style, str):
        subtitle_style = json.dumps(subtitle_style, ensure_ascii=False)
    if not isinstance(auto_split_config, str):
        auto_split_config = json.dumps(auto_split_config, ensure_ascii=False)
    return await generate_auto_video(
        text, video_path, voice_index, output_path, 
        segments_mode, segments, subtitle_style, auto_split_config
    )

# 配置获取工具
@mcp.tool()
async def get_system_status_mcp() -> str:
    """获取系统状态信息"""
    return await get_system_status()

@mcp.tool()
async def get_available_voice_options_mcp() -> str:
    """获取可用的语音选项"""
    return await get_available_voice_options()

@mcp.tool()
async def validate_input_parameters_mcp(text: str, video_path: str, voice_index: int = 0) -> str:
    """验证输入参数"""
    return await validate_input_parameters(text, video_path, voice_index)

@mcp.tool()
async def get_generation_estimate_mcp(text: str, video_path: str) -> str:
    """获取生成时间估算"""
    return await get_generation_estimate(text, video_path)

@mcp.tool()
async def get_all_available_tools() -> str:
    """获取所有可用的工具列表"""
    tools_info = """智能视频剪辑MCP服务器 - 可用工具列表

=== 核心功能 ===
- generate_auto_video_mcp: 智能剪辑视频并自动添加字幕、语音（主要功能）

=== 配置获取工具 ===
- get_system_status_mcp: 获取系统状态信息
- get_available_voice_options_mcp: 获取可用的语音选项
- validate_input_parameters_mcp: 验证输入参数
- get_generation_estimate_mcp: 获取生成时间估算
- get_all_available_tools: 获取所有可用的工具列表

=== 时间标记语法 ===
支持在文本中使用时间标记来控制静默时间：
- {5s} 表示5秒静默
- {5000ms} 表示5000毫秒静默
- {2.5s} 表示2.5秒静默
- {1500ms} 表示1500毫秒静默

示例："{5s}欢迎观看{5000ms}本视频由AI自动剪辑并添加智能字幕和语音解说。{2s}感谢您的观看！"

=== 参数说明 ===
- text: 要转换的文本（必填）
- video_path: 视频文件路径（必填）
- voice_index: 语音音色索引 0-4（可选，默认0）
- output_path: 输出视频路径（可选，默认output_video.mp4）
- segments_mode: 视频片段模式 "keep"或"cut"（可选，默认keep）
- segments: 视频片段配置 JSON字符串（可选）
- subtitle_style: 字幕样式配置 JSON字符串（可选）
- auto_split_config: 智能分割配置 JSON字符串（可选）

=== 默认字幕样式 ===
- 字体大小: 40
- 字体颜色: white (白色)
- 背景颜色: [0, 0, 0, 0] (透明)
- 字体路径: arial.ttf
- 左右边距: 100
- 底部边距: 50

=== 复杂参数示例 ===
segments: '[{"start": "00:00:05", "end": "00:00:15"}]'
subtitle_style: '{"fontSize": 60, "color": "yellow", "bgColor": [0, 0, 0, 128]}'
auto_split_config: '{"enable": true, "strategy": "smart", "maxChars": 20}'
"""
    return tools_info

def main():
    print("启动自动视频生成MCP服务器 v3.0...")
    print("服务器包含以下功能:")
    print("- 核心视频生成功能")
    print("- 配置获取工具")
    print("\n使用 get_all_available_tools 查看所有可用工具")
    print("服务器将以SSE方式运行")
    print("访问地址: http://localhost:8000/sse")
    
    # 以SSE方式运行
    mcp.run(transport='sse')

if __name__ == "__main__":
    main() 
    