"""Tests for data models."""

import pytest
from pathlib import Path
from screenscribe.models import (
    TranscriptSegment, FrameData, AlignedContent, 
    VideoMetadata, ProcessingOptions, SynthesisResult
)


class TestTranscriptSegment:
    """Test TranscriptSegment model."""
    
    def test_create_segment(self):
        """Test creating a transcript segment."""
        segment = TranscriptSegment(
            id=0,
            seek=0,
            start=5.0,
            end=10.0,
            text="Test transcript",
            tokens=[1, 2, 3],
            temperature=0.0,
            avg_logprob=-0.5,
            compression_ratio=1.0,
            no_speech_prob=0.1
        )
        
        assert segment.id == 0
        assert segment.duration == 5.0
        assert segment.timestamp_str == "0:00:05"
    
    def test_segment_properties(self):
        """Test segment computed properties."""
        segment = TranscriptSegment(
            id=1,
            seek=0,
            start=65.5,
            end=72.3,
            text="Another test",
            tokens=[4, 5, 6],
            temperature=0.0,
            avg_logprob=-0.3,
            compression_ratio=1.1,
            no_speech_prob=0.05
        )
        
        assert segment.duration == pytest.approx(6.8)
        assert segment.timestamp_str == "0:01:05"


class TestFrameData:
    """Test FrameData model."""
    
    def test_create_frame(self, temp_dir):
        """Test creating frame data."""
        frame_path = temp_dir / "frame.jpg"
        thumb_path = temp_dir / "thumb.jpg"
        
        # Create dummy files
        frame_path.write_bytes(b"dummy")
        thumb_path.write_bytes(b"dummy")
        
        frame = FrameData(
            index=0,
            timestamp=5.5,
            frame_path=frame_path,
            thumbnail_path=thumb_path
        )
        
        assert frame.index == 0
        assert frame.timestamp == 5.5
        assert frame.timestamp_str == "0:00:05"
        assert frame.is_scene_change is True  # default value


class TestAlignedContent:
    """Test AlignedContent model."""
    
    def test_get_transcript_text(self, sample_transcript_segments, sample_frames):
        """Test transcript text concatenation."""
        aligned = AlignedContent(
            frame=sample_frames[0],
            transcript_segments=sample_transcript_segments,
            time_window=2.0
        )
        
        text = aligned.get_transcript_text()
        expected = "Hello and welcome to this tutorial Today we will be learning about Python"
        assert text == expected


class TestVideoMetadata:
    """Test VideoMetadata model."""
    
    def test_duration_formatting(self, temp_dir):
        """Test duration string formatting."""
        video_path = temp_dir / "video.mp4"
        video_path.write_bytes(b"dummy")
        
        metadata = VideoMetadata(
            title="Test Video",
            duration=3665.0,  # 1 hour, 1 minute, 5 seconds
            fps=30.0,
            width=1920,
            height=1080,
            codec="h264",
            source_path=video_path
        )
        
        assert metadata.duration_str == "1:01:05"


class TestProcessingOptions:
    """Test ProcessingOptions model."""
    
    def test_valid_options(self, temp_dir):
        """Test creating valid processing options."""
        options = ProcessingOptions(
            output_dir=temp_dir,
            output_format="markdown",
            sampling_mode="scene"
        )
        
        assert options.output_dir == temp_dir
        assert options.output_format == "markdown"
        assert options.sampling_mode == "scene"
        assert options.whisper_model == "medium"  # default
    
    def test_invalid_format(self, temp_dir):
        """Test invalid output format validation."""
        with pytest.raises(ValueError):
            ProcessingOptions(
                output_dir=temp_dir,
                output_format="invalid"
            )
    
    def test_invalid_sampling_mode(self, temp_dir):
        """Test invalid sampling mode validation."""
        with pytest.raises(ValueError):
            ProcessingOptions(
                output_dir=temp_dir,
                sampling_mode="invalid"
            )


class TestSynthesisResult:
    """Test SynthesisResult model."""
    
    def test_create_result(self):
        """Test creating synthesis result."""
        result = SynthesisResult(
            frame_timestamp=5.5,
            summary="Test summary",
            visual_description="Test description",
            key_points=["Point 1", "Point 2"]
        )
        
        assert result.frame_timestamp == 5.5
        assert result.summary == "Test summary"
        assert len(result.key_points) == 2