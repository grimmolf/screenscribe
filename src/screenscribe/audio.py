"""Audio processing module for screenscribe."""

from faster_whisper import WhisperModel
from pathlib import Path
import subprocess
import tempfile
import signal
import sys
import shutil
import json
import threading
import time
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.console import Console
import logging
from typing import Dict, Any, Optional, List, Tuple

from .config import config

logger = logging.getLogger(__name__)
console = Console()

# Global flag for graceful shutdown
_shutdown_requested = False
_original_handler = None

def _signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) gracefully."""
    global _shutdown_requested, _original_handler
    
    if _shutdown_requested:
        # Second ctrl+c - force quit immediately
        console.print("\n🛑 Force quit! Restoring original handler...", style="red")
        signal.signal(signal.SIGINT, _original_handler)
        if _original_handler:
            _original_handler(signum, frame)
        else:
            sys.exit(1)
    else:
        # First ctrl+c - request graceful shutdown
        _shutdown_requested = True
        console.print("\n⏸️  Graceful shutdown requested. Press Ctrl+C again to force quit.", style="yellow")

# Register signal handler and save original
_original_handler = signal.signal(signal.SIGINT, _signal_handler)


def _get_optimal_device() -> tuple[str, str]:
    """Determine the optimal device and compute type for faster-whisper."""
    try:
        import torch
        import platform
        
        machine = platform.machine().lower()
        
        # For Apple Silicon, try different device configurations
        if 'arm64' in machine or 'aarch64' in machine:
            console.print("🍎 Apple Silicon detected - optimizing for M3 Ultra", style="blue")
            
            # Check if we can use Metal Performance Shaders
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                console.print("🚀 Metal Performance Shaders detected - attempting GPU acceleration", style="green")
                # Try mps device first for Apple Silicon GPU acceleration
                return "mps", "float16"
            else:
                console.print("⚡ Using CPU with optimized threading for Apple Silicon", style="yellow")
                return "cpu", "int8"
        
        # Check for NVIDIA CUDA
        elif torch.cuda.is_available():
            return "cuda", "float16"
            
        # Fall back to CPU
        else:
            return "cpu", "int8"
            
    except ImportError:
        # If torch isn't available, assume CPU for Apple Silicon
        import platform
        machine = platform.machine().lower()
        if 'arm64' in machine or 'aarch64' in machine:
            console.print("🍎 Apple Silicon detected (no torch) - using optimized CPU", style="blue")
            return "cpu", "int8"
        return "cpu", "int8"


class AudioProcessor:
    """Handles audio extraction and transcription using faster-whisper."""
    
    def __init__(self, model_name: str = "medium"):
        self.model_name = model_name
        # Get optimal device and compute type for this system
        self.device, self.compute_type = _get_optimal_device()
        self.model: Optional[WhisperModel] = None
        
        device_info = {
            "mps": "Apple Silicon GPU (Metal)",
            "cuda": "NVIDIA GPU", 
            "cpu": "CPU (Apple Silicon Optimized)" if self.device == "cpu" and self.compute_type == "int8" else "CPU"
        }.get(self.device, self.device)
        
        logger.info(f"Initializing AudioProcessor with model '{model_name}' on {device_info} ({self.compute_type})")
        self._checkpoint_file: Optional[Path] = None
    
    def _load_model(self) -> None:
        """Load faster-whisper model with error handling."""
        if self.model is not None:
            return
        
        try:
            logger.info(f"Loading faster-whisper model: {self.model_name}")
            
            # Apple Silicon optimizations
            cpu_threads = None
            if self.device == "cpu":
                import os
                import platform
                
                total_cores = os.cpu_count() or 4
                machine = platform.machine().lower()
                
                if 'arm64' in machine or 'aarch64' in machine:
                    # Apple Silicon: Use most cores but leave some headroom
                    # M3 Ultra has 28 cores, M3 Max has 16, M3 Pro has 12, M3 has 8
                    cpu_threads = max(4, int(total_cores * 0.85))  # Use 85% of cores
                    logger.info(f"Apple Silicon detected: Using {cpu_threads}/{total_cores} CPU threads")
                else:
                    # Intel or other architectures
                    cpu_threads = min(8, total_cores)
                    logger.info(f"Using {cpu_threads}/{total_cores} CPU threads")
            
            self.model = WhisperModel(
                self.model_name, 
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=cpu_threads,
                download_root=str(config.whisper_cache_dir) if hasattr(config, 'whisper_cache_dir') else None
            )
        except Exception as e:
            if "out of memory" in str(e).lower() and (self.device == "cuda" or self.device == "mps"):
                logger.warning(f"GPU out of memory on {self.device}, falling back to CPU")
                self.device = "cpu" 
                self.compute_type = "int8"
                self.model = WhisperModel(
                    self.model_name, 
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=max(4, int((os.cpu_count() or 4) * 0.85)),
                    download_root=str(config.whisper_cache_dir) if hasattr(config, 'whisper_cache_dir') else None
                )
            elif "incompatible constructor arguments" in str(e) or "device" in str(e).lower():
                # MPS or other device not supported, fall back to CPU
                logger.warning(f"Device '{self.device}' not supported by faster-whisper, falling back to CPU")
                self.device = "cpu"
                self.compute_type = "int8"
                
                import os
                cpu_threads = max(4, int((os.cpu_count() or 4) * 0.85))
                
                self.model = WhisperModel(
                    self.model_name, 
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=cpu_threads,
                    download_root=str(config.whisper_cache_dir) if hasattr(config, 'whisper_cache_dir') else None
                )
                logger.info(f"Successfully loaded model on CPU with {cpu_threads} threads")
            else:
                raise RuntimeError(f"Failed to load faster-whisper model: {e}")
    
    def _check_nas_performance(self, file_path: Path) -> bool:
        """Check if file is on slow network storage and should be copied locally."""
        try:
            # Check if path indicates network storage
            path_str = str(file_path).lower()
            if any(indicator in path_str for indicator in ['/volumes/', '/mnt/', 'nfs', 'smb', 'cifs']):
                console.print(f"🔍 Detected network storage path: {file_path}", style="yellow")
                return True
                
            # Quick read test - if it takes >1 second to read 1MB, copy locally
            import time
            start = time.time()
            with open(file_path, 'rb') as f:
                f.read(1024 * 1024)  # Read 1MB
            read_time = time.time() - start
            
            # If reading 1MB takes >1 second, network is slow
            if read_time > 1.0:
                console.print(f"🐌 Slow storage detected ({read_time:.1f}s for 1MB)", style="yellow")
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Could not test storage performance: {e}")
            return False
    
    def _copy_to_local(self, remote_path: Path) -> Path:
        """Copy file from NAS to local temporary directory."""
        temp_dir = Path(tempfile.gettempdir()) / "screenscribe_temp"
        temp_dir.mkdir(exist_ok=True)
        
        local_path = temp_dir / remote_path.name
        
        console.print(f"📥 Copying {remote_path.name} from network storage to local temp for better performance...")
        
        # Copy with progress tracking
        file_size = remote_path.stat().st_size
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            copy_task = progress.add_task(f"Copying {remote_path.name}...", total=100)
            
            copied = 0
            with open(remote_path, 'rb') as src, open(local_path, 'wb') as dst:
                while chunk := src.read(1024 * 1024):  # 1MB chunks
                    if _shutdown_requested:
                        raise KeyboardInterrupt("Copy interrupted by user")
                        
                    dst.write(chunk)
                    copied += len(chunk)
                    progress.update(copy_task, completed=int(copied / file_size * 100))
        
        logger.info(f"File copied to local storage: {local_path}")
        return local_path
    
    async def extract_audio(self, video_path: Path, copy_from_nas: bool = True) -> Path:
        """Extract audio track from video file."""
        logger.info(f"Extracting audio from: {video_path}")
        
        # Check if file should be copied locally for performance
        working_video_path = video_path
        copied_locally = False
        
        if copy_from_nas and self._check_nas_performance(video_path):
            try:
                working_video_path = self._copy_to_local(video_path)
                copied_locally = True
            except KeyboardInterrupt:
                console.print("\n❌ File copy interrupted", style="red")
                raise
        
        # Create temporary audio file
        audio_path = Path(tempfile.mktemp(suffix=".wav"))
        
        # Check if video has audio stream first
        probe_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_type", "-of", "csv=p=0",
            str(working_video_path)
        ]
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            if not result.stdout.strip():
                raise ValueError("Video has no audio stream")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to probe video for audio: {e}")
        
        # Extract audio using ffmpeg
        cmd = [
            "ffmpeg", "-i", str(working_video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # WAV format
            "-ar", "16000",  # 16kHz for Whisper
            "-ac", "1",  # Mono
            str(audio_path),
            "-y"  # Overwrite
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Audio extracted to: {audio_path}")
            
            # Clean up copied file after successful extraction
            if copied_locally and working_video_path != video_path:
                working_video_path.unlink(missing_ok=True)
                logger.info("Cleaned up temporary video copy")
            
            return audio_path
        except subprocess.CalledProcessError as e:
            # Clean up copied file if extraction fails
            if copied_locally and working_video_path != video_path:
                working_video_path.unlink(missing_ok=True)
            raise RuntimeError(f"Failed to extract audio: {e.stderr}")
    
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio file using faster-whisper."""
        logger.info(f"Transcribing audio: {audio_path}")
        
        self._load_model()
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("Transcribing audio...", total=100)
            
            try:
                # Check for interruption before starting transcription
                if _shutdown_requested:
                    raise KeyboardInterrupt("Transcription interrupted before starting")
                
                # faster-whisper returns segments and info separately
                segments, info = self.model.transcribe(
                    str(audio_path),
                    language=language,
                    word_timestamps=True,
                    vad_filter=True,  # Voice activity detection
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                
                progress.update(task, completed=30)
                
                # Convert segments to list and format similar to openai-whisper
                segment_list = []
                segment_count = 0
                
                # Use iterator to get segments with more frequent interruption checks
                segments_iter = iter(segments)
                
                while True:
                    try:
                        # Check for interruption before processing next segment
                        if _shutdown_requested:
                            console.print("\\n💾 Transcription interrupted - partial results will be returned", style="yellow")
                            break
                        
                        # Get next segment
                        segment = next(segments_iter)
                        
                        segment_dict = {
                        "id": segment.id,
                        "seek": int(segment.start * 100),  # Convert to centiseconds
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip(),
                        "tokens": [],  # faster-whisper doesn't expose tokens by default
                        "temperature": getattr(segment, 'temperature', 0.0),
                        "avg_logprob": getattr(segment, 'avg_logprob', 0.0),
                        "compression_ratio": getattr(segment, 'compression_ratio', 0.0),
                        "no_speech_prob": getattr(segment, 'no_speech_prob', 0.0),
                        "words": []
                    }
                    
                    # Add word-level timestamps if available
                    if hasattr(segment, 'words') and segment.words:
                        for word in segment.words:
                            word_dict = {
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "probability": getattr(word, 'probability', 1.0)
                            }
                            segment_dict["words"].append(word_dict)
                    
                        segment_list.append(segment_dict)
                        segment_count += 1
                        
                        # Update progress every 5 segments for more responsive interruption
                        if segment_count % 5 == 0:
                            progress.update(task, completed=min(30 + segment_count * 2, 90))
                    
                    except StopIteration:
                        # End of segments
                        break
                    except Exception as e:
                        logger.error(f"Error processing segment: {e}")
                        break
                
                progress.update(task, completed=100)
                
                # Format result to match openai-whisper structure
                result = {
                    "text": " ".join(segment["text"] for segment in segment_list),
                    "segments": segment_list,
                    "language": info.language,
                    "language_probability": info.language_probability,
                    "duration": info.duration,
                    "duration_after_vad": getattr(info, 'duration_after_vad', info.duration)
                }
                
                logger.info(f"Transcription completed. {len(segment_list)} segments found")
                return result
                
            except Exception as e:
                raise RuntimeError(f"Transcription failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "compute_type": self.compute_type,
            "cache_dir": str(config.whisper_cache_dir) if hasattr(config, 'whisper_cache_dir') else None,
            "loaded": self.model is not None,
            "engine": "faster-whisper"
        }