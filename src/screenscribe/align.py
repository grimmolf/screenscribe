"""Temporal alignment module for screenscribe."""

from typing import List, Dict
import logging

from .models import TranscriptSegment, FrameData, AlignedContent

logger = logging.getLogger(__name__)


class TemporalAligner:
    """Aligns transcript segments with video frames based on temporal proximity."""
    
    def __init__(self, time_window: float = 2.0):
        """
        Initialize temporal aligner.
        
        Args:
            time_window: Time window in seconds before/after frame to look for transcript segments
        """
        self.time_window = time_window
        logger.info(f"TemporalAligner initialized with time_window={time_window}s")
    
    def align(self, 
              transcript_segments: List[TranscriptSegment],
              frames: List[FrameData]) -> List[AlignedContent]:
        """
        Match transcript segments to frames based on temporal proximity.
        
        Args:
            transcript_segments: List of transcript segments with timing
            frames: List of extracted frames with timestamps
            
        Returns:
            List of aligned content pairing frames with relevant transcript segments
        """
        logger.info(f"Aligning {len(frames)} frames with {len(transcript_segments)} transcript segments")
        
        if not transcript_segments:
            logger.warning("No transcript segments provided")
            return self._create_empty_aligned_content(frames)
        
        if not frames:
            logger.warning("No frames provided")
            return []
        
        aligned = []
        
        # Build time index for efficient lookup
        # Create sorted list of (time, segment) tuples for binary search optimization
        time_index = []
        for seg in transcript_segments:
            time_index.append((seg.start, seg))
            time_index.append((seg.end, seg))
        time_index.sort(key=lambda x: x[0])
        
        for frame in frames:
            # Find segments within time window of frame
            window_start = frame.timestamp - self.time_window
            window_end = frame.timestamp + self.time_window
            
            # Find all segments that overlap with the time window
            relevant_segments = []
            
            for seg in transcript_segments:
                # Check if segment overlaps with window
                # Segment overlaps if: segment.end >= window_start AND segment.start <= window_end
                if seg.end >= window_start and seg.start <= window_end:
                    relevant_segments.append(seg)
            
            # Handle frames with no nearby transcript
            if not relevant_segments:
                # Look for nearest segment
                nearest = self._find_nearest_segment(transcript_segments, frame.timestamp)
                if nearest:
                    relevant_segments = [nearest]
                    logger.debug(f"Frame at {frame.timestamp:.2f}s: no segments in window, using nearest at {nearest.start:.2f}s")
                else:
                    logger.warning(f"Frame at {frame.timestamp:.2f}s: no transcript segments found")
            else:
                logger.debug(f"Frame at {frame.timestamp:.2f}s: found {len(relevant_segments)} relevant segments")
            
            aligned_content = AlignedContent(
                frame=frame,
                transcript_segments=relevant_segments,
                time_window=self.time_window
            )
            
            aligned.append(aligned_content)
        
        logger.info(f"Successfully aligned {len(aligned)} frames with transcript segments")
        return aligned
    
    def _find_nearest_segment(self, segments: List[TranscriptSegment], timestamp: float) -> TranscriptSegment:
        """Find the transcript segment nearest to the given timestamp."""
        if not segments:
            return None
        
        # Find segment with minimum distance to timestamp
        min_distance = float('inf')
        nearest_segment = None
        
        for seg in segments:
            # Calculate distance to segment (considering segment duration)
            if timestamp < seg.start:
                distance = seg.start - timestamp
            elif timestamp > seg.end:
                distance = timestamp - seg.end
            else:
                # Timestamp is within segment
                distance = 0
            
            if distance < min_distance:
                min_distance = distance
                nearest_segment = seg
        
        return nearest_segment
    
    def _create_empty_aligned_content(self, frames: List[FrameData]) -> List[AlignedContent]:
        """Create aligned content with empty transcript segments for frames."""
        logger.warning("Creating aligned content with empty transcript segments")
        
        aligned = []
        for frame in frames:
            aligned_content = AlignedContent(
                frame=frame,
                transcript_segments=[],
                time_window=self.time_window
            )
            aligned.append(aligned_content)
        
        return aligned
    
    def get_alignment_stats(self, aligned_content: List[AlignedContent]) -> Dict[str, float]:
        """Get statistics about the alignment quality."""
        if not aligned_content:
            return {}
        
        total_frames = len(aligned_content)
        frames_with_transcript = sum(1 for ac in aligned_content if ac.transcript_segments)
        frames_without_transcript = total_frames - frames_with_transcript
        
        # Calculate average segments per frame
        total_segments = sum(len(ac.transcript_segments) for ac in aligned_content)
        avg_segments_per_frame = total_segments / total_frames if total_frames > 0 else 0
        
        # Calculate coverage statistics
        coverage_ratio = frames_with_transcript / total_frames if total_frames > 0 else 0
        
        return {
            "total_frames": total_frames,
            "frames_with_transcript": frames_with_transcript,
            "frames_without_transcript": frames_without_transcript,
            "coverage_ratio": coverage_ratio,
            "avg_segments_per_frame": avg_segments_per_frame,
            "time_window": self.time_window
        }