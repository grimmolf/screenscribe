"""Audio processing module for screenscribe."""

import whisper
import torch
from pathlib import Path
import subprocess
import tempfile
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
import numpy as np
import logging
from typing import Dict, Any, Optional

from .config import config

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio extraction and transcription using Whisper."""
    
    def __init__(self, model_name: str = "medium"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model: Optional[whisper.Whisper] = None
        
        logger.info(f"Initializing AudioProcessor with model '{model_name}' on {self.device}")
    
    def _load_model(self) -> None:
        """Load Whisper model with error handling."""
        if self.model is not None:
            return
        
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
        except RuntimeError as e:
            if "out of memory" in str(e) and self.device == "cuda":
                logger.warning("GPU out of memory, falling back to CPU")
                self.device = "cpu"
                self.model = whisper.load_model(self.model_name, device="cpu")
            else:
                raise RuntimeError(f"Failed to load Whisper model: {e}")
    
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
        """Transcribe audio file using Whisper."""
        logger.info(f"Transcribing audio: {audio_path}")
        
        self._load_model()
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Load audio and check duration
        audio = whisper.load_audio(str(audio_path))
        duration = len(audio) / whisper.audio.SAMPLE_RATE
        
        # Handle very short audio by padding with silence
        if duration < 0.5:
            logger.warning(f"Audio duration ({duration:.2f}s) is very short, padding with silence")
            silence_samples = int(0.5 * whisper.audio.SAMPLE_RATE)
            audio = np.pad(audio, (0, silence_samples), mode='constant')
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("Transcribing audio...", total=100)
            
            # Progress callback
            def progress_callback(completed: float):
                progress.update(task, completed=completed * 100)
            
            try:
                # Transcribe with word-level timestamps
                result = self.model.transcribe(
                    audio,
                    language=language,
                    word_timestamps=True,
                    verbose=False,
                    # Note: progress_callback might not be available in all Whisper versions
                    # We'll implement a simpler approach
                )
                
                progress.update(task, completed=100)
                
                logger.info(f"Transcription completed. {len(result['segments'])} segments found")
                return result
                
            except Exception as e:
                raise RuntimeError(f"Transcription failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "cache_dir": str(config.whisper_cache_dir),
            "loaded": self.model is not None
        }