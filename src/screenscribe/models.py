"""Data models for screenscribe."""

from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class WordTiming(BaseModel):
    """Individual word with timing information"""
    word: str
    start: float
    end: float
    probability: float = Field(ge=0.0, le=1.0)


class TranscriptSegment(BaseModel):
    """Segment of transcript with timing"""
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: Optional[List[WordTiming]] = None

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def timestamp_str(self) -> str:
        """Format as [HH:MM:SS]"""
        return str(timedelta(seconds=int(self.start))).split(".")[0]


class FrameData(BaseModel):
    """Extracted frame with metadata"""
    index: int
    timestamp: float
    frame_path: Path
    thumbnail_path: Path
    is_scene_change: bool = True
    ocr_text: Optional[str] = None

    @field_validator("frame_path", "thumbnail_path")
    @classmethod
    def path_must_exist(cls, v):
        if not v.exists():
            raise ValueError(f"Path does not exist: {v}")
        return v

    @property
    def timestamp_str(self) -> str:
        """Format as [HH:MM:SS]"""
        return str(timedelta(seconds=int(self.timestamp))).split(".")[0]


class AlignedContent(BaseModel):
    """Frame with associated transcript segments"""
    frame: FrameData
    transcript_segments: List[TranscriptSegment]
    time_window: float = 2.0  # seconds before/after frame

    def get_transcript_text(self) -> str:
        """Concatenate all transcript segments"""
        return " ".join(seg.text.strip() for seg in self.transcript_segments)


class VideoMetadata(BaseModel):
    """Video information"""
    title: str
    duration: float
    fps: float
    width: int
    height: int
    codec: str
    source_path: Path
    youtube_url: Optional[str] = None

    @property
    def duration_str(self) -> str:
        """Format as HH:MM:SS"""
        return str(timedelta(seconds=int(self.duration)))


class ProcessingOptions(BaseModel):
    """User-specified processing options"""
    output_dir: Path
    output_format: str = Field(pattern="^(markdown|html)$")
    whisper_model: str = "medium"
    whisper_backend: Optional[str] = None  # Backend selection (mlx, faster-whisper, auto)
    llm_provider: str = "openai"
    no_fallback: bool = False
    sampling_mode: str = Field(pattern="^(scene|interval)$", default="interval")
    interval_seconds: float = 45.0
    scene_threshold: float = 0.3
    thumbnail_width: int = 320
    verbose: bool = False
    prompts_dir: Optional[Path] = None
    copy_from_nas: bool = True


class SynthesisResult(BaseModel):
    """LLM synthesis output for one frame"""
    frame_timestamp: float
    summary: str
    visual_description: Optional[str] = None
    key_points: List[str] = []


# Multi-backend transcription models

class TranscriptionSegment(BaseModel):
    """Normalized segment format across all backends."""
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int] = []
    temperature: float = 0.0
    avg_logprob: float = 0.0
    compression_ratio: float = 0.0
    no_speech_prob: float = 0.0
    words: Optional[List[Dict[str, Any]]] = None

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def timestamp_str(self) -> str:
        """Format as [HH:MM:SS]"""
        return str(timedelta(seconds=int(self.start))).split(".")[0]


class TranscriptionResult(BaseModel):
    """Normalized transcription result."""
    text: str
    segments: List[TranscriptionSegment]
    language: str
    duration: Optional[float] = None


class BackendInfo(BaseModel):
    """Information about an audio backend."""
    name: Literal["mlx", "faster-whisper", "whisper-cpp"]
    available: bool
    device: str
    compute_type: Optional[str] = None
    reason: Optional[str] = None  # Why not available


class ProcessingResult(BaseModel):
    """Final processing result"""
    video_metadata: VideoMetadata
    processing_options: ProcessingOptions
    transcript_segments: List[TranscriptSegment]
    frames: List[FrameData]
    aligned_content: List[AlignedContent]
    synthesis_results: List[SynthesisResult]
    output_file: Path
    processing_time: float

    def save(self, path: Path):
        """Save processing result as JSON"""
        path.write_text(self.model_dump_json(indent=2))
