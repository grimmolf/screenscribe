"""Video processing module for screenscribe."""

import cv2
import subprocess
import json
from pathlib import Path
from typing import List, Tuple
import numpy as np
from PIL import Image
import logging
import re

from .models import FrameData

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video frame extraction and scene detection."""
    
    def __init__(
        self, 
        sampling_mode: str = "scene", 
        interval: float = 5.0,
        scene_threshold: float = 0.3,
        thumbnail_width: int = 320
    ):
        self.sampling_mode = sampling_mode
        self.interval = interval
        self.scene_threshold = scene_threshold
        self.thumbnail_width = thumbnail_width
        
        logger.info(f"VideoProcessor initialized: mode={sampling_mode}, interval={interval}s, threshold={scene_threshold}")
    
    def extract_frames_scene(self, video_path: Path, output_dir: Path) -> List[FrameData]:
        """Extract frames using scene detection."""
        logger.info(f"Extracting frames using scene detection from: {video_path}")
        
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        # Two-pass approach: detect scenes, then extract full resolution frames
        
        # Pass 1: Detect scene timestamps using scaled-down video for performance
        logger.info("Pass 1: Detecting scene changes...")
        detect_cmd = [
            "ffmpeg", "-i", str(video_path),
            "-vf", f"scale=640:-1,select='gt(scene,{self.scene_threshold})',metadata=print",
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(detect_cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Scene detection failed: {e.stderr}")
        
        # Parse timestamps from metadata
        timestamps = []
        for line in result.stderr.split('\n'):
            if "pts_time:" in line:
                # Extract timestamp using regex for robustness
                match = re.search(r'pts_time:([\d.]+)', line)
                if match:
                    ts = float(match.group(1))
                    timestamps.append(ts)
        
        if not timestamps:
            logger.warning("No scene changes detected, falling back to first frame")
            timestamps = [0.0]
        
        logger.info(f"Found {len(timestamps)} scene changes")
        
        # Pass 2: Extract full resolution frames at detected timestamps
        logger.info("Pass 2: Extracting full resolution frames...")
        frames = []
        
        for i, ts in enumerate(timestamps):
            frame_path = frames_dir / f"frame_{i:04d}.jpg"
            
            # Seek before input for better performance
            extract_cmd = [
                "ffmpeg", "-ss", str(ts), "-i", str(video_path),
                "-vframes", "1", "-q:v", "2",  # High quality JPEG
                str(frame_path), "-y"
            ]
            
            try:
                subprocess.run(extract_cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to extract frame at {ts}s: {e}")
                continue
            
            # Create thumbnail
            thumbnail_path = self._create_thumbnail(frame_path, output_dir)
            
            frames.append(FrameData(
                index=i,
                timestamp=ts,
                frame_path=frame_path,
                thumbnail_path=thumbnail_path,
                is_scene_change=True
            ))
        
        logger.info(f"Successfully extracted {len(frames)} frames")
        return frames
    
    def extract_frames_interval(self, video_path: Path, output_dir: Path) -> List[FrameData]:
        """Extract frames at regular intervals."""
        logger.info(f"Extracting frames at {self.interval}s intervals from: {video_path}")
        
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        # Open video with OpenCV
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            logger.info(f"Video info: {fps:.2f} fps, {total_frames} frames, {duration:.2f}s duration")
            
            frames = []
            frame_interval = int(fps * self.interval)
            
            for i in range(0, total_frames, frame_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning(f"Failed to read frame at position {i}")
                    break
                
                timestamp = i / fps
                frame_index = len(frames)
                frame_path = frames_dir / f"frame_{frame_index:04d}.jpg"
                
                # Save frame
                success = cv2.imwrite(str(frame_path), frame)
                if not success:
                    logger.warning(f"Failed to save frame at {timestamp}s")
                    continue
                
                # Create thumbnail
                thumbnail_path = self._create_thumbnail(frame_path, output_dir)
                
                frames.append(FrameData(
                    index=frame_index,
                    timestamp=timestamp,
                    frame_path=frame_path,
                    thumbnail_path=thumbnail_path,
                    is_scene_change=False
                ))
                
                logger.debug(f"Extracted frame {frame_index} at {timestamp:.2f}s")
        
        finally:
            cap.release()
        
        logger.info(f"Successfully extracted {len(frames)} frames")
        return frames
    
    def _create_thumbnail(self, frame_path: Path, output_dir: Path) -> Path:
        """Create thumbnail with fixed width maintaining aspect ratio."""
        thumb_dir = output_dir / "thumbnails"
        thumb_dir.mkdir(exist_ok=True)
        
        thumb_path = thumb_dir / f"thumb_{frame_path.stem}.jpg"
        
        try:
            # Open image with Pillow
            with Image.open(frame_path) as img:
                # Calculate height to maintain aspect ratio
                width = self.thumbnail_width
                height = int((width / img.width) * img.height)
                
                # Resize using high-quality resampling
                img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Save with optimization
                img_resized.save(thumb_path, "JPEG", quality=85, optimize=True)
                
                logger.debug(f"Created thumbnail: {thumb_path} ({width}x{height})")
                
        except Exception as e:
            logger.error(f"Failed to create thumbnail for {frame_path}: {e}")
            # Create a placeholder thumbnail
            thumb_path = self._create_placeholder_thumbnail(thumb_dir, frame_path.stem)
        
        return thumb_path
    
    def _create_placeholder_thumbnail(self, thumb_dir: Path, stem: str) -> Path:
        """Create a placeholder thumbnail when image processing fails."""
        thumb_path = thumb_dir / f"thumb_{stem}.jpg"
        
        # Create a simple placeholder image
        placeholder = Image.new('RGB', (self.thumbnail_width, int(self.thumbnail_width * 0.75)), color='gray')
        placeholder.save(thumb_path, "JPEG", quality=85)
        
        logger.warning(f"Created placeholder thumbnail: {thumb_path}")
        return thumb_path
    
    def get_processing_info(self) -> dict:
        """Get information about the video processor configuration."""
        return {
            "sampling_mode": self.sampling_mode,
            "interval": self.interval,
            "scene_threshold": self.scene_threshold,
            "thumbnail_width": self.thumbnail_width
        }