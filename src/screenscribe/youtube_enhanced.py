"""Enhanced YouTube integration with transcript extraction and fallbacks."""

import json
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from .models import TranscriptSegment, TranscriptionResult

logger = logging.getLogger(__name__)


@dataclass
class YouTubeTranscriptSource:
    """Information about a YouTube transcript source."""
    source: str  # "youtube_auto", "youtube_manual", "whisper", "external_file"
    language: Optional[str] = None
    confidence: Optional[float] = None
    segment_count: int = 0


class YouTubeProcessor:
    """Enhanced YouTube video processor with transcript options."""
    
    def __init__(self, prefer_youtube_transcripts: bool = True):
        self.prefer_youtube_transcripts = prefer_youtube_transcripts
        
    async def download_video(self, url: str, output_dir: Path, format_selector: str) -> Tuple[Path, Dict[str, Any]]:
        """Download YouTube video and return path and metadata."""
        
        ydl_opts = {
            'format': format_selector,
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'writeinfojson': True,
            'extractaudio': False,
            'writesubtitles': False,  # We'll handle transcripts separately
            'writeautomaticsub': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract info without downloading first
                info = ydl.extract_info(url, download=False)
                logger.info(f"Found video: {info.get('title', 'Unknown')}")
                
                # Download the video
                ydl.download([url])
                
                # Find the downloaded video file
                video_files = list(output_dir.glob(f"{info['title']}.*"))
                video_files = [f for f in video_files if f.suffix in ['.mp4', '.webm', '.mkv']]
                
                if not video_files:
                    raise RuntimeError("Downloaded video file not found")
                    
                video_path = video_files[0]
                logger.info(f"Downloaded video to: {video_path}")
                
                return video_path, info
                
            except Exception as e:
                logger.error(f"Error downloading YouTube video: {e}")
                raise
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('id')
        except Exception as e:
            logger.warning(f"Could not extract video ID from {url}: {e}")
            return None
    
    async def get_youtube_transcript(self, video_id: str, language_preference: List[str] = None) -> Optional[Tuple[TranscriptionResult, YouTubeTranscriptSource]]:
        """
        Attempt to get YouTube's built-in transcript.
        
        Args:
            video_id: YouTube video ID
            language_preference: List of preferred languages (e.g., ['en', 'en-US'])
            
        Returns:
            Tuple of (TranscriptionResult, YouTubeTranscriptSource) if successful, None otherwise
        """
        if not self.prefer_youtube_transcripts:
            return None
            
        if language_preference is None:
            language_preference = ['en', 'en-US', 'en-GB']
        
        try:
            # Get available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to find preferred language transcript
            transcript = None
            source_info = None
            
            # First try manually created transcripts
            for lang in language_preference:
                try:
                    transcript = transcript_list.find_manually_created_transcript([lang])
                    source_info = YouTubeTranscriptSource(
                        source="youtube_manual",
                        language=lang,
                        confidence=1.0
                    )
                    logger.info(f"Found manual YouTube transcript in {lang}")
                    break
                except NoTranscriptFound:
                    continue
            
            # Fall back to auto-generated transcripts
            if transcript is None:
                for lang in language_preference:
                    try:
                        transcript = transcript_list.find_generated_transcript([lang])
                        source_info = YouTubeTranscriptSource(
                            source="youtube_auto",
                            language=lang,
                            confidence=0.8  # Auto-generated are less reliable
                        )
                        logger.info(f"Found auto-generated YouTube transcript in {lang}")
                        break
                    except NoTranscriptFound:
                        continue
            
            if transcript is None:
                logger.info("No suitable YouTube transcript found")
                return None
            
            # Fetch the transcript
            transcript_data = transcript.fetch()
            
            # Convert to our format
            segments = []
            for i, item in enumerate(transcript_data):
                segments.append(TranscriptSegment(
                    id=i,
                    start=item['start'],
                    end=item['start'] + item['duration'],
                    text=item['text'].strip()
                ))
            
            if not segments:
                logger.warning("YouTube transcript was empty")
                return None
            
            # Create full text
            full_text = " ".join(segment.text for segment in segments)
            
            result = TranscriptionResult(
                text=full_text,
                segments=segments
            )
            
            source_info.segment_count = len(segments)
            
            logger.info(f"Successfully extracted YouTube transcript: {len(segments)} segments")
            return result, source_info
            
        except TranscriptsDisabled:
            logger.info("Transcripts are disabled for this video")
            return None
        except NoTranscriptFound:
            logger.info("No transcripts found for this video")
            return None
        except Exception as e:
            logger.error(f"Error extracting YouTube transcript: {e}")
            return None
    
    async def load_external_transcript(self, transcript_file: Path) -> Optional[Tuple[TranscriptionResult, YouTubeTranscriptSource]]:
        """
        Load transcript from external file.
        
        Supports:
        - JSON format (screenscribe format)
        - SRT format
        - VTT format
        - Plain text with timestamps
        """
        
        if not transcript_file.exists():
            logger.error(f"Transcript file not found: {transcript_file}")
            return None
        
        try:
            file_extension = transcript_file.suffix.lower()
            
            if file_extension == '.json':
                return await self._load_json_transcript(transcript_file)
            elif file_extension == '.srt':
                return await self._load_srt_transcript(transcript_file)
            elif file_extension == '.vtt':
                return await self._load_vtt_transcript(transcript_file)
            elif file_extension == '.txt':
                return await self._load_text_transcript(transcript_file)
            else:
                logger.error(f"Unsupported transcript format: {file_extension}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading external transcript: {e}")
            return None
    
    async def _load_json_transcript(self, file_path: Path) -> Tuple[TranscriptionResult, YouTubeTranscriptSource]:
        """Load JSON transcript (screenscribe format)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'segments' in data:
            segments = [TranscriptSegment(**seg) for seg in data['segments']]
        else:
            # Legacy format conversion
            segments = []
            for i, item in enumerate(data):
                segments.append(TranscriptSegment(
                    id=i,
                    start=item.get('start', 0),
                    end=item.get('end', 0),
                    text=item.get('text', '')
                ))
        
        full_text = data.get('text', ' '.join(seg.text for seg in segments))
        
        result = TranscriptionResult(text=full_text, segments=segments)
        source_info = YouTubeTranscriptSource(
            source="external_file", 
            segment_count=len(segments),
            confidence=1.0
        )
        
        logger.info(f"Loaded JSON transcript: {len(segments)} segments")
        return result, source_info
    
    async def _load_srt_transcript(self, file_path: Path) -> Tuple[TranscriptionResult, YouTubeTranscriptSource]:
        """Load SRT subtitle format."""
        import re
        
        content = file_path.read_text(encoding='utf-8')
        
        # Parse SRT format
        srt_pattern = r'(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)(?=\n\d+\s*\n|\Z)'
        matches = re.findall(srt_pattern, content, re.DOTALL)
        
        segments = []
        for match in matches:
            seq_num, start_time, end_time, text = match
            
            # Convert SRT timestamp to seconds
            start_seconds = self._srt_time_to_seconds(start_time)
            end_seconds = self._srt_time_to_seconds(end_time)
            
            # Clean up text
            clean_text = re.sub(r'<[^>]+>', '', text.strip().replace('\n', ' '))
            
            segments.append(TranscriptSegment(
                id=int(seq_num) - 1,
                start=start_seconds,
                end=end_seconds,
                text=clean_text
            ))
        
        full_text = ' '.join(seg.text for seg in segments)
        
        result = TranscriptionResult(text=full_text, segments=segments)
        source_info = YouTubeTranscriptSource(
            source="external_file",
            segment_count=len(segments),
            confidence=0.9
        )
        
        logger.info(f"Loaded SRT transcript: {len(segments)} segments")
        return result, source_info
    
    async def _load_vtt_transcript(self, file_path: Path) -> Tuple[TranscriptionResult, YouTubeTranscriptSource]:
        """Load WebVTT format."""
        import re
        
        content = file_path.read_text(encoding='utf-8')
        
        # Remove WebVTT header
        content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.MULTILINE | re.DOTALL)
        
        # Parse VTT format  
        vtt_pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\s*\n(.*?)(?=\n\d{2}:\d{2}:\d{2}|\Z)'
        matches = re.findall(vtt_pattern, content, re.DOTALL)
        
        segments = []
        for i, match in enumerate(matches):
            start_time, end_time, text = match
            
            # Convert VTT timestamp to seconds
            start_seconds = self._vtt_time_to_seconds(start_time)
            end_seconds = self._vtt_time_to_seconds(end_time)
            
            # Clean up text
            clean_text = re.sub(r'<[^>]+>', '', text.strip().replace('\n', ' '))
            
            segments.append(TranscriptSegment(
                id=i,
                start=start_seconds,
                end=end_seconds,
                text=clean_text
            ))
        
        full_text = ' '.join(seg.text for seg in segments)
        
        result = TranscriptionResult(text=full_text, segments=segments)
        source_info = YouTubeTranscriptSource(
            source="external_file",
            segment_count=len(segments),
            confidence=0.9
        )
        
        logger.info(f"Loaded VTT transcript: {len(segments)} segments")
        return result, source_info
    
    async def _load_text_transcript(self, file_path: Path) -> Tuple[TranscriptionResult, YouTubeTranscriptSource]:
        """Load plain text transcript (no timing information)."""
        content = file_path.read_text(encoding='utf-8').strip()
        
        # Create single segment with no timing
        segments = [TranscriptSegment(
            id=0,
            start=0.0,
            end=0.0,
            text=content
        )]
        
        result = TranscriptionResult(text=content, segments=segments)
        source_info = YouTubeTranscriptSource(
            source="external_file",
            segment_count=1,
            confidence=0.7  # Lower confidence due to no timing
        )
        
        logger.info("Loaded plain text transcript")
        return result, source_info
    
    def _srt_time_to_seconds(self, srt_time: str) -> float:
        """Convert SRT timestamp (HH:MM:SS,mmm) to seconds."""
        time_part, ms_part = srt_time.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return h * 3600 + m * 60 + s + ms / 1000
    
    def _vtt_time_to_seconds(self, vtt_time: str) -> float:
        """Convert VTT timestamp (HH:MM:SS.mmm) to seconds."""
        h, m, s = vtt_time.split(':')
        s, ms = s.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000