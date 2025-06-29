"""
FFmpeg工具模块
负责FFmpeg的检测、配置和路径管理
"""

import sys
import shutil
import subprocess
from pydub import AudioSegment
import moviepy
from moviepy.config import change_settings
from mcp.server.fastmcp import FastMCP

# 创建MCP实例
mcp = FastMCP("ffmpeg-utils", log_level="ERROR")

def check_ffmpeg():
    """检查系统是否安装了ffmpeg"""
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    
    if ffmpeg_path and ffprobe_path:
        print(f"找到系统ffmpeg: {ffmpeg_path}")
        print(f"找到系统ffprobe: {ffprobe_path}")
        return ffmpeg_path, ffprobe_path
    else:
        print("未找到系统ffmpeg，请按以下步骤安装：")
        print("1. 访问 https://ffmpeg.org/download.html")
        print("2. 下载Windows版本")
        print("3. 解压到任意目录")
        print("4. 将ffmpeg/bin目录添加到系统PATH环境变量")
        print("5. 重启命令行窗口")
        raise FileNotFoundError("系统未安装ffmpeg，请先安装ffmpeg")

def setup_ffmpeg():
    """设置FFmpeg路径到各个库"""
    try:
        ffmpeg_path, ffprobe_path = check_ffmpeg()
        
        # 设置 pydub 的 ffmpeg 路径
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffmpeg = ffmpeg_path
        AudioSegment.ffprobe = ffprobe_path
        
        # 设置moviepy的ffmpeg路径
        change_settings({"FFMPEG_BINARY": ffmpeg_path})
        
        return ffmpeg_path, ffprobe_path
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)

def test_ffmpeg():
    """测试FFmpeg是否正常工作"""
    try:
        ffmpeg_path, ffprobe_path = check_ffmpeg()
        
        # 测试ffmpeg版本
        result = subprocess.run([ffmpeg_path, "-version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("FFmpeg测试成功")
            return True
        else:
            print("FFmpeg测试失败")
            return False
            
    except Exception as e:
        print(f"FFmpeg测试出错: {e}")
        return False

@mcp.tool()
async def check_ffmpeg_status() -> str:
    """检查FFmpeg状态
    
    Returns:
        FFmpeg状态信息
    """
    try:
        ffmpeg_path, ffprobe_path = check_ffmpeg()
        return f"FFmpeg状态正常\nffmpeg: {ffmpeg_path}\nffprobe: {ffprobe_path}"
    except Exception as e:
        return f"FFmpeg状态异常: {str(e)}"

@mcp.tool()
async def test_ffmpeg_functionality() -> str:
    """测试FFmpeg功能
    
    Returns:
        测试结果信息
    """
    try:
        if test_ffmpeg():
            return "FFmpeg功能测试成功"
        else:
            return "FFmpeg功能测试失败"
    except Exception as e:
        return f"FFmpeg功能测试出错: {str(e)}"

@mcp.tool()
async def get_ffmpeg_version() -> str:
    """获取FFmpeg版本信息
    
    Returns:
        FFmpeg版本信息
    """
    try:
        ffmpeg_path, _ = check_ffmpeg()
        result = subprocess.run([ffmpeg_path, "-version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # 提取版本信息
            lines = result.stdout.split('\n')
            version_line = lines[0] if lines else "未知版本"
            return f"FFmpeg版本信息:\n{version_line}"
        else:
            return "无法获取FFmpeg版本信息"
    except Exception as e:
        return f"获取FFmpeg版本信息失败: {str(e)}"

def get_mcp_instance():
    """获取MCP实例
    
    Returns:
        FastMCP: MCP实例
    """
    return mcp 