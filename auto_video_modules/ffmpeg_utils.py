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
        # AudioSegment.ffprobe = ffprobe_path  # 注释掉，因为 pydub 可能不支持这个属性
        
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

def check_gpu_support():
    """检查GPU加速支持情况
    
    Returns:
        dict: GPU支持信息
    """
    try:
        ffmpeg_path, _ = check_ffmpeg()
        
        # 检查可用的硬件编码器
        result = subprocess.run([ffmpeg_path, "-hide_banner", "-encoders"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return {"supported": False, "error": "无法获取编码器列表"}
        
        encoders_output = result.stdout
        
        # 检查AMD AMF编码器
        amf_encoders = []
        if "h264_amf" in encoders_output:
            amf_encoders.append("h264_amf")
        if "hevc_amf" in encoders_output:
            amf_encoders.append("hevc_amf")
        if "av1_amf" in encoders_output:
            amf_encoders.append("av1_amf")
        
        # 检查NVIDIA NVENC编码器
        nvenc_encoders = []
        if "h264_nvenc" in encoders_output:
            nvenc_encoders.append("h264_nvenc")
        if "hevc_nvenc" in encoders_output:
            nvenc_encoders.append("hevc_nvenc")
        if "av1_nvenc" in encoders_output:
            nvenc_encoders.append("av1_nvenc")
        
        # 检查Intel QSV编码器
        qsv_encoders = []
        if "h264_qsv" in encoders_output:
            qsv_encoders.append("h264_qsv")
        if "hevc_qsv" in encoders_output:
            qsv_encoders.append("hevc_qsv")
        
        # 检查VAAPI编码器
        vaapi_encoders = []
        if "h264_vaapi" in encoders_output:
            vaapi_encoders.append("h264_vaapi")
        if "hevc_vaapi" in encoders_output:
            vaapi_encoders.append("hevc_vaapi")
        
        # 获取显卡信息
        try:
            gpu_result = subprocess.run(["wmic", "path", "win32_VideoController", "get", "name"], 
                                      capture_output=True, text=True, timeout=5)
            gpu_name = "未知"
            if gpu_result.returncode == 0:
                lines = gpu_result.stdout.strip().split('\n')
                if len(lines) > 1:
                    gpu_name = lines[1].strip()
        except:
            gpu_name = "未知"
        
        return {
            "supported": len(amf_encoders) > 0 or len(nvenc_encoders) > 0 or len(qsv_encoders) > 0 or len(vaapi_encoders) > 0,
            "gpu_name": gpu_name,
            "amf_encoders": amf_encoders,
            "nvenc_encoders": nvenc_encoders,
            "qsv_encoders": qsv_encoders,
            "vaapi_encoders": vaapi_encoders,
            "all_hardware_encoders": amf_encoders + nvenc_encoders + qsv_encoders + vaapi_encoders
        }
        
    except Exception as e:
        return {"supported": False, "error": str(e)}

def get_gpu_encoder(quality_preset="720p", gpu_type="auto"):
    """根据画质预设和GPU类型选择合适的GPU编码器
    
    Args:
        quality_preset (str): 画质预设
        gpu_type (str): GPU类型 ("auto", "amd", "nvidia", "intel")
    
    Returns:
        str: 编码器名称，如果不支持则返回None
    """
    gpu_info = check_gpu_support()
    
    if not gpu_info["supported"]:
        return None
    
    # 根据画质预设选择编码器优先级
    if quality_preset in ["1080p", "720p"]:
        # 高质量优先使用HEVC
        encoders_priority = ["hevc_amf", "hevc_nvenc", "hevc_qsv", "hevc_vaapi", 
                           "h264_amf", "h264_nvenc", "h264_qsv", "h264_vaapi"]
    else:
        # 标准质量优先使用H.264
        encoders_priority = ["h264_amf", "h264_nvenc", "h264_qsv", "h264_vaapi",
                           "hevc_amf", "hevc_nvenc", "hevc_qsv", "hevc_vaapi"]
    
    # 根据GPU类型过滤编码器
    if gpu_type == "amd":
        available_encoders = gpu_info["amf_encoders"]
    elif gpu_type == "nvidia":
        available_encoders = gpu_info["nvenc_encoders"]
    elif gpu_type == "intel":
        available_encoders = gpu_info["qsv_encoders"]
    else:
        # auto模式，使用所有可用的硬件编码器
        available_encoders = gpu_info["all_hardware_encoders"]
    
    # 按优先级选择第一个可用的编码器
    for encoder in encoders_priority:
        if encoder in available_encoders:
            return encoder
    
    return None

def test_gpu_encoder(encoder_name):
    """测试GPU编码器是否可用
    
    Args:
        encoder_name (str): 编码器名称
    
    Returns:
        bool: 是否可用
    """
    try:
        ffmpeg_path, _ = check_ffmpeg()
        
        # 创建测试命令
        test_cmd = [
            ffmpeg_path, "-f", "lavfi", 
            "-i", "testsrc=duration=1:size=1280x720:rate=30",
            "-c:v", encoder_name,
            "-f", "null", "-", "-y"
        ]
        
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
        
    except Exception as e:
        print(f"测试GPU编码器 {encoder_name} 失败: {e}")
        return False

@mcp.tool()
async def check_gpu_acceleration() -> str:
    """检查GPU加速支持情况
    
    Returns:
        GPU加速支持信息
    """
    try:
        gpu_info = check_gpu_support()
        
        if not gpu_info["supported"]:
            return f"GPU加速不支持\n错误: {gpu_info.get('error', '未知错误')}"
        
        result = f"GPU加速支持情况:\n"
        result += f"显卡: {gpu_info['gpu_name']}\n"
        result += f"AMD AMF编码器: {', '.join(gpu_info['amf_encoders']) if gpu_info['amf_encoders'] else '无'}\n"
        result += f"NVIDIA NVENC编码器: {', '.join(gpu_info['nvenc_encoders']) if gpu_info['nvenc_encoders'] else '无'}\n"
        result += f"Intel QSV编码器: {', '.join(gpu_info['qsv_encoders']) if gpu_info['qsv_encoders'] else '无'}\n"
        result += f"VAAPI编码器: {', '.join(gpu_info['vaapi_encoders']) if gpu_info['vaapi_encoders'] else '无'}\n"
        
        # 测试推荐的编码器
        recommended_encoder = get_gpu_encoder("720p", "auto")
        if recommended_encoder:
            test_result = test_gpu_encoder(recommended_encoder)
            result += f"推荐编码器: {recommended_encoder} ({'可用' if test_result else '不可用'})\n"
        
        return result
        
    except Exception as e:
        return f"检查GPU加速失败: {str(e)}"

def get_mcp_instance():
    """获取MCP实例
    
    Returns:
        FastMCP: MCP实例
    """
    return mcp 