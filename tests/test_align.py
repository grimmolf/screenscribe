"""Tests for temporal alignment module."""

import pytest
from screenscribe.align import TemporalAligner
from screenscribe.models import AlignedContent


class TestTemporalAligner:
    """Test the TemporalAligner class."""
    
    def test_init(self):
        """Test aligner initialization."""
        aligner = TemporalAligner(time_window=3.0)
        assert aligner.time_window == 3.0
    
    def test_align_basic(self, sample_transcript_segments, sample_frames):
        """Test basic alignment functionality."""
        aligner = TemporalAligner(time_window=2.0)
        
        aligned = aligner.align(sample_transcript_segments, sample_frames)
        
        assert len(aligned) == len(sample_frames)
        assert all(isinstance(ac, AlignedContent) for ac in aligned)
        
        # Check first frame alignment (timestamp 2.5)
        first_aligned = aligned[0]
        assert first_aligned.frame.timestamp == 2.5
        assert len(first_aligned.transcript_segments) == 1
        assert first_aligned.transcript_segments[0].text == "Hello and welcome to this tutorial"
        
        # Check second frame alignment (timestamp 7.5)
        second_aligned = aligned[1]
        assert second_aligned.frame.timestamp == 7.5
        assert len(second_aligned.transcript_segments) == 1
        assert second_aligned.transcript_segments[0].text == "Today we will be learning about Python"
    
    def test_align_empty_transcript(self, sample_frames):
        """Test alignment with empty transcript."""
        aligner = TemporalAligner()
        
        aligned = aligner.align([], sample_frames)
        
        assert len(aligned) == len(sample_frames)
        for ac in aligned:
            assert len(ac.transcript_segments) == 0
    
    def test_align_empty_frames(self, sample_transcript_segments):
        """Test alignment with empty frames."""
        aligner = TemporalAligner()
        
        aligned = aligner.align(sample_transcript_segments, [])
        
        assert len(aligned) == 0
    
    def test_find_nearest_segment(self, sample_transcript_segments):
        """Test finding nearest segment."""
        aligner = TemporalAligner()
        
        # Test timestamp before first segment
        nearest = aligner._find_nearest_segment(sample_transcript_segments, -1.0)
        assert nearest.id == 0
        
        # Test timestamp after last segment
        nearest = aligner._find_nearest_segment(sample_transcript_segments, 15.0)
        assert nearest.id == 1
        
        # Test timestamp within segment
        nearest = aligner._find_nearest_segment(sample_transcript_segments, 2.5)
        assert nearest.id == 0
    
    def test_get_alignment_stats(self, sample_transcript_segments, sample_frames):
        """Test alignment statistics."""
        aligner = TemporalAligner()
        aligned = aligner.align(sample_transcript_segments, sample_frames)
        
        stats = aligner.get_alignment_stats(aligned)
        
        assert stats["total_frames"] == 2
        assert stats["frames_with_transcript"] == 2
        assert stats["frames_without_transcript"] == 0
        assert stats["coverage_ratio"] == 1.0
        assert stats["avg_segments_per_frame"] == 1.0
        assert stats["time_window"] == aligner.time_window