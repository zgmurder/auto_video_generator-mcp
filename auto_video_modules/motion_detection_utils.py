"""
运动检测工具模块
负责视频中静止片段和重复帧的检测与处理
"""

import cv2
import numpy as np
import os
import json
import asyncio
from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP

# 创建MCP实例
mcp = FastMCP("motion-detection-utils", log_level="ERROR")

class MotionDetectionConfig:
    """运动检测配置类"""
    def __init__(self, motion_threshold: float = 0.1, 
                 min_static_duration: float = 2.0, 
                 sample_step: int = 1):
        self.motion_threshold = motion_threshold
        self.min_static_duration = min_static_duration
        self.sample_step = sample_step

class StaticSegment:
    """静止片段数据类"""
    def __init__(self, start_time: float, end_time: float):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time

    def to_dict(self) -> Dict:
        return {
            "start": self.start_time,
            "end": self.end_time,
            "duration": self.duration
        }

    def to_timestamp(self) -> Dict:
        """转换为时间戳格式"""
        return {
            "start": self._seconds_to_timestamp(self.start_time),
            "end": self._seconds_to_timestamp(self.end_time)
        }

    @staticmethod
    def _seconds_to_timestamp(seconds: float) -> str:
        """将秒数转换为时间戳格式 HH:MM:SS.mmm"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds * 1000) % 1000)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

async def detect_static_segments_by_motion(
    video_path: str, 
    motion_threshold: float = 0.1, 
    min_static_duration: float = 2.0, 
    sample_step: int = 1
) -> List[StaticSegment]:
    """
    使用帧间像素差异检测视频中的静止片段
    
    Args:
        video_path: 视频文件路径
        motion_threshold: 运动阈值（像素差异）
        min_static_duration: 最小静止时长（秒）
        sample_step: 采样步长（帧数）
    
    Returns:
        静止片段列表
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")
    
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"[运动检测] 开始分析视频: {os.path.basename(video_path)}")
        print(f"[运动检测] 视频信息: {total_frames}帧, {fps:.2f}fps, {duration:.2f}秒")
        
        # 计算需要处理的帧数
        total_frames_to_process = total_frames // sample_step
        processed_frames = 0
        
        static_segments = []
        prev_gray = None
        static_start_time = None
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_step != 0:
                frame_idx += 1
                continue

            processed_frames += 1
            if processed_frames % 100 == 0:
                progress = (processed_frames / total_frames_to_process) * 100
                print(f"\r[运动检测] 分析进度: {progress:.1f}%", end="")

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            current_time = frame_idx / fps

            if prev_gray is not None:
                # 计算帧间差异
                diff = cv2.absdiff(prev_gray, gray)
                motion = np.mean(diff.astype(np.float32))
                
                if motion < motion_threshold:
                    # 检测到静止
                    if static_start_time is None:
                        static_start_time = current_time
                else:
                    # 检测到运动
                    if static_start_time is not None:
                        if current_time - static_start_time >= min_static_duration:
                            segment = StaticSegment(static_start_time, current_time)
                            static_segments.append(segment)
                        static_start_time = None
            
            prev_gray = gray
            frame_idx += 1
        
        # 处理最后一个静止片段
        if static_start_time is not None:
            if duration - static_start_time >= min_static_duration:
                segment = StaticSegment(static_start_time, duration)
                static_segments.append(segment)

        print(f"\r[运动检测] 分析完成! 发现 {len(static_segments)} 个静止片段")
        
        # 统计信息
        total_static_time = sum(seg.duration for seg in static_segments)
        cut_duration = duration - total_static_time
        print(f"[运动检测] 静止总时长: {total_static_time:.2f}秒")
        print(f"[运动检测] 剪辑后时长: {cut_duration:.2f}秒")
        print(f"[运动检测] 压缩比例: {(total_static_time/duration)*100:.1f}%")
        
        return static_segments
        
    finally:
        cap.release()

def to_timestamp(seconds: float) -> str:
    """
    将秒数转换为时间戳格式
    
    Args:
        seconds: 秒数
    
    Returns:
        时间戳字符串 (HH:MM:SS.mmm)
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds * 1000) % 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

async def optimize_motion_parameters(
    video_path: str, 
    target_duration_range: tuple = (50, 70),
    param_grid: Optional[Dict] = None
) -> Optional[MotionDetectionConfig]:
    """
    优化运动检测参数以达到目标时长
    
    Args:
        video_path: 视频文件路径
        target_duration_range: 目标时长范围 (min, max)
        param_grid: 参数网格，如果为None则使用默认值
    
    Returns:
        最优参数配置，如果未找到则返回None
    """
    from .video_utils import get_video_info
    
    video_info = get_video_info(video_path)
    duration = float(video_info.get("duration", 0))
    target_min, target_max = target_duration_range
    
    print(f"[参数优化] 视频总时长: {duration:.2f}秒")
    print(f"[参数优化] 目标区间: {target_min}s - {target_max}s")
    
    # 默认参数网格
    if param_grid is None:
        param_grid = {
            'motion_thresholds': [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5],
            'min_static_durations': [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
            'sample_steps': [1, 2, 3]
        }
    
    total_combinations = (
        len(param_grid['motion_thresholds']) * 
        len(param_grid['min_static_durations']) * 
        len(param_grid['sample_steps'])
    )
    current_combination = 0

    for mt in param_grid['motion_thresholds']:
        for msd in param_grid['min_static_durations']:
            for step in param_grid['sample_steps']:
                current_combination += 1
                print(f"[参数优化] 测试 {current_combination}/{total_combinations}: "
                      f"阈值={mt}, 时长={msd}s, 步长={step}")
                
                try:
                    static_segments = await detect_static_segments_by_motion(
                        video_path, mt, msd, step
                    )
                    static_total = sum(seg.duration for seg in static_segments)
                    cut_duration = duration - static_total
                    
                    print(f"[参数优化] 结果: {len(static_segments)}个片段, "
                          f"静止{static_total:.2f}s, 剪辑后{cut_duration:.2f}s")
                    
                    if target_min <= cut_duration <= target_max:
                        print(f"[参数优化] 找到合适参数!")
                        return MotionDetectionConfig(mt, msd, step)
                        
                except Exception as e:
                    print(f"[参数优化] 参数测试失败: {e}")
                    continue
    
    print("[参数优化] 未找到合适的参数组合")
    return None

def load_motion_config(config_path: str = "best_motion_clip_params.json") -> MotionDetectionConfig:
    """
    从配置文件加载运动检测参数
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        运动检测配置对象
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return MotionDetectionConfig(
                motion_threshold=config_data.get("motion_threshold", 0.1),
                min_static_duration=config_data.get("min_static_duration", 2.0),
                sample_step=config_data.get("sample_step", 1)
            )
        else:
            print(f"[配置] 配置文件不存在: {config_path}，使用默认参数")
            return MotionDetectionConfig()
            
    except Exception as e:
        print(f"[配置] 加载配置文件失败: {e}，使用默认参数")
        return MotionDetectionConfig()

def save_motion_config(config: MotionDetectionConfig, config_path: str = "best_motion_clip_params.json"):
    """
    保存运动检测参数到配置文件
    
    Args:
        config: 运动检测配置对象
        config_path: 配置文件路径
    """
    try:
        config_data = {
            "motion_threshold": config.motion_threshold,
            "min_static_duration": config.min_static_duration,
            "sample_step": config.sample_step
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"[配置] 参数已保存到: {config_path}")
        
    except Exception as e:
        print(f"[配置] 保存配置文件失败: {e}")

@mcp.tool()
async def detect_video_motion(video_path: str, config_path: str = "best_motion_clip_params.json") -> str:
    """
    检测视频中的运动片段
    
    Args:
        video_path: 视频文件路径
        config_path: 配置文件路径
    
    Returns:
        检测结果JSON字符串
    """
    try:
        config = load_motion_config(config_path)
        static_segments = await detect_static_segments_by_motion(
            video_path, 
            config.motion_threshold, 
            config.min_static_duration, 
            config.sample_step
        )
        
        # 转换为JSON格式
        result = {
            "video_path": video_path,
            "config": {
                "motion_threshold": config.motion_threshold,
                "min_static_duration": config.min_static_duration,
                "sample_step": config.sample_step
            },
            "static_segments": [seg.to_dict() for seg in static_segments],
            "timestamps": [seg.to_timestamp() for seg in static_segments],
            "summary": {
                "total_segments": len(static_segments),
                "total_static_time": sum(seg.duration for seg in static_segments),
                "average_segment_duration": sum(seg.duration for seg in static_segments) / len(static_segments) if static_segments else 0
            }
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

@mcp.tool()
async def optimize_video_motion_params(
    video_path: str, 
    target_min_duration: float = 50.0, 
    target_max_duration: float = 70.0
) -> str:
    """
    优化视频运动检测参数
    
    Args:
        video_path: 视频文件路径
        target_min_duration: 目标最小时长
        target_max_duration: 目标最大时长
    
    Returns:
        优化结果JSON字符串
    """
    try:
        optimal_config = await optimize_motion_parameters(
            video_path, 
            (target_min_duration, target_max_duration)
        )
        
        if optimal_config:
            # 保存最优参数
            save_motion_config(optimal_config)
            
            result = {
                "success": True,
                "optimal_config": {
                    "motion_threshold": optimal_config.motion_threshold,
                    "min_static_duration": optimal_config.min_static_duration,
                    "sample_step": optimal_config.sample_step
                },
                "message": "找到最优参数并已保存到配置文件"
            }
        else:
            result = {
                "success": False,
                "message": "未找到合适的参数组合"
            }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

def get_mcp_instance():
    """获取MCP实例"""
    return mcp 