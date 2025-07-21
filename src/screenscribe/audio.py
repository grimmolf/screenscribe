"""Audio processing module for screenscribe."""

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
from .audio_backends import get_best_backend, get_available_backends

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


class AudioProcessor:
    """Handles audio extraction and transcription using best available backend."""
    
    def __init__(self, model_name: str = "medium", backend: Optional[str] = None):
        """
        Initialize audio processor with platform-optimized backend.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            backend: Force specific backend (mlx, faster-whisper) or None for auto
        """
        self.model_name = model_name
        self.backend = get_best_backend(model_name, preferred=backend)
        self._checkpoint_file: Optional[Path] = None
        
        # Log backend selection
        backend_info = self.backend.get_info()
        console.print(
            f"🎙️ Audio backend: {backend_info.name} "
            f"({'GPU' if 'gpu' in backend_info.device else backend_info.device.upper()})",
            style="blue"
        )
    
    
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
        """Transcribe audio file using the selected backend."""
        logger.info(f"Transcribing audio: {audio_path}")
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Create progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task(
                f"Transcribing with {self.backend.get_info().name}...", 
                total=100
            )
            
            try:
                # Check for interruption before starting transcription
                if _shutdown_requested:
                    raise KeyboardInterrupt("Transcription interrupted before starting")
                
                # Transcribe using backend
                result = self.backend.transcribe(audio_path, language)
                progress.update(task, completed=100)
                
                # Convert to dict for compatibility with existing code
                return {
                    "text": result.text,
                    "segments": [seg.dict() for seg in result.segments],
                    "language": result.language,
                    "duration": result.duration
                }
                
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        backend_info = self.backend.get_info()
        return {
            "model_name": self.model_name,
            "backend": backend_info.name,
            "device": backend_info.device,
            "compute_type": backend_info.compute_type,
            "available": backend_info.available,
            "cache_dir": str(config.whisper_cache_dir) if hasattr(config, 'whisper_cache_dir') else None
        }