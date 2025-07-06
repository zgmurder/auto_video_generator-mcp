import cv2
import numpy as np
import os
import json
import asyncio
from auto_generate_video_mcp_modular import generate_auto_video
from auto_video_modules.video_utils import get_video_info

async def detect_static_segments_by_motion(video_path, motion_threshold=2.0, min_static_duration=1.0, sample_step=1):
    """
    用帧间像素差检测静止片段。
    返回：静止片段列表 [{"start": 秒, "end": 秒}]
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    
    # 简单的进度条
    total_frames_to_process = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) // sample_step
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
            print(f"\r  -> Analyzing... {progress:.1f}%", end="")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        current_time = frame_idx / fps

        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            motion = np.mean(diff.astype(np.float32))
            
            if motion < motion_threshold:
                if static_start_time is None:
                    static_start_time = current_time
            else:
                if static_start_time is not None:
                    if current_time - static_start_time >= min_static_duration:
                        static_segments.append({"start": static_start_time, "end": current_time})
                    static_start_time = None
        
        prev_gray = gray
        frame_idx += 1
        
    if static_start_time is not None:
        if duration - static_start_time >= min_static_duration:
            static_segments.append({"start": static_start_time, "end": duration})

    cap.release()
    print("\r  -> Analysis complete.      ")
    return static_segments

def to_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds * 1000) % 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

async def try_low_motion_params(video_path, target_min=53, target_max=64):
    video_info = get_video_info(video_path)
    duration = float(video_info.get("duration", 0))
    print(f"视频总时长: {duration:.2f}s, 目标区间: {target_min}s - {target_max}s")
    
    param_grid = {
        'motion_thresholds': [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45],
        'min_static_durations': [0.5, 1.0, 2.0],
        'sample_steps': [1, 2]
    }
    
    total_combinations = len(param_grid['motion_thresholds']) * len(param_grid['min_static_durations']) * len(param_grid['sample_steps'])
    current_combination = 0

    for mt in param_grid['motion_thresholds']:
        for msd in param_grid['min_static_durations']:
            for step in param_grid['sample_steps']:
                current_combination += 1
                print("-" * 50)
                print(f"Combination {current_combination}/{total_combinations}: motion_threshold={mt}, min_static_duration={msd}, sample_step={step}")
                
                static_segments = await detect_static_segments_by_motion(video_path, mt, msd, step)
                static_total = sum(seg['end']-seg['start'] for seg in static_segments)
                cut_duration = duration - static_total
                
                print(f"  Result: Found {len(static_segments)} static segments. Total static time: {static_total:.2f}s. Final Cut Duration: {cut_duration:.2f}s")
                
                if target_min <= cut_duration <= target_max:
                    print(f"  [HIT!] Duration is in the target range. Starting video generation...")
                    
                    segments_json = json.dumps([{"start": to_timestamp(s["start"]), "end": to_timestamp(s["end"])} for s in static_segments])
                    
                    output_cut = f"motion_cut_{cut_duration:.1f}s_mt{mt}_msd{msd}_step{step}.mp4"
                    output_keep = f"motion_keep_{static_total:.1f}s_mt{mt}_msd{msd}_step{step}.mp4"
                    
                    print(f"  Generating 'cut' video: {output_cut}")
                    await generate_auto_video(video_path=video_path, output_path=output_cut, segments=segments_json, segments_mode="cut")
                    
                    print(f"  Generating 'keep' video: {output_keep}")
                    await generate_auto_video(video_path=video_path, output_path=output_keep, segments=segments_json, segments_mode="keep")
                    
                    print(f"  Successfully generated videos. Mission accomplished.")
                    return True # Stop after the first hit
    
    print("-" * 50)
    print("Search finished. No parameter combination hit the target duration range.")
    return False

if __name__ == "__main__":
    video_path = "test.mp4"
    if not os.path.exists(video_path):
        print("ERROR: 'test.mp4' not found.")
    else:
        asyncio.run(try_low_motion_params(video_path)) 