#!/usr/bin/env python3
"""
YouTube helper script for Fabric integration
Downloads videos and extracts transcripts using yt-dlp
"""

import argparse
import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional


def check_ytdlp():
    """Check if yt-dlp is available and provide helpful error messages"""
    try:
        result = subprocess.run(['yt-dlp', '--version'], 
                              capture_output=True, text=True, check=True)
        return True
    except FileNotFoundError:
        print("Error: yt-dlp not found. Please install it:", file=sys.stderr)
        print("  pip install yt-dlp", file=sys.stderr)
        print("  # or", file=sys.stderr) 
        print("  pipx install yt-dlp", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error: yt-dlp check failed: {e}", file=sys.stderr)
        print("Try updating yt-dlp: pip install --upgrade yt-dlp", file=sys.stderr)
        return False


def extract_youtube_transcript(url: str, verbose: bool = False) -> Dict[str, Any]:
    """Extract transcript from YouTube video using yt-dlp"""
    try:
        # Build yt-dlp command for transcript extraction
        cmd = [
            'yt-dlp',
            '--write-subs',
            '--write-auto-subs',
            '--sub-langs', 'en,en-US,en-GB',
            '--sub-format', 'vtt',
            '--skip-download',
            '--output', '%(title)s.%(ext)s',
            url
        ]
        
        if verbose:
            print(f"Extracting transcript from: {url}", file=sys.stderr)
            cmd.append('--verbose')
        else:
            cmd.append('--quiet')
        
        # Create temporary directory for transcript files
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Find the downloaded VTT file
                vtt_files = list(Path('.').glob('*.vtt'))
                if not vtt_files:
                    raise FileNotFoundError("No transcript file found. Video may not have captions available.")
                
                vtt_file = vtt_files[0]
                
                # Parse VTT file to extract transcript segments
                segments = parse_vtt_file(vtt_file)
                
                # Get video info for metadata
                info_cmd = ['yt-dlp', '--dump-json', '--quiet', url]
                info_result = subprocess.run(info_cmd, capture_output=True, text=True, check=True)
                video_info = json.loads(info_result.stdout)
                
                # Build transcript output
                full_text = " ".join([seg["text"] for seg in segments])
                
                return {
                    "text": full_text,
                    "segments": segments,
                    "language": "en",  # Default to English for YouTube transcripts
                    "duration": video_info.get("duration", 0),
                    "backend": "youtube-transcript",
                    "source_file": url,
                    "model": "youtube-captions",
                    "timestamp": __import__("time").time()
                }
                
            finally:
                os.chdir(original_cwd)
                
    except subprocess.CalledProcessError as e:
        error_msg = f"yt-dlp transcript extraction failed: {e}"
        if "No video subtitles found" in e.stderr:
            error_msg += "\nThis video does not have captions/transcripts available."
        elif "Private video" in e.stderr:
            error_msg += "\nThis video is private or unavailable."
        elif "Video unavailable" in e.stderr:
            error_msg += "\nThis video is unavailable or the URL is invalid."
        
        raise RuntimeError(error_msg)
    except FileNotFoundError as e:
        raise RuntimeError(f"Transcript file processing failed: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse video information: {e}")


def parse_vtt_file(vtt_path: Path) -> List[Dict[str, Any]]:
    """Parse VTT subtitle file and convert to transcript segments"""
    segments = []
    
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_segment = None
        segment_id = 0
        
        for line in lines:
            line = line.strip()
            
            # Skip header and empty lines
            if not line or line.startswith('WEBVTT') or line.startswith('NOTE'):
                continue
            
            # Time range line (e.g., "00:00:01.000 --> 00:00:05.000")
            if '-->' in line:
                try:
                    start_time, end_time = line.split(' --> ')
                    start_seconds = parse_vtt_timestamp(start_time)
                    end_seconds = parse_vtt_timestamp(end_time)
                    
                    current_segment = {
                        "id": segment_id,
                        "start": start_seconds,
                        "end": end_seconds,
                        "text": ""
                    }
                    segment_id += 1
                except ValueError:
                    continue
            
            # Text line
            elif current_segment is not None and line:
                # Clean up VTT formatting
                clean_text = line.replace('<c>', '').replace('</c>', '')
                clean_text = clean_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                
                if current_segment["text"]:
                    current_segment["text"] += " " + clean_text
                else:
                    current_segment["text"] = clean_text
                
                # If this is the end of the segment, add it to segments
                if current_segment["text"]:
                    segments.append(current_segment.copy())
                    current_segment = None
    
    except Exception as e:
        raise RuntimeError(f"Failed to parse VTT file: {e}")
    
    return segments


def parse_vtt_timestamp(timestamp: str) -> float:
    """Convert VTT timestamp to seconds"""
    # Handle format: "00:01:23.456" or "01:23.456"
    parts = timestamp.split(':')
    
    if len(parts) == 3:  # HH:MM:SS.mmm
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    elif len(parts) == 2:  # MM:SS.mmm
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    else:
        return float(timestamp)


def download_youtube_video(url: str, verbose: bool = False) -> str:
    """Download YouTube video and return local file path"""
    try:
        # Create temporary directory for video download
        temp_dir = tempfile.mkdtemp(prefix="youtube_video_")
        
        # Build yt-dlp command for video download
        cmd = [
            'yt-dlp',
            '--format', 'best[height<=720]',  # Limit quality for faster processing
            '--output', f'{temp_dir}/%(title)s.%(ext)s',
            url
        ]
        
        if verbose:
            print(f"Downloading video from: {url}", file=sys.stderr)
            cmd.append('--verbose')
        else:
            cmd.append('--quiet')
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Find the downloaded video file
        video_files = list(Path(temp_dir).glob('*'))
        video_files = [f for f in video_files if f.suffix.lower() in ['.mp4', '.mkv', '.webm', '.avi']]
        
        if not video_files:
            raise FileNotFoundError("No video file found after download")
        
        video_path = str(video_files[0])
        
        if verbose:
            print(f"Video downloaded to: {video_path}", file=sys.stderr)
        
        return video_path
        
    except subprocess.CalledProcessError as e:
        error_msg = f"yt-dlp video download failed: {e}"
        if "Private video" in e.stderr:
            error_msg += "\nThis video is private or unavailable."
        elif "Video unavailable" in e.stderr:
            error_msg += "\nThis video is unavailable or the URL is invalid."
        elif "Sign in to confirm your age" in e.stderr:
            error_msg += "\nThis video requires age verification."
        
        raise RuntimeError(error_msg)


def main():
    parser = argparse.ArgumentParser(description="YouTube helper for screenscribe Fabric integration")
    parser.add_argument("url", help="YouTube URL")
    parser.add_argument("--transcript-only", action="store_true", 
                       help="Extract transcript only (don't download video)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Check if yt-dlp is available
    if not check_ytdlp():
        sys.exit(1)
    
    try:
        if args.transcript_only:
            # Extract transcript and output JSON
            transcript_data = extract_youtube_transcript(args.url, args.verbose)
            print(json.dumps(transcript_data, indent=2, ensure_ascii=False))
        else:
            # Download video and output file path
            video_path = download_youtube_video(args.url, args.verbose)
            print(video_path)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()