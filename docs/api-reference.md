# API Reference

This document provides a comprehensive reference for screenscribe's internal modules and APIs. This is primarily useful for developers who want to contribute to the project or integrate screenscribe into other applications.

> 📖 **For user documentation**, see the **[User Manual](USER_MANUAL.md)** which provides complete usage guidance, prompt customization, and troubleshooting.
> 
> 👨‍💻 **For development context**, see the **[Development Guide](DEVELOPMENT.md)** which explains the WHY → HOW → WHAT narrative and architecture decisions.

## Module Architecture

screenscribe follows a modular architecture with clear separation of concerns:

```
src/screenscribe/
├── cli.py          # CLI interface and argument parsing
├── models.py       # Pydantic data models
├── audio.py        # Audio processing with Whisper
├── video.py        # Video processing with OpenCV/FFmpeg
├── align.py        # Temporal alignment algorithms
├── synthesis.py    # LLM-based content synthesis
├── output.py       # Output generation (Markdown/HTML)
├── utils.py        # Utility functions
└── config.py       # Configuration management
```

## Core Data Models

### TranscriptSegment
Represents a segment of transcribed audio with timing information.

```python
class TranscriptSegment(BaseModel):
    id: int                           # Segment identifier
    seek: int                         # Seek position in milliseconds
    start: float                      # Start time in seconds
    end: float                        # End time in seconds
    text: str                         # Transcribed text
    tokens: List[int]                 # Token IDs from Whisper
    temperature: float                # Generation temperature
    avg_logprob: float               # Average log probability
    compression_ratio: float          # Text compression ratio
    no_speech_prob: float            # No speech probability
    words: Optional[List[WordTiming]] # Word-level timing (optional)
    
    @property
    def duration(self) -> float       # Segment duration
    
    @property
    def timestamp_str(self) -> str    # Formatted timestamp [HH:MM:SS]
```

### FrameData
Represents an extracted video frame with metadata.

```python
class FrameData(BaseModel):
    index: int                        # Frame index
    timestamp: float                  # Time in video (seconds)
    frame_path: Path                  # Path to full-size frame image
    thumbnail_path: Path              # Path to thumbnail image
    is_scene_change: bool = True      # Whether frame is a scene change
    ocr_text: Optional[str] = None    # OCR text (if available)
    
    @property
    def timestamp_str(self) -> str    # Formatted timestamp [HH:MM:SS]
```

### AlignedContent
Pairs a video frame with relevant transcript segments.

```python
class AlignedContent(BaseModel):
    frame: FrameData                  # Video frame data
    transcript_segments: List[TranscriptSegment]  # Associated segments
    time_window: float = 2.0          # Time window used for alignment
    
    def get_transcript_text(self) -> str  # Combined transcript text
```

### SynthesisResult
Contains LLM analysis results for a frame.

```python
class SynthesisResult(BaseModel):
    frame_timestamp: float            # Frame timestamp
    summary: str                      # AI-generated summary
    visual_description: Optional[str] # Visual content description
    key_points: List[str] = []       # Extracted key points
```

### ProcessingOptions
User-specified processing configuration.

```python
class ProcessingOptions(BaseModel):
    output_dir: Path                  # Output directory
    output_format: str               # "markdown" or "html"
    whisper_model: str = "medium"    # Whisper model size
    llm_provider: str = "openai"     # LLM provider
    no_fallback: bool = False        # Disable LLM fallbacks
    sampling_mode: str              # "scene" or "interval"
    interval_seconds: float = 5.0   # Interval sampling rate
    scene_threshold: float = 0.3    # Scene detection threshold
    thumbnail_width: int = 320      # Thumbnail width in pixels
    verbose: bool = False           # Enable verbose logging
    prompts_dir: Optional[Path] = None  # Custom prompts directory
```

## Audio Processing Module

### AudioProcessor
Handles audio extraction and transcription using faster-whisper.

```python
class AudioProcessor:
    def __init__(self, model_name: str = "medium")
        """Initialize with faster-whisper model."""
    
    async def extract_audio(self, video_path: Path) -> Path
        """Extract audio track from video file."""
    
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> Dict[str, Any]
        """Transcribe audio using faster-whisper with VAD."""
    
    def get_model_info(self) -> Dict[str, Any]
        """Get information about loaded model."""
```

**Key Features:**
- Automatic GPU/CPU fallback with enhanced memory management
- Voice Activity Detection (VAD) for improved transcription quality
- 2-5x faster processing than openai-whisper
- Efficient compute type optimization (float16 for GPU, int8 for CPU)
- Progress tracking during transcription
- Audio format validation and conversion
- Word-level timestamp extraction with improved accuracy

## Video Processing Module

### VideoProcessor
Handles video frame extraction using scene detection or interval sampling.

```python
class VideoProcessor:
    def __init__(
        self, 
        sampling_mode: str = "scene", 
        interval: float = 5.0,
        scene_threshold: float = 0.3,
        thumbnail_width: int = 320
    )
        """Initialize video processor with sampling parameters."""
    
    def extract_frames_scene(self, video_path: Path, output_dir: Path) -> List[FrameData]
        """Extract frames using scene detection."""
    
    def extract_frames_interval(self, video_path: Path, output_dir: Path) -> List[FrameData]
        """Extract frames at regular intervals."""
    
    def get_processing_info(self) -> dict
        """Get processor configuration information."""
```

**Key Features:**
- Scene detection using FFmpeg filters
- High-quality thumbnail generation with Pillow
- Automatic scaling for performance optimization
- Cross-platform video format support

## Temporal Alignment Module

### TemporalAligner
Aligns transcript segments with video frames based on temporal proximity.

```python
class TemporalAligner:
    def __init__(self, time_window: float = 2.0)
        """Initialize with time window for alignment."""
    
    def align(
        self, 
        transcript_segments: List[TranscriptSegment],
        frames: List[FrameData]
    ) -> List[AlignedContent]
        """Align transcript segments with video frames."""
    
    def get_alignment_stats(self, aligned_content: List[AlignedContent]) -> Dict[str, float]
        """Get statistics about alignment quality."""
```

**Algorithm Details:**
- Uses configurable time windows (default: ±2 seconds)
- Binary search optimization for large datasets
- Graceful handling of frames without nearby transcript
- Quality metrics for alignment assessment

## LLM Synthesis Module

### ContentSynthesizer
Synthesizes frame and transcript content using vision-capable LLMs.

```python
class ContentSynthesizer:
    def __init__(
        self, 
        provider: str = "openai",
        model: Optional[str] = None,
        no_fallback: bool = False,
        prompts_dir: Optional[Path] = None
    )
        """Initialize with LLM configuration."""
    
    async def synthesize_frame(self, aligned: AlignedContent) -> SynthesisResult
        """Synthesize content for a single frame."""
    
    async def synthesize_all(
        self, 
        aligned_content: List[AlignedContent],
        max_concurrent: int = 5
    ) -> List[SynthesisResult]
        """Process all frames with concurrency control."""
    
    def get_synthesis_info(self) -> Dict[str, Any]
        """Get synthesizer configuration."""
```

**Key Features:**
- Multi-provider support (OpenAI, Anthropic)
- Automatic fallback between providers
- Configurable concurrency limits for rate limiting
- Custom prompt template loading from markdown files
- Base64 image encoding for vision models

## Output Generation Module

### OutputGenerator
Generates final output in Markdown or HTML format.

```python
class OutputGenerator:
    def __init__(self, format: str = "markdown")
        """Initialize with output format."""
    
    def generate(self, result: ProcessingResult, output_dir: Path) -> Path
        """Generate final output file."""
```

**Output Features:**
- Responsive HTML with embedded CSS
- Markdown with proper image links
- Timeline-based organization
- Embedded thumbnails with full-frame links
- Processing metadata inclusion

## Utility Functions

### Configuration Management
```python
# Load prompt templates
load_prompt_template(prompt_name: str, prompts_dir: Optional[Path] = None) -> str

# Format prompt templates  
format_prompt_template(template: str, **kwargs) -> str

# Video metadata extraction
get_video_metadata(video_path: Path) -> dict

# Dependency checking
check_dependencies() -> list[str]

# Progress bars
create_progress_bar(description: str) -> Progress
```

### File Operations
```python
# Safe filename sanitization
sanitize_filename(filename: str) -> str

# Cross-platform path handling (uses pathlib.Path throughout)
```

## Error Handling Patterns

screenscribe uses consistent error handling patterns:

```python
# Configuration validation
config.validate() -> List[str]  # Returns list of error messages

# Graceful degradation
try:
    result = primary_operation()
except SpecificError:
    result = fallback_operation()
    logger.warning("Fell back to alternative method")

# User-friendly error messages
raise RuntimeError(f"Clear description: {technical_details}")
```

## Extension Points

### Custom Prompt Templates
Create new prompt templates by:
1. Adding markdown files to `prompts/` directory
2. Using `{variable_name}` for template substitution
3. Following the established JSON output format

### Additional LLM Providers
Extend LLM support by:
1. Adding provider configuration to `ContentSynthesizer`
2. Implementing authentication in `_setup_llm()`
3. Adding fallback logic in router configuration

### New Output Formats
Add output formats by:
1. Creating new methods in `OutputGenerator`
2. Adding format validation in `ProcessingOptions`
3. Updating CLI argument parsing

## Performance Considerations

### Memory Management
- Streams large videos without loading entirely into memory
- Cleans up temporary files after processing
- Uses efficient thumbnail generation with proper scaling

### Concurrency
- Async/await patterns for I/O operations
- Configurable concurrency limits for API calls
- Progress tracking for long-running operations

### Caching
- Whisper model caching via environment variables
- Prompt template caching after first load
- Reuses video metadata across processing steps

## Testing Architecture

### Test Structure
```
tests/
├── conftest.py           # Pytest fixtures
├── test_models.py        # Data model tests
├── test_audio.py         # Audio processing tests
├── test_video.py         # Video processing tests
├── test_align.py         # Alignment algorithm tests
├── test_synthesis.py     # LLM synthesis tests
└── test_integration.py   # End-to-end tests
```

### Mock Patterns
- Mock LLM responses for consistent testing
- Fixture videos for predictable test scenarios
- Temporary directories for file operations

## Development Workflow

### Adding New Features
1. Define data models in `models.py`
2. Implement core logic in appropriate module
3. Add configuration options to `ProcessingOptions`
4. Update CLI argument parsing
5. Add comprehensive tests
6. Update documentation

### Code Quality Standards
- Type hints for all public functions
- Docstrings following Google style
- Error handling with user-friendly messages
- Logging for debugging and monitoring
- Cross-platform compatibility

This API reference provides the foundation for understanding and extending screenscribe's architecture. For implementation examples, see the source code and test suite.