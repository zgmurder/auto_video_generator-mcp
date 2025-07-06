import cv2
import numpy as np
from tqdm import tqdm
from dataclasses import dataclass, field
from typing import Tuple, List, Dict
import asyncio

@dataclass
class DuplicateFrameConfig:
    """
    Configuration for detecting and removing duplicate/static frames.
    """
    method: str = 'hist'  # 'ssim', 'mse', 'hist'
    similarity_threshold: float = 0.98
    resize_for_comparison: bool = True
    comparison_size: Tuple[int, int] = (32, 32)
    min_segment_duration: float = 0.5 # Minimum duration in seconds for a segment to be considered


class DuplicateFrameRemover:
    def __init__(self, config: DuplicateFrameConfig):
        self.config = config

    def _calculate_ssim(self, frame1, frame2):
        # Implementation for SSIM
        # (For simplicity, this is a placeholder. A real implementation would use scikit-image)
        return np.corrcoef(frame1.flatten(), frame2.flatten())[0, 1]

    def _calculate_mse(self, frame1, frame2):
        err = np.sum((frame1.astype("float") - frame2.astype("float")) ** 2)
        err /= float(frame1.shape[0] * frame1.shape[1])
        return 1 - (err / (255*255)) # Normalize to a similarity score

    def _calculate_hist_similarity(self, frame1, frame2):
        hist1 = cv2.calcHist([frame1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([frame2], [0], None, [256], [0, 256])
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    async def detect_duplicate_segments(self, video_path: str) -> List[Dict[str, float]]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video file {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        segments = []
        last_frame = None
        start_frame = 0
        is_duplicate_sequence = False

        pbar = tqdm(total=total_frames, desc="Detecting Duplicate Segments")
        
        ret, frame = cap.read()
        frame_count = 0
        while ret:
            pbar.update(1)
            frame_count += 1

            if self.config.resize_for_comparison:
                current_frame_processed = cv2.resize(frame, self.config.comparison_size)
            else:
                current_frame_processed = frame
            
            if len(current_frame_processed.shape) == 3:
                 current_frame_processed = cv2.cvtColor(current_frame_processed, cv2.COLOR_BGR2GRAY)


            if last_frame is not None:
                if self.config.method == 'ssim':
                    similarity = self._calculate_ssim(last_frame, current_frame_processed)
                elif self.config.method == 'mse':
                    similarity = self._calculate_mse(last_frame, current_frame_processed)
                else: # hist
                    similarity = self._calculate_hist_similarity(last_frame, current_frame_processed)

                if similarity > self.config.similarity_threshold:
                    if not is_duplicate_sequence:
                        start_frame = frame_count - 1
                        is_duplicate_sequence = True
                else:
                    if is_duplicate_sequence:
                        end_frame = frame_count - 1
                        duration = (end_frame - start_frame) / fps
                        if duration >= self.config.min_segment_duration:
                            segments.append({"start": start_frame / fps, "end": end_frame / fps})
                        is_duplicate_sequence = False
            
            last_frame = current_frame_processed
            ret, frame = cap.read()
            await asyncio.sleep(0) # Yield control to allow UI updates

        if is_duplicate_sequence: # Handle case where video ends in a duplicate sequence
            end_frame = total_frames -1
            duration = (end_frame - start_frame) / fps
            if duration >= self.config.min_segment_duration:
                segments.append({"start": start_frame / fps, "end": end_frame / fps})

        pbar.close()
        cap.release()
        return segments 