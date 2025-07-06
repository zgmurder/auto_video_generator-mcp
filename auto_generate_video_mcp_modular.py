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
    generate_auto_video_mcp,
    generate_auto_video_sync,
    generate_auto_video_async,
    get_task_status,
    list_all_tasks,
    cancel_task,
    get_system_status,
    get_available_voice_options,
    validate_input_parameters,
    get_generation_estimate
)

# 导入GPU加速功能
from auto_video_modules.ffmpeg_utils import check_gpu_acceleration

# 导入运动检测功能
from auto_video_modules.motion_detection_utils import detect_video_motion, optimize_video_motion_params

# 创建主MCP服务器
mcp = FastMCP("auto-video-generator", log_level="INFO")

# 核心功能工具
@mcp.tool()
async def generate_auto_video_mcp(
    video_path: Any, 
    text: Any = "", 
    voice_index: Any = 0, 
    output_path: Any = "output_video.mp4",
    segments_mode: Any = "keep",
    segments: Any = "",
    subtitle_style: Any = "",
    auto_split_config: Any = "",
    quality_preset: Any = "720p",
    enable_motion_clip: Any = False,
    motion_clip_params: Any = None,
    enable_gpu_acceleration: Any = False,
    gpu_type: Any = "auto"
) -> str:
    """智能剪辑视频并自动添加字幕、语音（主要功能）
    新增：enable_motion_clip, motion_clip_params
    
    Args:
        video_path: 视频文件路径（必传）
        text: 要转换的文本（可选，为空时只进行视频处理）
        voice_index: 语音音色索引 (0-4)
        output_path: 输出视频路径
        segments_mode: 视频片段模式 ("keep" 保留指定片段, "cut" 剪掉指定片段)
        segments: 视频片段配置 (JSON字符串，格式: [{"start": "00:00:05", "end": "00:00:15"}])
        subtitle_style: 字幕样式配置 (JSON字符串)
        auto_split_config: 智能分割配置 (JSON字符串)
        quality_preset: 画质预设 ("240p", "360p", "480p", "720p", "1080p")
        enable_motion_clip: 是否启用运动剪辑
        motion_clip_params: 运动剪辑参数
        enable_gpu_acceleration: 是否启用GPU加速
        gpu_type: GPU类型 ("auto", "amd", "nvidia", "intel")
        
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
        video_path, text, voice_index, output_path, 
        segments_mode, segments, subtitle_style, auto_split_config, quality_preset,
        enable_motion_clip, motion_clip_params, enable_gpu_acceleration, gpu_type
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
async def check_gpu_acceleration_mcp() -> str:
    """检查GPU加速支持情况"""
    return await check_gpu_acceleration()

@mcp.tool()
async def detect_video_motion_mcp(video_path: str, config_path: str = "best_motion_clip_params.json") -> str:
    """检测视频中的运动片段"""
    return await detect_video_motion(video_path, config_path)

@mcp.tool()
async def optimize_video_motion_params_mcp(
    video_path: str, 
    target_min_duration: float = 50.0, 
    target_max_duration: float = 70.0
) -> str:
    """优化视频运动检测参数"""
    return await optimize_video_motion_params(video_path, target_min_duration, target_max_duration)

@mcp.tool()
async def get_all_available_tools() -> str:
    """获取所有可用的工具列表"""
    tools_info = """智能视频剪辑MCP服务器 - 可用工具列表

=== 核心功能 ===
- generate_auto_video_mcp: 智能剪辑视频并自动添加字幕、语音（默认使用异步任务）
- generate_auto_video_sync: 智能剪辑视频并自动添加字幕、语音（同步版本，适合短时间任务）
- generate_auto_video_async: 异步视频生成（推荐用于长时间任务）

=== 任务管理 ===
- get_task_status: 获取任务状态和进度
- list_all_tasks: 列出所有任务
- cancel_task: 取消正在运行的任务

=== 配置获取工具 ===
- get_system_status_mcp: 获取系统状态信息
- get_available_voice_options_mcp: 获取可用的语音选项
- validate_input_parameters_mcp: 验证输入参数
- get_generation_estimate_mcp: 获取生成时间估算
- check_gpu_acceleration_mcp: 检查GPU加速支持情况
- detect_video_motion_mcp: 检测视频中的运动片段
- optimize_video_motion_params_mcp: 优化视频运动检测参数
- get_all_available_tools: 获取所有可用的工具列表

=== 使用建议 ===
- 默认推荐使用 generate_auto_video_mcp（异步任务）
- 短时间任务（< 2分钟）可使用 generate_auto_video_sync
- 长时间任务（> 2分钟）建议使用 generate_auto_video_async

=== 异步任务使用流程 ===
1. 调用 generate_auto_video_mcp 或 generate_auto_video_async 创建任务，获得 task_id
2. 使用 get_task_status 查询任务进度
3. 任务完成后获取结果
4. 可选：使用 cancel_task 取消任务

=== 时间标记语法 ===
支持在文本中使用时间标记来控制静默时间：
- {5s} 表示5秒静默
- {5000ms} 表示5000毫秒静默
- {2.5s} 表示2.5秒静默
- {1500ms} 表示1500毫秒静默

示例："{5s}欢迎观看{5000ms}本视频由AI自动剪辑并添加智能字幕和语音解说。{2s}感谢您的观看！"

=== 参数说明 ===
- video_path: 视频文件路径（必传）
- text: 要转换的文本（可选，为空时只进行视频处理）
- voice_index: 语音音色索引 0-4（可选，默认0）
- output_path: 输出视频路径（可选，默认output_video.mp4）
- segments_mode: 视频片段模式 "keep"或"cut"（可选，默认keep）
- segments: 视频片段配置 JSON字符串（可选）
- subtitle_style: 字幕样式配置 JSON字符串（可选）
- auto_split_config: 智能分割配置 JSON字符串（可选）
- quality_preset: 画质预设 ("240p", "360p", "480p", "720p", "1080p")（可选，默认720p）
- enable_motion_clip: 是否启用运动剪辑
- motion_clip_params: 运动剪辑参数
- enable_gpu_acceleration: 是否启用GPU加速 (可选，默认False)
- gpu_type: GPU类型 ("auto", "amd", "nvidia", "intel") (可选，默认"auto")

=== 画质预设说明 ===
- 240p: 低画质预览 (426x240, 500k) - 适合快速预览
- 360p: 标清画质 (640x360, 800k) - 适合移动设备
- 480p: 标准画质 (854x480, 1.2M) - 适合一般用途
- 720p: 高清画质 (1280x720, 2M) - 默认设置
- 1080p: 全高清 (1920x1080, 4M) - 最高质量

=== 智能分割配置 ===
- 默认开启智能分割
- 最大长度: 50字符
- 最小长度: 10字符
- 分割字符: 。！？；，、
- 保留标点: 是

=== 默认字幕样式 ===
- 字体大小: 50
- 字体颜色: white (白色)
- 背景颜色: [0, 0, 0, 30] (半透明黑色)
- 字体路径: arial.ttf
- 左右边距: 100
- 底部边距: 50

=== 复杂参数示例 ===
segments: '[{"start": "00:00:05", "end": "00:00:15"}]'
subtitle_style: '{"fontSize": 60, "color": "yellow", "bgColor": [0, 0, 0, 128]}'
auto_split_config: '{"enable": true, "strategy": "smart", "maxChars": 20}'

=== 使用场景示例 ===
1. 仅视频处理（无文本）: 设置text为空字符串
2. 完整视频生成: 提供video_path和text
3. 快速预览: 使用quality_preset="240p"
4. 高质量输出: 使用quality_preset="1080p"
5. GPU加速处理: 设置enable_gpu_acceleration=True
6. 指定GPU类型: 设置gpu_type="amd"或"nvidia"或"intel"

=== 长时间任务处理建议 ===
- 默认使用异步任务处理，避免连接超时
- 定期查询任务状态，建议每5-10秒查询一次
- 任务完成后及时清理临时文件
- 支持并发任务，建议同时运行不超过5个任务
"""
    return tools_info

# 注册MCP工具
mcp.tool()(generate_auto_video_mcp)
mcp.tool()(generate_auto_video_sync)
mcp.tool()(generate_auto_video_async)
mcp.tool()(get_task_status)
mcp.tool()(list_all_tasks)
mcp.tool()(cancel_task)
mcp.tool()(check_gpu_acceleration_mcp)
mcp.tool()(detect_video_motion_mcp)
mcp.tool()(optimize_video_motion_params_mcp)

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
    