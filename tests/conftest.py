"""Pytest configuration and fixtures for screenscribe tests."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import json

from screenscribe.models import (
    TranscriptSegment, FrameData, VideoMetadata, 
    ProcessingOptions, SynthesisResult
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_transcript_segments():
    """Sample transcript segments for testing."""
    return [
        TranscriptSegment(
            id=0,
            seek=0,
            start=0.0,
            end=5.0,
            text="Hello and welcome to this tutorial",
            tokens=[1, 2, 3],
            temperature=0.0,
            avg_logprob=-0.5,
            compression_ratio=1.0,
            no_speech_prob=0.1
        ),
        TranscriptSegment(
            id=1,
            seek=5000,
            start=5.0,
            end=10.0,
            text="Today we will be learning about Python",
            tokens=[4, 5, 6],
            temperature=0.0,
            avg_logprob=-0.4,
            compression_ratio=1.1,
            no_speech_prob=0.05
        )
    ]


@pytest.fixture
def sample_frames(temp_dir):
    """Sample frame data for testing."""
    frames_dir = temp_dir / "frames"
    thumbnails_dir = temp_dir / "thumbnails"
    frames_dir.mkdir()
    thumbnails_dir.mkdir()
    
    # Create dummy image files
    frame_path_1 = frames_dir / "frame_0000.jpg"
    frame_path_2 = frames_dir / "frame_0001.jpg"
    thumb_path_1 = thumbnails_dir / "thumb_frame_0000.jpg"
    thumb_path_2 = thumbnails_dir / "thumb_frame_0001.jpg"
    
    # Create dummy files
    for path in [frame_path_1, frame_path_2, thumb_path_1, thumb_path_2]:
        path.write_bytes(b"dummy image data")
    
    return [
        FrameData(
            index=0,
            timestamp=2.5,
            frame_path=frame_path_1,
            thumbnail_path=thumb_path_1,
            is_scene_change=True
        ),
        FrameData(
            index=1,
            timestamp=7.5,
            frame_path=frame_path_2,
            thumbnail_path=thumb_path_2,
            is_scene_change=True
        )
    ]


@pytest.fixture
def sample_video_metadata(temp_dir):
    """Sample video metadata for testing."""
    video_path = temp_dir / "sample.mp4"
    video_path.write_bytes(b"dummy video data")
    
    return VideoMetadata(
        title="Sample Video",
        duration=30.0,
        fps=30.0,
        width=1920,
        height=1080,
        codec="h264",
        source_path=video_path
    )


@pytest.fixture
def sample_processing_options(temp_dir):
    """Sample processing options for testing."""
    return ProcessingOptions(
        output_dir=temp_dir,
        output_format="markdown",
        whisper_model="tiny",
        llm_provider="openai",
        sampling_mode="scene"
    )


@pytest.fixture
def sample_synthesis_results():
    """Sample synthesis results for testing."""
    return [
        SynthesisResult(
            frame_timestamp=2.5,
            summary="Introduction slide with welcome message",
            visual_description="Title slide with 'Tutorial' text",
            key_points=["Welcome message", "Tutorial introduction"]
        ),
        SynthesisResult(
            frame_timestamp=7.5,
            summary="Code editor showing Python syntax",
            visual_description="Code editor with Python function definition",
            key_points=["Python function", "Code syntax highlighting"]
        )
    ]


@pytest.fixture
def mock_whisper_result():
    """Mock Whisper transcription result."""
    return {
        "text": "Hello and welcome to this tutorial. Today we will be learning about Python.",
        "segments": [
            {
                "id": 0,
                "seek": 0,
                "start": 0.0,
                "end": 5.0,
                "text": "Hello and welcome to this tutorial",
                "tokens": [1, 2, 3],
                "temperature": 0.0,
                "avg_logprob": -0.5,
                "compression_ratio": 1.0,
                "no_speech_prob": 0.1,
                "words": None
            },
            {
                "id": 1,
                "seek": 5000,
                "start": 5.0,
                "end": 10.0,
                "text": "Today we will be learning about Python",
                "tokens": [4, 5, 6],
                "temperature": 0.0,
                "avg_logprob": -0.4,
                "compression_ratio": 1.1,
                "no_speech_prob": 0.05,
                "words": None
            }
        ]
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM synthesis response."""
    return {
        "summary": "Test summary of frame content",
        "visual_description": "Test visual description",
        "key_points": ["Point 1", "Point 2"]
    }