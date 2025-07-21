# Product Requirements Prompt: screenscribe

You are building **screenscribe**, a CLI tool that processes video/audio recordings (especially technical content) to produce structured Markdown or HTML notes that integrate spoken language and visual context. This PRP provides everything needed to implement a production-ready tool in one pass.

---

## Purpose

CLI tool optimized for technical content analysis, designed to bridge the gap between visual and verbal information in video content. Built for developers, technical professionals, and self-learners who need searchable, structured documentation from video sources where visual context (diagrams, charts, code demonstrations) is as important as spoken content.

## Core Principles

1. **Stream Processing**: Handle large videos without memory exhaustion using chunked processing
2. **Graceful Degradation**: Continue processing even if individual components fail (e.g., OCR fails but audio succeeds)
3. **User Feedback**: Clear progress indicators, meaningful error messages, and verbose logging options
4. **Extensibility**: Modular pipeline architecture allowing easy component swapping
5. **Local-First**: Capable of fully offline operation with local models

---

## Goal

Build a production-ready CLI tool that:
- Processes videos and screen recordings to extract both audio transcripts and visual keyframes
- Synthesizes audio and visual context using LLMs to create comprehensive, structured notes
- Outputs searchable Markdown/HTML with embedded thumbnails and temporal references
- Handles technical content where visual elements (diagrams, code, charts) are critical
- Provides accurate transcription beyond what YouTube auto-captions offer
- Works across macOS and Linux (Fedora) systems

## Why

- **Problem Solved**: Technical videos contain critical visual information that pure transcription misses
- **User Value**: Enables rapid knowledge extraction from hours of video content into searchable documents
- **Business Value**: Saves time for technical teams documenting meetings, tutorials, and presentations
- **Competitive Advantage**: Combines visual+audio analysis unlike speech-only tools
- **Integration**: Outputs standard Markdown/HTML for easy integration with knowledge bases

## What

### User-Visible Behavior

1. **Simple CLI invocation**: `screenscribe video.mp4 --output notes/`
2. **Progress feedback**: Real-time updates on transcription, frame extraction, synthesis
3. **Flexible output**: Markdown by default, HTML with embedded images optional
4. **Smart defaults**: Works out-of-the-box with sensible settings
5. **YouTube support**: Direct URL processing with `screenscribe https://youtube.com/...`

### Technical Requirements

- Process videos up to 2 hours in length
- Support common formats: MP4, MKV, MOV, WebM, AVI
- Generate notes with temporal markers for easy video navigation
- Thumbnail generation at 320px width for reasonable file sizes
- Configurable quality/speed tradeoffs

### Success Criteria

- [ ] CLI successfully processes a 5-minute technical video with default settings
- [ ] Transcription accuracy > 95% for clear speech (validated against manual transcript)
- [ ] Scene detection captures all major visual transitions
- [ ] LLM synthesis correctly associates visual and audio context
- [ ] Output Markdown renders correctly with embedded images
- [ ] Processing time < 2x video duration on modern hardware
- [ ] Graceful handling of videos without audio track
- [ ] Clear error messages for common failure modes

## All Needed Context

### Documentation & References

```yaml
# Core Libraries - MUST READ
- url: https://github.com/openai/whisper#available-models-and-languages
  why: Model selection guide - understand speed/accuracy tradeoffs for --whisper-model flag
  critical: medium model balances speed/accuracy, large-v3 is most accurate but slow

- url: https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp
  why: Python API for video downloading, not just CLI usage
  section: "Embedding YT-DLP"
  critical: Use extract_info() with download=False to get metadata first

- url: https://docs.litellm.ai/docs/routing
  why: LLM provider routing and fallback configuration
  critical: Set router timeout to prevent hanging on failed providers

- url: https://ffmpeg.org/ffmpeg-filters.html#select
  why: Scene detection filter syntax and threshold tuning
  section: "select, aselect"
  critical: scene detection threshold 0.3 works for most content, 0.1 for subtle changes

# Python Libraries
- url: https://typer.tiangolo.com/tutorial/commands/
  why: CLI command structure and error handling patterns
  critical: Use typer.Exit() with proper codes for scripting

- url: https://github.com/openai/openai-python
  why: If using OpenAI for LLM synthesis, async client patterns

# Similar Tools for Patterns
- url: https://github.com/xenova/whisper-web
  why: Example of Whisper integration with progress callbacks

- url: https://github.com/m-bain/whisperX
  why: Advanced whisper usage with word-level timestamps - study alignment approach

# Video Processing
- url: https://imageio.readthedocs.io/en/v2.31.5/userapi.html
  why: Alternative to OpenCV for frame extraction if needed

# Example Implementation Patterns
- file: examples/whisper_progress.py
  why: Shows how to add progress bars to Whisper transcription

- file: examples/scene_detection.sh
  why: FFmpeg command for scene detection that we'll wrap

- file: examples/litellm_router.py
  why: Production LiteLLM configuration with retries and fallbacks
```

### Current Codebase Tree

```bash
# Run: tree -I '__pycache__|*.pyc|.git'
screenscribe/
├── README.md
├── pyproject.toml          # Poetry/pip configuration
├── .env.example           # Example environment variables
├── src/
│   └── screenscribe/
│       ├── __init__.py
│       ├── cli.py         # Typer CLI entry point
│       ├── audio.py       # Whisper integration
│       ├── video.py       # Frame extraction & scene detection
│       ├── align.py       # Timestamp alignment logic
│       ├── synthesis.py   # LLM synthesis
│       ├── output.py      # Markdown/HTML generation
│       └── utils.py       # Logging, progress bars
├── tests/
│   ├── fixtures/
│   │   ├── sample_5s.mp4  # 5-second test video
│   │   └── README.md      # How to generate fixtures
│   ├── test_audio.py
│   ├── test_video.py
│   ├── test_synthesis.py
│   └── test_integration.py
└── scripts/
    ├── install_deps.sh    # System dependency installer
    └── test_e2e.sh       # End-to-end test script
```

### Desired Codebase Tree

```bash
screenscribe/
├── README.md                    # User documentation
├── DEVELOPMENT.md              # Developer guide
├── pyproject.toml              # Dependencies and project metadata
├── .env.example                # OPENAI_API_KEY=, LITELLM_CONFIG=
├── Makefile                    # Common commands
├── src/
│   └── screenscribe/
│       ├── __init__.py         # Package initialization
│       ├── __main__.py         # Entry point for python -m screenscribe
│       ├── cli.py              # Typer CLI implementation
│       ├── models.py           # Pydantic data models
│       ├── audio.py            # Audio extraction & transcription
│       ├── video.py            # Frame extraction & scene detection
│       ├── align.py            # Temporal alignment algorithm
│       ├── synthesis.py        # LLM-based synthesis
│       ├── output.py           # Markdown/HTML generation
│       ├── utils.py            # Logging, progress, helpers
│       └── config.py           # Configuration management
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── fixtures/
│   │   ├── sample_5s.mp4      # Short test video
│   │   ├── sample_30s.mp4     # Longer test video
│   │   ├── no_audio.mp4       # Edge case: video without audio
│   │   └── generate.sh        # Script to create fixtures
│   ├── test_audio.py          # Audio module tests
│   ├── test_video.py          # Video module tests  
│   ├── test_align.py          # Alignment tests
│   ├── test_synthesis.py      # Synthesis tests
│   ├── test_cli.py            # CLI tests
│   └── test_integration.py    # End-to-end tests
├── scripts/
│   ├── install_ffmpeg.sh      # Install ffmpeg on macOS/Linux
│   ├── download_models.py     # Pre-download Whisper models
│   └── benchmark.py           # Performance testing
├── examples/
│   ├── basic_usage.md         # Simple examples
│   ├── advanced_config.md     # Complex configurations
│   └── output_samples/        # Example outputs
└── .github/
    └── workflows/
        └── test.yml           # CI pipeline
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: Whisper gotchas
# 1. First run downloads models (~1.5GB for medium)
import whisper
import os
# Set custom model directory to avoid re-downloads
os.environ['WHISPER_CACHE_DIR'] = os.path.expanduser('~/.cache/whisper')

# 2. Whisper fails on very short audio (<0.5s)
# Always pad short audio with silence
if audio_duration < 0.5:
    audio = np.pad(audio, (0, int(0.5 * sample_rate)), mode='constant')

# 3. GPU memory errors with large models
# Fallback to CPU on CUDA out of memory
try:
    model = whisper.load_model(model_name, device="cuda")
except RuntimeError as e:
    if "out of memory" in str(e):
        print("WARNING: GPU out of memory, falling back to CPU")
        model = whisper.load_model(model_name, device="cpu")

# CRITICAL: yt-dlp gotchas  
# 1. Age-restricted videos need cookies
ydl_opts = {
    'cookiefile': 'cookies.txt',  # Export from browser
    'quiet': True,
    'no_warnings': True,
}

# 2. Some videos have multiple audio streams
# Always specify format to get best audio
ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

# CRITICAL: FFmpeg gotchas
# 1. Scene detection can be slow on high-res video
# Always scale down for scene detection
scene_cmd = f"ffmpeg -i {input} -vf 'scale=640:-1,select=gt(scene\,{threshold})' ..."

# 2. FFmpeg command varies by platform
# Use shutil.which() to find ffmpeg
ffmpeg_path = shutil.which('ffmpeg')
if not ffmpeg_path:
    raise RuntimeError("ffmpeg not found. Install with: brew install ffmpeg")

# CRITICAL: LiteLLM gotchas
# 1. Provider authentication varies
# Use environment variables for all providers
os.environ['OPENAI_API_KEY'] = config.openai_key
os.environ['ANTHROPIC_API_KEY'] = config.anthropic_key

# 2. Context window limits vary by model
# Check model_info before sending
from litellm import model_info
max_tokens = model_info[model_name]['max_tokens']

# CRITICAL: File system gotchas
# 1. Always use pathlib for cross-platform paths
from pathlib import Path
output_dir = Path(args.output).expanduser().resolve()

# 2. Sanitize filenames from video titles
import re
safe_filename = re.sub(r'[<>:"/\\|?*]', '_', video_title)
```

## Implementation Blueprint

### Data Models and Structure

```python
# src/screenscribe/models.py
from pydantic import BaseModel, Field, validator
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
    
    @validator('frame_path', 'thumbnail_path')
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
    output_format: str = Field(regex="^(markdown|html)$")
    whisper_model: str = "medium"
    llm_provider: str = "openai"
    no_fallback: bool = False
    sampling_mode: str = Field(regex="^(scene|interval)$")
    interval_seconds: float = 5.0
    scene_threshold: float = 0.3
    thumbnail_width: int = 320
    verbose: bool = False

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
```

### List of Tasks to Complete

```yaml
Task 1 - Project Setup:
  CREATE pyproject.toml:
    - NAME: screenscribe
    - PYTHON: ">=3.9,<3.12"  # Whisper compatibility
    - DEPENDENCIES:
      - typer = "^0.9.0"
      - openai-whisper = "^20231117"
      - opencv-python = "^4.8.0" 
      - yt-dlp = "^2024.1.0"
      - litellm = "^1.0.0"
      - pydantic = "^2.0.0"
      - rich = "^13.0.0"  # Progress bars
      - pillow = "^10.0.0"  # Thumbnail generation
      - numpy = "^1.24.0"
      - ffmpeg-python = "^0.2.0"
    - DEV-DEPENDENCIES:
      - pytest = "^7.4.0"
      - pytest-asyncio = "^0.21.0"
      - ruff = "^0.1.0"
      - mypy = "^1.7.0"
      - black = "^23.0.0"
      
  CREATE .env.example:
    - OPENAI_API_KEY=sk-...
    - ANTHROPIC_API_KEY=sk-ant-...
    - WHISPER_CACHE_DIR=~/.cache/whisper
    - LITELLM_LOG_LEVEL=INFO
    
  CREATE Makefile:
    ```makefile
    install:
        poetry install
        ./scripts/install_ffmpeg.sh
    
    test:
        poetry run pytest tests/ -v
    
    lint:
        poetry run ruff check src/ --fix
        poetry run mypy src/
    
    format:
        poetry run black src/ tests/
    ```

Task 2 - Core CLI Implementation (src/screenscribe/cli.py):
  IMPLEMENT using Typer:
    ```python
    import typer
    from pathlib import Path
    from typing import Optional
    import sys
    
    app = typer.Typer()
    
    @app.command()
    def main(
        input: str = typer.Argument(..., help="Video file or YouTube URL"),
        output: Path = typer.Option("./screenscribe_output", "--output", "-o"),
        format: str = typer.Option("markdown", "--format", "-f"),
        llm: str = typer.Option("openai", "--llm"),
        no_fallback: bool = typer.Option(False, "--nofallback"),
        whisper_model: str = typer.Option("medium", "--whisper-model"),
        sampling_mode: str = typer.Option("scene", "--sampling-mode"),
        interval: float = typer.Option(5.0, "--interval"),
        verbose: bool = typer.Option(False, "--verbose", "-v"),
    ):
        """Process video/audio to structured notes"""
        # Validate inputs
        if format not in ["markdown", "html"]:
            typer.echo("Error: format must be 'markdown' or 'html'", err=True)
            raise typer.Exit(1)
            
        # Setup logging
        setup_logging(verbose)
        
        # Create output directory
        output.mkdir(parents=True, exist_ok=True)
        
        # Process based on input type
        if input.startswith(("http://", "https://")):
            process_youtube(input, output, options)
        else:
            process_local_file(Path(input), output, options)
    ```

Task 3 - Audio Processing Module (src/screenscribe/audio.py):
  # Pseudocode for Whisper integration
  ```python
  import whisper
  import torch
  from pathlib import Path
  import subprocess
  import tempfile
  from rich.progress import Progress
  import numpy as np
  
  class AudioProcessor:
      def __init__(self, model_name: str = "medium"):
          # PATTERN: Cache model loading
          self.device = "cuda" if torch.cuda.is_available() else "cpu"
          
          # CRITICAL: Handle model download on first run
          try:
              self.model = whisper.load_model(model_name, device=self.device)
          except RuntimeError as e:
              if "out of memory" in str(e) and self.device == "cuda":
                  # FALLBACK: Use CPU if GPU OOM
                  self.model = whisper.load_model(model_name, device="cpu")
                  self.device = "cpu"
              else:
                  raise
      
      async def extract_audio(self, video_path: Path) -> Path:
          """Extract audio track from video"""
          # PATTERN: Use temp file for audio
          audio_path = Path(tempfile.mktemp(suffix=".wav"))
          
          # CRITICAL: Use ffmpeg-python for cross-platform
          cmd = [
              "ffmpeg", "-i", str(video_path),
              "-vn",  # No video
              "-acodec", "pcm_s16le",  # WAV format
              "-ar", "16000",  # 16kHz for Whisper
              "-ac", "1",  # Mono
              str(audio_path),
              "-y"  # Overwrite
          ]
          
          # GOTCHA: Check if video has audio stream
          probe_cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", 
                      "-show_entries", "stream=codec_type", "-of", "csv=p=0", 
                      str(video_path)]
          
          result = subprocess.run(probe_cmd, capture_output=True, text=True)
          if not result.stdout.strip():
              raise ValueError("Video has no audio stream")
              
          subprocess.run(cmd, check=True, capture_output=True)
          return audio_path
      
      def transcribe(self, audio_path: Path, language: str = None) -> dict:
          """Transcribe audio with progress callback"""
          # PATTERN: Progress callback for long operations
          with Progress() as progress:
              task = progress.add_task("Transcribing...", total=100)
              
              # CRITICAL: Use word_timestamps for alignment
              result = self.model.transcribe(
                  str(audio_path),
                  language=language,
                  word_timestamps=True,
                  verbose=False,
                  # PATTERN: Progress callback
                  progress_callback=lambda x: progress.update(task, completed=x*100)
              )
              
          return result
  ```

Task 4 - Video Processing Module (src/screenscribe/video.py):
  ```python
  import cv2
  import subprocess
  import json
  from pathlib import Path
  from typing import List, Tuple
  import numpy as np
  from PIL import Image
  
  class VideoProcessor:
      def __init__(self, sampling_mode: str = "scene", 
                   interval: float = 5.0,
                   scene_threshold: float = 0.3):
          self.sampling_mode = sampling_mode
          self.interval = interval
          self.scene_threshold = scene_threshold
      
      def extract_frames_scene(self, video_path: Path, output_dir: Path) -> List[FrameData]:
          """Extract frames using scene detection"""
          frames_dir = output_dir / "frames"
          frames_dir.mkdir(exist_ok=True)
          
          # CRITICAL: Scale down for performance
          # PATTERN: Two-pass approach - detect scenes, then extract full res
          
          # Pass 1: Detect scene timestamps
          detect_cmd = [
              "ffmpeg", "-i", str(video_path),
              "-vf", f"scale=640:-1,select='gt(scene,{self.scene_threshold})',metadata=print",
              "-f", "null", "-"
          ]
          
          result = subprocess.run(detect_cmd, capture_output=True, text=True)
          
          # Parse timestamps from metadata
          timestamps = []
          for line in result.stderr.split('\n'):
              if "pts_time:" in line:
                  # Extract timestamp
                  ts = float(line.split("pts_time:")[1].split()[0])
                  timestamps.append(ts)
          
          # Pass 2: Extract full resolution frames at timestamps
          frames = []
          for i, ts in enumerate(timestamps):
              frame_path = frames_dir / f"frame_{i:04d}.jpg"
              
              # GOTCHA: Seek before input for performance
              extract_cmd = [
                  "ffmpeg", "-ss", str(ts), "-i", str(video_path),
                  "-vframes", "1", "-q:v", "2",
                  str(frame_path), "-y"
              ]
              
              subprocess.run(extract_cmd, check=True, capture_output=True)
              
              # Create thumbnail
              thumbnail_path = self._create_thumbnail(frame_path, output_dir)
              
              frames.append(FrameData(
                  index=i,
                  timestamp=ts,
                  frame_path=frame_path,
                  thumbnail_path=thumbnail_path,
                  is_scene_change=True
              ))
          
          return frames
      
      def extract_frames_interval(self, video_path: Path, output_dir: Path) -> List[FrameData]:
          """Extract frames at regular intervals"""
          # PATTERN: Use OpenCV for interval extraction
          cap = cv2.VideoCapture(str(video_path))
          fps = cap.get(cv2.CAP_PROP_FPS)
          total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
          
          frames = []
          frame_interval = int(fps * self.interval)
          
          for i in range(0, total_frames, frame_interval):
              cap.set(cv2.CAP_PROP_POS_FRAMES, i)
              ret, frame = cap.read()
              
              if not ret:
                  break
                  
              timestamp = i / fps
              frame_path = output_dir / "frames" / f"frame_{len(frames):04d}.jpg"
              cv2.imwrite(str(frame_path), frame)
              
              # Create thumbnail
              thumbnail_path = self._create_thumbnail(frame_path, output_dir)
              
              frames.append(FrameData(
                  index=len(frames),
                  timestamp=timestamp,
                  frame_path=frame_path,
                  thumbnail_path=thumbnail_path,
                  is_scene_change=False
              ))
          
          cap.release()
          return frames
      
      def _create_thumbnail(self, frame_path: Path, output_dir: Path) -> Path:
          """Create thumbnail with fixed width"""
          thumb_dir = output_dir / "thumbnails"
          thumb_dir.mkdir(exist_ok=True)
          
          thumb_path = thumb_dir / f"thumb_{frame_path.stem}.jpg"
          
          # PATTERN: Use Pillow for high-quality resize
          img = Image.open(frame_path)
          
          # Calculate height to maintain aspect ratio
          width = 320
          height = int((width / img.width) * img.height)
          
          # GOTCHA: Use LANCZOS for quality
          img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
          img_resized.save(thumb_path, "JPEG", quality=85, optimize=True)
          
          return thumb_path
  ```

Task 5 - Alignment Module (src/screenscribe/align.py):
  ```python
  from typing import List, Dict
  from .models import TranscriptSegment, FrameData, AlignedContent
  
  class TemporalAligner:
      """Align transcript segments with video frames"""
      
      def __init__(self, time_window: float = 2.0):
          self.time_window = time_window
      
      def align(self, 
                transcript_segments: List[TranscriptSegment],
                frames: List[FrameData]) -> List[AlignedContent]:
          """Match transcript segments to frames based on temporal proximity"""
          
          aligned = []
          
          # PATTERN: Build time index for efficient lookup
          # Create sorted list of (time, segment) tuples
          time_index = []
          for seg in transcript_segments:
              time_index.append((seg.start, seg))
              time_index.append((seg.end, seg))
          time_index.sort(key=lambda x: x[0])
          
          for frame in frames:
              # Find segments within time window of frame
              window_start = frame.timestamp - self.time_window
              window_end = frame.timestamp + self.time_window
              
              # ALGORITHM: Binary search for efficiency
              relevant_segments = []
              
              # Find all segments that overlap with window
              for seg in transcript_segments:
                  # Check if segment overlaps with window
                  if seg.end >= window_start and seg.start <= window_end:
                      relevant_segments.append(seg)
              
              # GOTCHA: Handle frames with no nearby transcript
              if not relevant_segments:
                  # Look for nearest segment
                  nearest = min(transcript_segments, 
                              key=lambda s: abs(s.start - frame.timestamp))
                  relevant_segments = [nearest]
              
              aligned.append(AlignedContent(
                  frame=frame,
                  transcript_segments=relevant_segments,
                  time_window=self.time_window
              ))
          
          return aligned
  ```

Task 6 - LLM Synthesis Module (src/screenscribe/synthesis.py):
  ```python
  from litellm import Router, completion
  import asyncio
  from typing import List, Optional
  import base64
  from pathlib import Path
  
  class ContentSynthesizer:
      def __init__(self, 
                   provider: str = "openai",
                   model: str = None,
                   no_fallback: bool = False):
          
          # PATTERN: LiteLLM router for provider flexibility
          if not no_fallback:
              # Setup router with fallbacks
              self.router = Router(
                  model_list=[
                      {
                          "model_name": "primary",
                          "litellm_params": {
                              "model": f"{provider}/{model or 'gpt-4-vision-preview'}",
                              "api_key": os.getenv(f"{provider.upper()}_API_KEY"),
                          },
                      },
                      {
                          "model_name": "fallback", 
                          "litellm_params": {
                              "model": "openai/gpt-4-vision-preview",
                              "api_key": os.getenv("OPENAI_API_KEY"),
                          },
                      },
                  ],
                  fallbacks=[{"primary": ["fallback"]}],
                  timeout=30,
                  retry_policy={"initial_retry_delay": 1, "max_retries": 3}
              )
          else:
              # Single provider, no fallback
              self.model = f"{provider}/{model}"
      
      async def synthesize_frame(self, aligned: AlignedContent) -> SynthesisResult:
          """Synthesize summary for a single frame with context"""
          
          # PATTERN: Encode image for vision models
          image_base64 = self._encode_image(aligned.frame.thumbnail_path)
          
          # Build prompt with transcript context
          transcript_text = aligned.get_transcript_text()
          
          prompt = f"""You are analyzing a technical video frame with its corresponding audio transcript.

Frame timestamp: {aligned.frame.timestamp_str}
Transcript (±{aligned.time_window}s): "{transcript_text}"

Analyze this frame and create a structured summary that:
1. Describes what is visually shown
2. Explains how it relates to what is being said
3. Extracts key technical points or concepts
4. Notes any important visual elements (diagrams, code, charts)

Provide response in this JSON format:
{{
  "summary": "Brief synthesis of audio and visual content",
  "visual_description": "What is shown in the frame",
  "key_points": ["point 1", "point 2", ...]
}}"""

          # CRITICAL: Handle vision API properly
          messages = [
              {
                  "role": "user",
                  "content": [
                      {"type": "text", "text": prompt},
                      {
                          "type": "image_url",
                          "image_url": {
                              "url": f"data:image/jpeg;base64,{image_base64}",
                              "detail": "low"  # Use "low" for cost efficiency
                          }
                      }
                  ]
              }
          ]
          
          # PATTERN: Async for parallel processing
          if hasattr(self, 'router'):
              response = await self.router.acompletion(
                  model="primary",
                  messages=messages,
                  response_format={"type": "json_object"},
                  temperature=0.3,
                  max_tokens=500
              )
          else:
              response = await completion(
                  model=self.model,
                  messages=messages,
                  response_format={"type": "json_object"},
                  temperature=0.3,
                  max_tokens=500
              )
          
          # Parse response
          import json
          result_data = json.loads(response.choices[0].message.content)
          
          return SynthesisResult(
              frame_timestamp=aligned.frame.timestamp,
              summary=result_data.get("summary", ""),
              visual_description=result_data.get("visual_description"),
              key_points=result_data.get("key_points", [])
          )
      
      async def synthesize_all(self, 
                             aligned_content: List[AlignedContent],
                             max_concurrent: int = 5) -> List[SynthesisResult]:
          """Process all frames with concurrency limit"""
          
          # PATTERN: Semaphore for API rate limiting
          semaphore = asyncio.Semaphore(max_concurrent)
          
          async def process_with_semaphore(aligned):
              async with semaphore:
                  return await self.synthesize_frame(aligned)
          
          # CRITICAL: Gather with exception handling
          tasks = [process_with_semaphore(a) for a in aligned_content]
          
          results = []
          for future in asyncio.as_completed(tasks):
              try:
                  result = await future
                  results.append(result)
              except Exception as e:
                  # Log error but continue processing
                  print(f"Synthesis error: {e}")
                  # Create placeholder result
                  results.append(SynthesisResult(
                      frame_timestamp=0,
                      summary="[Error during synthesis]"
                  ))
          
          # Sort by timestamp
          results.sort(key=lambda r: r.frame_timestamp)
          return results
      
      def _encode_image(self, image_path: Path) -> str:
          """Encode image to base64"""
          with open(image_path, "rb") as f:
              return base64.b64encode(f.read()).decode()
  ```

Task 7 - Output Generation Module (src/screenscribe/output.py):
  ```python
  from pathlib import Path
  from typing import List
  from datetime import datetime
  import json
  
  class OutputGenerator:
      def __init__(self, format: str = "markdown"):
          self.format = format
      
      def generate(self, result: ProcessingResult, output_dir: Path) -> Path:
          """Generate final output file"""
          
          if self.format == "markdown":
              return self._generate_markdown(result, output_dir)
          else:
              return self._generate_html(result, output_dir)
      
      def _generate_markdown(self, result: ProcessingResult, output_dir: Path) -> Path:
          """Generate Markdown output"""
          
          output_file = output_dir / "notes.md"
          
          # PATTERN: Use string builder for efficiency
          lines = []
          
          # Header
          lines.append(f"# {result.video_metadata.title}")
          lines.append(f"\n**Duration:** {result.video_metadata.duration_str}")
          lines.append(f"**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
          
          if result.video_metadata.youtube_url:
              lines.append(f"**Source:** [{result.video_metadata.youtube_url}]({result.video_metadata.youtube_url})")
          
          lines.append("\n---\n")
          
          # Executive Summary (if we want to add this)
          lines.append("## Summary\n")
          lines.append("[AI-generated executive summary could go here]\n")
          
          # Timeline
          lines.append("## Timeline\n")
          
          # Process each synthesis result
          for i, synthesis in enumerate(result.synthesis_results):
              # Find corresponding aligned content
              aligned = result.aligned_content[i]
              
              # Section header with timestamp
              lines.append(f"### [{synthesis.frame_timestamp:.1f}s] {aligned.frame.timestamp_str}")
              
              # Thumbnail with link to full frame
              rel_thumb = aligned.frame.thumbnail_path.relative_to(output_dir)
              rel_frame = aligned.frame.frame_path.relative_to(output_dir)
              
              lines.append(f"\n[![Frame]({rel_thumb})]({rel_frame})\n")
              
              # Transcript
              transcript = aligned.get_transcript_text()
              if transcript:
                  lines.append(f"**Transcript:** \"{transcript}\"\n")
              
              # Synthesis
              lines.append(f"**Summary:** {synthesis.summary}\n")
              
              # Visual description if available
              if synthesis.visual_description:
                  lines.append(f"**Visual:** {synthesis.visual_description}\n")
              
              # Key points
              if synthesis.key_points:
                  lines.append("**Key Points:**")
                  for point in synthesis.key_points:
                      lines.append(f"- {point}")
                  lines.append("")
              
              lines.append("---\n")
          
          # Footer
          lines.append(f"\n*Generated by screenscribe v1.0.0*")
          
          # Write file
          output_file.write_text("\n".join(lines))
          
          # Also save raw JSON for reprocessing
          json_file = output_dir / "processing_result.json"
          result.save(json_file)
          
          return output_file
      
      def _generate_html(self, result: ProcessingResult, output_dir: Path) -> Path:
          """Generate HTML output with embedded styles"""
          
          output_file = output_dir / "notes.html"
          
          # PATTERN: Self-contained HTML
          html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{result.video_metadata.title} - Notes</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        .frame-section {{ margin: 2em 0; border-bottom: 1px solid #eee; padding-bottom: 2em; }}
        .timestamp {{ color: #0066cc; font-weight: bold; }}
        .thumbnail {{ max-width: 320px; border: 1px solid #ddd; cursor: pointer; }}
        .transcript {{ background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        .summary {{ font-weight: 500; }}
        .key-points {{ margin-left: 20px; }}
        .visual-desc {{ color: #666; font-style: italic; }}
    </style>
</head>
<body>
    <h1>{result.video_metadata.title}</h1>
    <p><strong>Duration:</strong> {result.video_metadata.duration_str}<br>
       <strong>Processed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <hr>
"""
          
          # Add content sections
          for i, synthesis in enumerate(result.synthesis_results):
              aligned = result.aligned_content[i]
              
              # Make paths relative for portability
              rel_thumb = aligned.frame.thumbnail_path.relative_to(output_dir)
              rel_frame = aligned.frame.frame_path.relative_to(output_dir)
              
              html += f"""
    <div class="frame-section">
        <h2><span class="timestamp">{aligned.frame.timestamp_str}</span></h2>
        <a href="{rel_frame}" target="_blank">
            <img src="{rel_thumb}" class="thumbnail" alt="Frame at {aligned.frame.timestamp_str}">
        </a>
        <div class="transcript">
            <strong>Transcript:</strong> "{aligned.get_transcript_text()}"
        </div>
        <p class="summary"><strong>Summary:</strong> {synthesis.summary}</p>
"""
              
              if synthesis.visual_description:
                  html += f'        <p class="visual-desc">Visual: {synthesis.visual_description}</p>\n'
              
              if synthesis.key_points:
                  html += '        <div class="key-points"><strong>Key Points:</strong><ul>\n'
                  for point in synthesis.key_points:
                      html += f'            <li>{point}</li>\n'
                  html += '        </ul></div>\n'
              
              html += '    </div>\n'
          
          html += """
    <hr>
    <p><em>Generated by screenscribe v1.0.0</em></p>
</body>
</html>"""
          
          output_file.write_text(html)
          return output_file
  ```

Task 8 - Main Processing Pipeline (src/screenscribe/cli.py continued):
  ```python
  async def process_video(input_path: Path, options: ProcessingOptions) -> ProcessingResult:
      """Main processing pipeline"""
      
      # Initialize components
      audio_processor = AudioProcessor(options.whisper_model)
      video_processor = VideoProcessor(
          options.sampling_mode,
          options.interval_seconds,
          options.scene_threshold
      )
      aligner = TemporalAligner()
      synthesizer = ContentSynthesizer(
          options.llm_provider,
          no_fallback=options.no_fallback
      )
      
      # Step 1: Extract metadata
      metadata = extract_video_metadata(input_path)
      
      # Step 2: Extract and transcribe audio
      print("🎵 Extracting audio...")
      audio_path = await audio_processor.extract_audio(input_path)
      
      print("🎤 Transcribing audio...")
      transcript_data = audio_processor.transcribe(audio_path)
      
      # Save transcript
      transcript_file = options.output_dir / "transcript.json"
      transcript_file.write_text(json.dumps(transcript_data, indent=2))
      
      # Parse segments
      segments = [TranscriptSegment(**seg) for seg in transcript_data["segments"]]
      
      # Step 3: Extract frames
      print("🎬 Extracting frames...")
      if options.sampling_mode == "scene":
          frames = video_processor.extract_frames_scene(input_path, options.output_dir)
      else:
          frames = video_processor.extract_frames_interval(input_path, options.output_dir)
      
      print(f"📸 Extracted {len(frames)} frames")
      
      # Step 4: Align transcript with frames
      print("🔗 Aligning transcript with frames...")
      aligned = aligner.align(segments, frames)
      
      # Step 5: Synthesize content
      print("🤖 Synthesizing content...")
      synthesis_results = await synthesizer.synthesize_all(aligned)
      
      # Step 6: Generate output
      print("📝 Generating output...")
      output_gen = OutputGenerator(options.output_format)
      output_file = output_gen.generate(result, options.output_dir)
      
      # Clean up temp audio
      audio_path.unlink()
      
      return ProcessingResult(
          video_metadata=metadata,
          processing_options=options,
          transcript_segments=segments,
          frames=frames,
          aligned_content=aligned,
          synthesis_results=synthesis_results,
          output_file=output_file,
          processing_time=time.time() - start_time
      )
  ```

Task 9 - Testing Infrastructure:
  CREATE tests/conftest.py:
    - Pytest fixtures for sample videos
    - Mock LLM responses
    - Temp directory handling
    
  CREATE tests/test_audio.py:
    - Test Whisper model loading
    - Test audio extraction
    - Test transcription with short audio
    
  CREATE tests/test_video.py:
    - Test scene detection
    - Test interval extraction
    - Test thumbnail generation
    
  CREATE tests/test_integration.py:
    - End-to-end test with 15-second fixture
    - Test error handling (no audio, corrupt video)
    - Test YouTube download

Task 10 - Scripts and Documentation:
  CREATE scripts/install_ffmpeg.sh:
    ```bash
    #!/bin/bash
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    elif [[ -f /etc/fedora-release ]]; then
        sudo dnf install ffmpeg
    else
        echo "Please install ffmpeg manually"
        exit 1
    fi
    ```
    
  CREATE README.md:
    - Installation instructions
    - Usage examples
    - Troubleshooting guide
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check src/ tests/ --fix
mypy src/ --python-version 3.9
black src/ tests/ --check

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```bash
# Run individual test modules first
pytest tests/test_audio.py -v
pytest tests/test_video.py -v
pytest tests/test_align.py -v

# Then run all tests
pytest tests/ -v --cov=src/screenscribe --cov-report=term-missing

# Expected: 80%+ coverage, all tests pass
```

### Level 3: Integration Test
```bash
# Test with provided fixture
python -m screenscribe tests/fixtures/sample_5s.mp4 \
    --output test_output \
    --whisper-model tiny \
    --format markdown

# Verify output exists
ls -la test_output/
# Should see: transcript.json, frames/, thumbnails/, notes.md

# Test error handling
python -m screenscribe tests/fixtures/no_audio.mp4 --output test_output2
# Should handle gracefully with clear error
```

### Level 4: Performance Test
```bash
# Test with longer video
time python -m screenscribe tests/fixtures/sample_30s.mp4 \
    --output perf_test \
    --whisper-model base

# Should complete in < 60 seconds
```

## Integration Points

```yaml
EXTERNAL SERVICES:
  - OpenAI API:
      endpoint: https://api.openai.com/v1/
      auth: Bearer token via OPENAI_API_KEY
      rate_limit: Handle 429 errors with exponential backoff
      
  - YouTube (via yt-dlp):
      cookies: Optional for age-restricted content
      format: Best video + audio, fallback to best
      
  - Local LLMs (via LiteLLM):
      endpoint: Configurable via LITELLM_API_BASE
      models: Support Ollama, LocalAI, etc.

SYSTEM DEPENDENCIES:
  - ffmpeg:
      version: 4.0+ required
      features: libx264, aac codec support
      install: Platform-specific installers provided
      
  - CUDA (optional):
      version: 11.0+ for GPU acceleration
      fallback: Automatic CPU fallback

FILE SYSTEM:
  - Output structure:
      preserve: Relative paths in output for portability
      cleanup: Remove temporary files after processing
      
  - Model cache:
      location: ~/.cache/whisper/ or WHISPER_CACHE_DIR
      size: ~1.5GB per model

ERROR HANDLING:
  - Network failures: 3 retries with exponential backoff
  - API limits: Respect rate limits, queue requests
  - File errors: Clear messages with recovery suggestions
  - Memory errors: Suggest smaller models or CPU mode
```

## Anti-Patterns to Avoid

```markdown
❌ DON'T load entire videos into memory
   ✅ DO stream process with ffmpeg

❌ DON'T use synchronous I/O in async functions  
   ✅ DO use asyncio subprocess for external commands

❌ DON'T assume dependencies are installed
   ✅ DO check with shutil.which() and provide clear install instructions

❌ DON'T ignore API rate limits
   ✅ DO implement backoff and respect headers

❌ DON'T hardcode paths or use OS-specific separators
   ✅ DO use pathlib.Path everywhere

❌ DON'T catch all exceptions blindly
   ✅ DO handle specific errors with appropriate messages

❌ DON'T process frames at full resolution for analysis
   ✅ DO create thumbnails for LLM processing

❌ DON'T skip validation of video codecs
   ✅ DO probe video format before processing

❌ DON'T forget to clean up temporary files
   ✅ DO use context managers or explicit cleanup

❌ DON'T send huge contexts to LLMs
   ✅ DO limit transcript segments to relevant time windows
```

## Final Validation Checklist

- [ ] All unit tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] No type errors: `mypy src/`
- [ ] Integration test succeeds with sample video
- [ ] Graceful handling of edge cases (no audio, corrupt video)
- [ ] Performance target met (< 2x video duration)
- [ ] Output renders correctly (images load, formatting preserved)
- [ ] Clear error messages for common failures
- [ ] Installation guide works on macOS and Linux
- [ ] API keys properly configured via environment
- [ ] Memory usage stays reasonable for long videos
- [ ] Progress indicators show during long operations

---

## Assistant Implementation Notes

When implementing based on this PRP:

1. **Start with project setup** - Get dependencies and structure right first
2. **Implement in order** - Each module builds on previous ones
3. **Test as you go** - Don't wait until the end to test
4. **Use the patterns** - Copy error handling and logging patterns exactly
5. **Handle errors gracefully** - Users should understand what went wrong
6. **Optimize later** - Get it working first, then improve performance

This PRP contains everything needed to implement screenscribe successfully. The validation loops ensure quality at each step. 