"""
极致GPU优化工具模块
将显卡性能发挥到最大，提供最快的视频处理速度
"""

import os
import subprocess
import threading
import multiprocessing
import psutil
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP

# 创建MCP实例
mcp = FastMCP("gpu-optimization-utils", log_level="ERROR")

@dataclass
class GPUOptimizationConfig:
    """GPU优化配置"""
    # 编码器设置
    encoder: str = "hevc_amf"
    preset: str = "speed"  # speed, balanced, quality
    quality: int = 18  # 0-51, 越小质量越好
    bitrate: str = "auto"
    
    # 多线程设置
    threads: int = 0  # 0=自动检测
    thread_type: str = "frame"  # frame, slice
    
    # 内存优化
    buffer_size: int = 1024  # MB
    max_muxing_queue_size: int = 1024
    
    # 性能调优
    gpu: int = 0  # GPU设备ID
    async_depth: int = 4  # 异步处理深度
    low_power: bool = False  # 低功耗模式
    
    # 高级设置
    bframes: int = 3  # B帧数量
    ref_frames: int = 4  # 参考帧数量
    gop_size: int = 30  # GOP大小
    keyint_min: int = 15  # 最小关键帧间隔
    
    # 缓存设置
    enable_cache: bool = True
    cache_dir: str = "temp_cache"
    cache_size: int = 2048  # MB

class GPUOptimizer:
    """GPU性能优化器"""
    
    def __init__(self):
        self.config = GPUOptimizationConfig()
        self.system_info = self._get_system_info()
        self._optimize_system_settings()
    
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        try:
            # CPU信息
            cpu_count = multiprocessing.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # 内存信息
            memory = psutil.virtual_memory()
            
            # GPU信息
            gpu_info = self._get_gpu_info()
            
            return {
                "cpu": {
                    "count": cpu_count,
                    "frequency": cpu_freq.current if cpu_freq else "未知",
                    "usage": psutil.cpu_percent(interval=1)
                },
                "memory": {
                    "total": memory.total // (1024**3),  # GB
                    "available": memory.available // (1024**3),  # GB
                    "usage": memory.percent
                },
                "gpu": gpu_info
            }
        except Exception as e:
            print(f"获取系统信息失败: {e}")
            return {}
    
    def _get_gpu_info(self) -> Dict:
        """获取GPU详细信息"""
        try:
            # 使用wmic获取GPU信息
            result = subprocess.run([
                "wmic", "path", "win32_VideoController", 
                "get", "name,adapterram,driverversion"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].strip().split()
                    if len(parts) >= 2:
                        return {
                            "name": parts[0],
                            "memory": int(parts[1]) // (1024**3) if parts[1].isdigit() else "未知",
                            "driver": parts[2] if len(parts) > 2 else "未知"
                        }
            
            return {"name": "未知", "memory": "未知", "driver": "未知"}
        except Exception as e:
            print(f"获取GPU信息失败: {e}")
            return {"name": "未知", "memory": "未知", "driver": "未知"}
    
    def _optimize_system_settings(self):
        """优化系统设置"""
        try:
            # 设置进程优先级
            current_process = psutil.Process()
            current_process.nice(psutil.HIGH_PRIORITY_CLASS)
            
            # 设置线程优先级
            current_process.cpu_affinity(list(range(multiprocessing.cpu_count())))
            
            print("[GPU优化] 系统设置已优化")
        except Exception as e:
            print(f"[GPU优化] 系统设置优化失败: {e}")
    
    def auto_optimize_config(self, video_path: str, target_quality: str = "720p") -> GPUOptimizationConfig:
        """根据系统配置自动优化参数"""
        config = GPUOptimizationConfig()
        
        # 根据CPU核心数优化线程数
        cpu_count = self.system_info.get("cpu", {}).get("count", 4)
        config.threads = min(cpu_count * 2, 16)  # 最多16线程
        
        # 根据内存大小优化缓冲区
        memory_gb = self.system_info.get("memory", {}).get("total", 8)
        config.buffer_size = min(memory_gb * 128, 2048)  # 每GB内存128MB缓冲区，最大2GB
        
        # 根据GPU类型优化编码器
        gpu_name = self.system_info.get("gpu", {}).get("name", "").lower()
        if "radeon" in gpu_name or "amd" in gpu_name:
            config.encoder = "hevc_amf"
            config.async_depth = 6  # AMD GPU支持更高的异步深度
        elif "nvidia" in gpu_name or "geforce" in gpu_name:
            config.encoder = "hevc_nvenc"
            config.async_depth = 4
        elif "intel" in gpu_name:
            config.encoder = "hevc_qsv"
            config.async_depth = 3
        else:
            config.encoder = "hevc_amf"  # 默认使用AMD编码器
        
        # 根据画质预设优化参数
        if target_quality == "1080p":
            config.quality = 20
            config.bframes = 4
            config.ref_frames = 6
        elif target_quality == "720p":
            config.quality = 18
            config.bframes = 3
            config.ref_frames = 4
        else:  # 480p及以下
            config.quality = 16
            config.bframes = 2
            config.ref_frames = 3
        
        # 根据内存使用情况调整缓存
        memory_usage = self.system_info.get("memory", {}).get("usage", 50)
        if memory_usage < 70:
            config.enable_cache = True
            config.cache_size = min(memory_gb * 256, 4096)  # 每GB内存256MB缓存
        else:
            config.enable_cache = False
        
        return config
    
    def build_optimized_ffmpeg_command(self, 
                                     input_path: str, 
                                     output_path: str, 
                                     config: GPUOptimizationConfig,
                                     additional_params: Optional[Dict] = None) -> List[str]:
        """构建优化的FFmpeg命令"""
        
        # 基础命令
        cmd = ["ffmpeg", "-y"]  # -y 覆盖输出文件
        
        # 输入设置
        cmd.extend(["-i", input_path])
        
        # 视频编码器设置
        cmd.extend(["-c:v", config.encoder])
        
        # 编码器特定参数
        if "amf" in config.encoder:
            cmd.extend([
                "-quality", config.preset,
                "-rc", "vbr_peak",  # 可变比特率峰值模式
                "-qp_i", str(config.quality),
                "-qp_p", str(config.quality + 2),
                "-qp_b", str(config.quality + 4),
                "-bf", str(config.bframes),
                "-refs", str(config.ref_frames),
                "-g", str(config.gop_size),
                "-keyint_min", str(config.keyint_min),
                "-async_depth", str(config.async_depth),
                "-gpu", str(config.gpu)
            ])
            
            if config.low_power:
                cmd.append("-low_power")
                
        elif "nvenc" in config.encoder:
            cmd.extend([
                "-preset", config.preset,
                "-rc", "vbr",
                "-cq", str(config.quality),
                "-bf", str(config.bframes),
                "-refs", str(config.ref_frames),
                "-g", str(config.gop_size),
                "-keyint_min", str(config.keyint_min),
                "-gpu", str(config.gpu)
            ])
            
        elif "qsv" in config.encoder:
            cmd.extend([
                "-preset", config.preset,
                "-global_quality", str(config.quality),
                "-bf", str(config.bframes),
                "-refs", str(config.ref_frames),
                "-g", str(config.gop_size),
                "-keyint_min", str(config.keyint_min),
                "-async_depth", str(config.async_depth)
            ])
        
        # 多线程设置
        if config.threads > 0:
            cmd.extend(["-threads", str(config.threads)])
        
        # 内存优化
        cmd.extend([
            "-bufsize", f"{config.buffer_size}M",
            "-max_muxing_queue_size", str(config.max_muxing_queue_size)
        ])
        
        # 缓存设置
        if config.enable_cache:
            if not os.path.exists(config.cache_dir):
                os.makedirs(config.cache_dir)
            cmd.extend(["-cache_dir", config.cache_dir])
        
        # 输出设置
        cmd.extend(["-c:a", "copy"])  # 复制音频流
        
        # 添加额外参数
        if additional_params is not None:
            for key, value in additional_params.items():
                if isinstance(value, bool):
                    if value:
                        cmd.append(f"-{key}")
                else:
                    cmd.extend([f"-{key}", str(value)])
        
        cmd.append(output_path)
        
        return cmd
    
    def monitor_performance(self, process: subprocess.Popen) -> Dict:
        """监控处理性能"""
        performance_data = {
            "cpu_usage": [],
            "memory_usage": [],
            "gpu_usage": [],
            "processing_speed": []
        }
        
        start_time = time.time()
        
        while process.poll() is None:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                performance_data["cpu_usage"].append(cpu_percent)
                
                # 内存使用率
                memory_percent = psutil.virtual_memory().percent
                performance_data["memory_usage"].append(memory_percent)
                
                # 处理速度（每秒处理的帧数）
                elapsed = time.time() - start_time
                if elapsed > 0:
                    # 这里需要根据实际处理的帧数来计算
                    pass
                
                time.sleep(1)
                
            except Exception as e:
                print(f"性能监控错误: {e}")
                break
        
        return performance_data

def create_optimized_video_processor() -> GPUOptimizer:
    """创建优化的视频处理器"""
    return GPUOptimizer()

@mcp.tool()
async def get_system_performance_info() -> str:
    """获取系统性能信息"""
    try:
        optimizer = GPUOptimizer()
        info = optimizer.system_info
        
        result = "=== 系统性能信息 ===\n"
        result += f"CPU: {info['cpu']['count']}核心, {info['cpu']['frequency']}MHz, 使用率: {info['cpu']['usage']}%\n"
        result += f"内存: {info['memory']['total']}GB总容量, {info['memory']['available']}GB可用, 使用率: {info['memory']['usage']}%\n"
        result += f"GPU: {info['gpu']['name']}, {info['gpu']['memory']}GB显存, 驱动: {info['gpu']['driver']}\n"
        
        return result
    except Exception as e:
        return f"获取系统性能信息失败: {str(e)}"

@mcp.tool()
async def optimize_video_processing(video_path: str, target_quality: str = "720p") -> str:
    """优化视频处理参数"""
    try:
        optimizer = GPUOptimizer()
        config = optimizer.auto_optimize_config(video_path, target_quality)
        
        result = "=== 视频处理优化配置 ===\n"
        result += f"编码器: {config.encoder}\n"
        result += f"预设: {config.preset}\n"
        result += f"质量: {config.quality}\n"
        result += f"线程数: {config.threads}\n"
        result += f"缓冲区: {config.buffer_size}MB\n"
        result += f"异步深度: {config.async_depth}\n"
        result += f"B帧数: {config.bframes}\n"
        result += f"参考帧: {config.ref_frames}\n"
        result += f"GOP大小: {config.gop_size}\n"
        result += f"启用缓存: {config.enable_cache}\n"
        if config.enable_cache:
            result += f"缓存大小: {config.cache_size}MB\n"
        
        return result
    except Exception as e:
        return f"优化视频处理失败: {str(e)}"

@mcp.tool()
async def benchmark_gpu_performance() -> str:
    """GPU性能基准测试"""
    try:
        import time
        
        optimizer = GPUOptimizer()
        config = optimizer.auto_optimize_config("test", "720p")
        
        # 创建测试视频
        test_input = "temp_benchmark_input.mp4"
        test_output = "temp_benchmark_output.mp4"
        
        # 生成测试视频
        test_cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "testsrc=duration=10:size=1280x720:rate=30",
            "-c:v", "libx264", "-preset", "ultrafast",
            test_input
        ]
        
        print("生成测试视频...")
        subprocess.run(test_cmd, capture_output=True, timeout=30)
        
        if not os.path.exists(test_input):
            return "无法生成测试视频"
        
        # 构建优化命令
        optimized_cmd = optimizer.build_optimized_ffmpeg_command(
            test_input, test_output, config
        )
        
        print("开始性能测试...")
        start_time = time.time()
        
        process = subprocess.Popen(optimized_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 清理测试文件
        for file in [test_input, test_output]:
            if os.path.exists(file):
                os.remove(file)
        
        if process.returncode == 0:
            result = f"=== GPU性能基准测试结果 ===\n"
            result += f"处理时间: {processing_time:.2f}秒\n"
            result += f"平均速度: {10/processing_time:.2f}倍速\n"
            result += f"编码器: {config.encoder}\n"
            result += f"线程数: {config.threads}\n"
            result += f"异步深度: {config.async_depth}\n"
            
            # 性能评级
            if processing_time < 5:
                result += "性能评级: 极佳 ⭐⭐⭐⭐⭐"
            elif processing_time < 8:
                result += "性能评级: 优秀 ⭐⭐⭐⭐"
            elif processing_time < 12:
                result += "性能评级: 良好 ⭐⭐⭐"
            else:
                result += "性能评级: 一般 ⭐⭐"
            
            return result
        else:
            return "性能测试失败"
            
    except Exception as e:
        return f"GPU性能基准测试失败: {str(e)}"

def get_mcp_instance():
    """获取MCP实例"""
    return mcp 