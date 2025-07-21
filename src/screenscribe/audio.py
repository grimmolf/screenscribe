"""Audio processing module for screenscribe."""

from faster_whisper import WhisperModel
from pathlib import Path
import subprocess
import tempfile
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
import logging
from typing import Dict, Any, Optional, List, Tuple

from .config import config

logger = logging.getLogger(__name__)


def _get_optimal_device() -> tuple[str, str]:
    """Determine the optimal device and compute type for faster-whisper."""
    try:
        import torch
        
        # Check for Apple Silicon GPU (Metal Performance Shaders)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            # Apple Silicon M1/M2/M3 with MPS support
            return "auto", "float16"  # faster-whisper will auto-detect best device
        
        # Check for NVIDIA CUDA
        elif torch.cuda.is_available():
            return "cuda", "float16"
            
        # Fall back to CPU
        else:
            return "cpu", "int8"
            
    except ImportError:
        # If torch isn't available, assume CPU
        return "cpu", "int8"


class AudioProcessor:
    """Handles audio extraction and transcription using faster-whisper."""
    
    def __init__(self, model_name: str = "medium"):
        self.model_name = model_name
        # Get optimal device and compute type for this system
        self.device, self.compute_type = _get_optimal_device()
        self.model: Optional[WhisperModel] = None
        
        device_info = {
            "auto": "Apple Silicon GPU (M1/M2/M3)",
            "cuda": "NVIDIA GPU",
            "cpu": "CPU"
        }.get(self.device, self.device)
        
        logger.info(f"Initializing AudioProcessor with model '{model_name}' on {device_info} ({self.compute_type})")
    
    def _load_model(self) -> None:
        """Load faster-whisper model with error handling."""
        if self.model is not None:
            return
        
        try:
            logger.info(f"Loading faster-whisper model: {self.model_name}")
            self.model = WhisperModel(
                self.model_name, 
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(config.whisper_cache_dir) if hasattr(config, 'whisper_cache_dir') else None
            )
        except Exception as e:
            if "out of memory" in str(e).lower() and self.device == "cuda":
                logger.warning("GPU out of memory, falling back to CPU")
                self.device = "cpu" 
                self.compute_type = "int8"
                self.model = WhisperModel(
                    self.model_name, 
                    device="cpu",
                    compute_type="int8",
                    download_root=str(config.whisper_cache_dir) if hasattr(config, 'whisper_cache_dir') else None
                )
            else:
                raise RuntimeError(f"Failed to load faster-whisper model: {e}")
    
    async def extract_audio(self, video_path: Path) -> Path:
        """Extract audio track from video file."""
        logger.info(f"Extracting audio from: {video_path}")
        
        # Create temporary audio file
        audio_path = Path(tempfile.mktemp(suffix=".wav"))
        
        # Check if video has audio stream first
        probe_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_type", "-of", "csv=p=0",
            str(video_path)
        ]
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            if not result.stdout.strip():
                raise ValueError("Video has no audio stream")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to probe video for audio: {e}")
        
        # Extract audio using ffmpeg
        cmd = [
            "ffmpeg", "-i", str(video_path),
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
            return audio_path
        except subprocess.CalledProcessError as e:
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
                # faster-whisper returns segments and info separately
                segments, info = self.model.transcribe(
                    str(audio_path),
                    language=language,
                    word_timestamps=True,
                    vad_filter=True,  # Voice activity detection
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                
                progress.update(task, completed=50)
                
                # Convert segments to list and format similar to openai-whisper
                segment_list = []
                for segment in segments:
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