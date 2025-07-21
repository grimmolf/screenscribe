"""Data models for screenscribe."""

from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import timedelta


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
        return str(timedelta(seconds=int(self.start))).split('.')[0]


class FrameData(BaseModel):
    """Extracted frame with metadata"""
    index: int
    timestamp: float
    frame_path: Path
    thumbnail_path: Path
    is_scene_change: bool = True
    ocr_text: Optional[str] = None
    
    @field_validator('frame_path', 'thumbnail_path')
    @classmethod
    def path_must_exist(cls, v):
        if not v.exists():
            raise ValueError(f"Path does not exist: {v}")
        return v
    
    @property
    def timestamp_str(self) -> str:
        """Format as [HH:MM:SS]"""
        return str(timedelta(seconds=int(self.timestamp))).split('.')[0]


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
    llm_provider: str = "openai"
    no_fallback: bool = False
    sampling_mode: str = Field(pattern="^(scene|interval)$")
    interval_seconds: float = 5.0
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
        path.write_text(self.json(indent=2))