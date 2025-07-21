#!/usr/bin/env python3
"""
Whisper wrapper script for Fabric integration
Transcribes video/audio files and outputs JSON for piping to Fabric patterns
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

def transcribe_with_faster_whisper(video_path: str, model: str = "base", language: Optional[str] = None) -> Dict[str, Any]:
    """Transcribe using faster-whisper (preferred for performance)"""
    try:
        from faster_whisper import WhisperModel
        
        # Use MLX backend if available on Apple Silicon
        device = "auto"
        compute_type = "float16"
        
        try:
            import platform
            if platform.system() == "Darwin" and platform.machine() == "arm64":
                # Try MLX first for Apple Silicon
                try:
                    import mlx_whisper
                    return transcribe_with_mlx(video_path, model, language)
                except ImportError:
                    pass
        except Exception:
            pass
        
        # Fall back to faster-whisper
        whisper_model = WhisperModel(model, device=device, compute_type=compute_type)
        
        segments, info = whisper_model.transcribe(
            video_path,
            language=language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Convert segments to list
        segments_list = []
        full_text = ""
        
        for i, segment in enumerate(segments):
            segment_dict = {
                "id": i,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }
            segments_list.append(segment_dict)
            full_text += segment.text.strip() + " "
        
        return {
            "text": full_text.strip(),
            "segments": segments_list,
            "language": info.language,
            "duration": segments_list[-1]["end"] if segments_list else 0,
            "backend": "faster-whisper"
        }
        
    except ImportError:
        # Fall back to openai-whisper
        return transcribe_with_openai_whisper(video_path, model, language)

def transcribe_with_mlx(video_path: str, model: str = "base", language: Optional[str] = None) -> Dict[str, Any]:
    """Transcribe using MLX Whisper for Apple Silicon GPU acceleration"""
    try:
        import mlx_whisper
        
        result = mlx_whisper.transcribe(
            video_path,
            model=model,
            language=language
        )
        
        # Format segments
        segments_list = []
        if "segments" in result:
            for i, segment in enumerate(result["segments"]):
                segment_dict = {
                    "id": i,
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0),
                    "text": segment.get("text", "").strip()
                }
                segments_list.append(segment_dict)
        
        return {
            "text": result.get("text", ""),
            "segments": segments_list,
            "language": result.get("language", "unknown"),
            "duration": segments_list[-1]["end"] if segments_list else 0,
            "backend": "mlx-whisper"
        }
        
    except ImportError as e:
        raise ImportError(f"MLX Whisper not available: {e}")

def transcribe_with_openai_whisper(video_path: str, model: str = "base", language: Optional[str] = None) -> Dict[str, Any]:
    """Transcribe using original OpenAI Whisper (fallback)"""
    try:
        import whisper
        
        whisper_model = whisper.load_model(model)
        result = whisper_model.transcribe(video_path, language=language)
        
        return {
            "text": result["text"],
            "segments": result["segments"],
            "language": result["language"],
            "duration": result["segments"][-1]["end"] if result["segments"] else 0,
            "backend": "openai-whisper"
        }
        
    except ImportError as e:
        raise ImportError(f"OpenAI Whisper not available: {e}")

def extract_audio_if_needed(input_path: str) -> str:
    """Extract audio from video if needed, return path to audio file"""
    input_path = Path(input_path)
    
    # If already an audio file, return as-is
    if input_path.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.aac']:
        return str(input_path)
    
    # Extract audio from video
    import subprocess
    
    temp_dir = Path(tempfile.gettempdir())
    audio_path = temp_dir / f"whisper_audio_{input_path.stem}.wav"
    
    try:
        subprocess.run([
            "ffmpeg", "-i", str(input_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            "-y", str(audio_path)
        ], check=True, capture_output=True)
        
        return str(audio_path)
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Audio extraction failed: {e}")
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

def main():
    parser = argparse.ArgumentParser(description="Whisper transcription wrapper for Fabric")
    parser.add_argument("input", help="Path to video or audio file")
    parser.add_argument("--model", "-m", default="base", 
                       choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
                       help="Whisper model size")
    parser.add_argument("--language", "-l", help="Force specific language (optional)")
    parser.add_argument("--backend", choices=["auto", "mlx", "faster-whisper", "openai-whisper"],
                       default="auto", help="Transcription backend to use")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Extract audio if needed
        if args.verbose:
            print(f"Processing: {args.input}", file=sys.stderr)
            
        audio_path = extract_audio_if_needed(args.input)
        
        # Transcribe based on backend preference
        if args.backend == "mlx":
            result = transcribe_with_mlx(audio_path, args.model, args.language)
        elif args.backend == "faster-whisper":
            result = transcribe_with_faster_whisper(audio_path, args.model, args.language)
        elif args.backend == "openai-whisper":
            result = transcribe_with_openai_whisper(audio_path, args.model, args.language)
        else:  # auto
            result = transcribe_with_faster_whisper(audio_path, args.model, args.language)
        
        # Clean up temporary audio file if created
        if audio_path != args.input:
            try:
                os.unlink(audio_path)
            except OSError:
                pass
        
        # Add metadata
        result["source_file"] = args.input
        result["model"] = args.model
        result["timestamp"] = __import__("time").time()
        
        if args.verbose:
            print(f"Transcription complete: {len(result['segments'])} segments, {result['duration']:.1f}s", file=sys.stderr)
        
        # Output JSON to stdout for piping to Fabric
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()