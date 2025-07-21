"""Audio transcription backend implementations for screenscribe."""

import logging
import os
import platform
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from .models import BackendInfo, TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


class WhisperBackend(ABC):
    """Abstract base class for Whisper backends."""

    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None

    @abstractmethod
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio file and return normalized result."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on current system."""

    @abstractmethod
    def get_info(self) -> BackendInfo:
        """Get backend information."""


class MLXWhisperBackend(WhisperBackend):
    """Apple Silicon optimized backend using MLX."""

    def is_available(self) -> bool:
        # Check platform
        if platform.system() != "Darwin":
            return False
        if platform.machine() != "arm64":
            return False

        # Check import
        try:
            import mlx_whisper
            return True
        except ImportError:
            return False

    def get_info(self) -> BackendInfo:
        available = self.is_available()
        return BackendInfo(
            name="mlx",
            available=available,
            device="gpu" if available else "none",
            compute_type="float16",
            reason=None if available else "Not Apple Silicon or MLX not installed",
        )

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        import mlx_whisper

        # Map model name to MLX format
        model_map = {
            "tiny": "mlx-community/whisper-tiny",
            "base": "mlx-community/whisper-base",
            "small": "mlx-community/whisper-small",
            "medium": "mlx-community/whisper-medium",
            "large": "mlx-community/whisper-large-v3",
            "large-v3": "mlx-community/whisper-large-v3",
        }

        model_repo = model_map.get(self.model_name, f"mlx-community/whisper-{self.model_name}")

        logger.info(f"Transcribing with MLX backend using model: {model_repo}")

        # Transcribe
        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=model_repo,
            language=language,
            verbose=False,
        )

        # Normalize output
        segments = []
        for i, seg in enumerate(result.get("segments", [])):
            segment = TranscriptionSegment(
                id=i,
                seek=0,  # MLX doesn't provide seek
                start=seg.get("start", 0),
                end=seg.get("end", 0),
                text=seg.get("text", ""),
                tokens=seg.get("tokens", []),
                temperature=seg.get("temperature", 0.0),
                avg_logprob=seg.get("avg_logprob", 0.0),
                compression_ratio=seg.get("compression_ratio", 0.0),
                no_speech_prob=seg.get("no_speech_prob", 0.0),
                words=seg.get("words"),
            )
            segments.append(segment)

        return TranscriptionResult(
            text=result["text"],
            segments=segments,
            language=result.get("language", language or "en"),
        )


class FasterWhisperBackend(WhisperBackend):
    """Cross-platform backend using faster-whisper."""

    def __init__(self, model_name: str = "base"):
        super().__init__(model_name)
        self._device = None
        self._compute_type = None

    def is_available(self) -> bool:
        """Always available as universal fallback."""
        return True

    def get_info(self) -> BackendInfo:
        # Detect device
        device = "cpu"
        compute_type = "int8"

        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                compute_type = "float16"
        except ImportError:
            pass

        return BackendInfo(
            name="faster-whisper",
            available=True,
            device=device,
            compute_type=compute_type,
        )

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        from faster_whisper import WhisperModel

        # Initialize model if needed
        if self.model is None:
            info = self.get_info()
            self._device = info.device
            self._compute_type = info.compute_type

            # CPU optimization for Apple Silicon
            cpu_threads = None
            if self._device == "cpu" and platform.machine() == "arm64":
                total_cores = os.cpu_count() or 4
                cpu_threads = max(4, int(total_cores * 0.85))
                logger.info(f"Using {cpu_threads}/{total_cores} CPU threads for Apple Silicon")

            logger.info(f"Loading faster-whisper model: {self.model_name} on {self._device} ({self._compute_type})")

            try:
                self.model = WhisperModel(
                    self.model_name,
                    device=self._device,
                    compute_type=self._compute_type,
                    cpu_threads=cpu_threads,
                )
            except Exception as e:
                if "out of memory" in str(e).lower() and (self._device == "cuda"):
                    logger.warning(f"GPU out of memory on {self._device}, falling back to CPU")
                    self._device = "cpu"
                    self._compute_type = "int8"
                    cpu_threads = max(4, int((os.cpu_count() or 4) * 0.85))
                    self.model = WhisperModel(
                        self.model_name,
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=cpu_threads,
                    )
                elif "incompatible constructor arguments" in str(e) or "device" in str(e).lower():
                    # Device not supported, fall back to CPU
                    logger.warning(f"Device '{self._device}' not supported by faster-whisper, falling back to CPU")
                    self._device = "cpu"
                    self._compute_type = "int8"
                    cpu_threads = max(4, int((os.cpu_count() or 4) * 0.85))
                    self.model = WhisperModel(
                        self.model_name,
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=cpu_threads,
                    )
                    logger.info(f"Successfully loaded model on CPU with {cpu_threads} threads")
                else:
                    raise RuntimeError(f"Failed to load faster-whisper model: {e}")

        # Transcribe
        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        # Convert generator to list and normalize
        segment_list = []
        full_text = []

        for i, segment in enumerate(segments):
            seg_model = TranscriptionSegment(
                id=i,
                seek=segment.seek,
                start=segment.start,
                end=segment.end,
                text=segment.text,
                tokens=segment.tokens,
                temperature=segment.temperature,
                avg_logprob=segment.avg_logprob,
                compression_ratio=segment.compression_ratio,
                no_speech_prob=segment.no_speech_prob,
                words=[
                    {"start": w.start, "end": w.end, "word": w.word, "probability": w.probability}
                    for w in (segment.words or [])
                ],
            )
            segment_list.append(seg_model)
            full_text.append(segment.text)

        return TranscriptionResult(
            text=" ".join(full_text),
            segments=segment_list,
            language=info.language,
            duration=info.duration,
        )


def get_available_backends(model_name: str = "base") -> List[BackendInfo]:
    """Get information about all available backends."""
    backends = [
        MLXWhisperBackend(model_name),
        FasterWhisperBackend(model_name),
    ]

    return [backend.get_info() for backend in backends]


def get_best_backend(model_name: str = "base", preferred: Optional[str] = None) -> WhisperBackend:
    """
    Get the best available backend for current platform.
    
    Priority:
    1. User preference (if available)
    2. Platform-specific optimization (MLX on Apple Silicon)
    3. Universal fallback (faster-whisper)
    """
    backends = {
        "mlx": MLXWhisperBackend,
        "faster-whisper": FasterWhisperBackend,
    }

    # Try user preference
    if preferred and preferred in backends:
        backend_class = backends[preferred]
        backend = backend_class(model_name)
        if backend.is_available():
            logger.info(f"Using requested backend: {preferred}")
            return backend
        logger.warning(f"Requested backend '{preferred}' not available")

    # Auto-detect best backend
    # Priority order for auto-detection
    priority = ["mlx", "faster-whisper"]

    for name in priority:
        if name in backends:
            backend_class = backends[name]
            backend = backend_class(model_name)
            if backend.is_available():
                logger.info(f"Auto-selected backend: {name}")
                return backend

    # This should never happen
    raise RuntimeError("No audio transcription backend available")
