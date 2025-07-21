# Product Requirements Prompt (PRP): Multi-Backend Audio Transcription

## Context & Problem Statement

The current screenscribe implementation uses faster-whisper for audio transcription, which does not support Apple Silicon GPU acceleration (MPS/Metal). This results in suboptimal performance on M-series Macs, using only CPU cores when GPU acceleration could provide 2-3x speedup. We need a multi-backend system that automatically selects the best transcription engine for each platform while maintaining cross-platform compatibility.

## Success Criteria

1. **Performance**: 
   - M3 Ultra achieves <80s transcription for 10-min audio (vs current ~200s)
   - Maintains current performance on Linux/Windows with NVIDIA GPUs
   - Graceful fallback to CPU with acceptable performance

2. **Compatibility**:
   - Works on macOS (Intel & Apple Silicon), Linux, Windows
   - No breaking changes to existing CLI interface
   - Maintains output format compatibility

3. **User Experience**:
   - Auto-detects best backend (no manual configuration required)
   - Clear logging of backend selection
   - Optional manual backend override via CLI flag

## All Needed Context

### Documentation & Resources

1. **MLX Whisper** (Apple Silicon GPU)
   - Repo: https://github.com/ml-explore/mlx-examples/tree/main/whisper
   - Install: `pip install mlx-whisper`
   - Models: https://huggingface.co/collections/mlx-community/whisper-663256f9964fbb1177db93dc
   - Example:
   ```python
   import mlx_whisper
   result = mlx_whisper.transcribe(
       "audio.mp3",
       path_or_hf_repo="mlx-community/whisper-large-v3"
   )
   ```

2. **faster-whisper** (Current, CUDA support)
   - Docs: https://github.com/SYSTRAN/faster-whisper
   - GPU Issue: https://github.com/SYSTRAN/faster-whisper/issues/231
   - Supported devices: "cpu", "cuda" (NOT "mps")

3. **whisper.cpp** (High performance)
   - Repo: https://github.com/ggerganov/whisper.cpp
   - CoreML: https://github.com/ggerganov/whisper.cpp#core-ml-support
   - Python wrapper: https://github.com/carloscdias/whisper-cpp-python

### Known Gotchas & Workarounds

1. **MLX Platform Detection**:
   ```python
   # GOTCHA: platform.machine() returns 'arm64' not 'aarch64' on macOS
   if platform.system() == "Darwin" and platform.machine() == "arm64":
       # Apple Silicon detected
   ```

2. **Import Guards Required**:
   ```python
   # GOTCHA: MLX only available on Apple Silicon, must guard imports
   try:
       import mlx_whisper
       MLX_AVAILABLE = True
   except ImportError:
       MLX_AVAILABLE = False
   ```

3. **Model Name Mapping**:
   ```python
   # GOTCHA: Different backends use different model naming
   MODEL_MAPPING = {
       "mlx": {
           "tiny": "mlx-community/whisper-tiny",
           "base": "mlx-community/whisper-base", 
           "small": "mlx-community/whisper-small",
           "medium": "mlx-community/whisper-medium",
           "large": "mlx-community/whisper-large-v3"
       },
       "faster-whisper": {
           # Uses standard names: tiny, base, small, medium, large-v3
       }
   }
   ```

4. **Output Format Normalization**:
   ```python
   # GOTCHA: Each backend returns different output format
   # MLX returns: {"text": str, "segments": list, "language": str}
   # faster-whisper returns: segments generator + info tuple
   # Must normalize to consistent format
   ```

## Data Models

```python
# src/screenscribe/models.py

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class TranscriptionSegment(BaseModel):
    """Normalized segment format across all backends."""
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int] = []
    temperature: float = 0.0
    avg_logprob: float = 0.0
    compression_ratio: float = 0.0
    no_speech_prob: float = 0.0
    words: Optional[List[Dict[str, Any]]] = None

class TranscriptionResult(BaseModel):
    """Normalized transcription result."""
    text: str
    segments: List[TranscriptionSegment]
    language: str
    duration: Optional[float] = None
    
class BackendInfo(BaseModel):
    """Information about an audio backend."""
    name: Literal["mlx", "faster-whisper", "whisper-cpp"]
    available: bool
    device: str
    compute_type: Optional[str] = None
    reason: Optional[str] = None  # Why not available
```

## Implementation Tasks

### Task 1: Create Backend Abstraction Layer

```python
# src/screenscribe/audio_backends.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
import platform
import logging

from .models import TranscriptionResult, BackendInfo

logger = logging.getLogger(__name__)

class WhisperBackend(ABC):
    """Abstract base class for Whisper backends."""
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None
        
    @abstractmethod
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio file and return normalized result."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on current system."""
        pass
    
    @abstractmethod
    def get_info(self) -> BackendInfo:
        """Get backend information."""
        pass
    
    def _normalize_segments(self, segments: Any) -> List[TranscriptionSegment]:
        """Normalize segments to common format."""
        # Backend-specific implementation
        pass
```

### Task 2: Implement MLX Backend

```python
# src/screenscribe/audio_backends.py (continued)

class MLXWhisperBackend(WhisperBackend):
    """Apple Silicon optimized backend using MLX."""
    
    def is_available(self) -> bool:
        # Check platform
        if platform.system() != "Darwin":
            return False
        if platform.machine() != "arm64":
            return False
            
        # Check import
        try:
            import mlx_whisper
            return True
        except ImportError:
            return False
    
    def get_info(self) -> BackendInfo:
        available = self.is_available()
        return BackendInfo(
            name="mlx",
            available=available,
            device="gpu" if available else "none",
            compute_type="float16",
            reason=None if available else "Not Apple Silicon or MLX not installed"
        )
    
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        import mlx_whisper
        
        # Map model name
        model_map = {
            "tiny": "mlx-community/whisper-tiny",
            "base": "mlx-community/whisper-base",
            "small": "mlx-community/whisper-small", 
            "medium": "mlx-community/whisper-medium",
            "large": "mlx-community/whisper-large-v3",
            "large-v3": "mlx-community/whisper-large-v3"
        }
        
        model_repo = model_map.get(self.model_name, f"mlx-community/whisper-{self.model_name}")
        
        # Transcribe
        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=model_repo,
            language=language,
            verbose=False
        )
        
        # Normalize output
        segments = [
            TranscriptionSegment(
                id=i,
                seek=0,  # MLX doesn't provide seek
                start=seg.get("start", 0),
                end=seg.get("end", 0),
                text=seg.get("text", ""),
                tokens=seg.get("tokens", []),
                temperature=seg.get("temperature", 0.0),
                avg_logprob=seg.get("avg_logprob", 0.0),
                compression_ratio=seg.get("compression_ratio", 0.0),
                no_speech_prob=seg.get("no_speech_prob", 0.0),
                words=seg.get("words")
            )
            for i, seg in enumerate(result.get("segments", []))
        ]
        
        return TranscriptionResult(
            text=result["text"],
            segments=segments,
            language=result.get("language", language or "en")
        )
```

### Task 3: Update FasterWhisperBackend

```python
# src/screenscribe/audio_backends.py (continued)

class FasterWhisperBackend(WhisperBackend):
    """Cross-platform backend using faster-whisper."""
    
    def __init__(self, model_name: str = "base"):
        super().__init__(model_name)
        self._device = None
        self._compute_type = None
    
    def is_available(self) -> bool:
        """Always available as universal fallback."""
        return True
    
    def get_info(self) -> BackendInfo:
        # Detect device
        device = "cpu"
        compute_type = "int8"
        
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                compute_type = "float16"
        except ImportError:
            pass
            
        return BackendInfo(
            name="faster-whisper",
            available=True,
            device=device,
            compute_type=compute_type
        )
    
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        from faster_whisper import WhisperModel
        
        # Initialize model if needed
        if self.model is None:
            info = self.get_info()
            self._device = info.device
            self._compute_type = info.compute_type
            
            # CPU optimization for Apple Silicon
            cpu_threads = None
            if self._device == "cpu" and platform.machine() == "arm64":
                import os
                total_cores = os.cpu_count() or 4
                cpu_threads = max(4, int(total_cores * 0.85))
                logger.info(f"Using {cpu_threads}/{total_cores} CPU threads")
            
            self.model = WhisperModel(
                self.model_name,
                device=self._device,
                compute_type=self._compute_type,
                cpu_threads=cpu_threads
            )
        
        # Transcribe
        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Convert generator to list and normalize
        segment_list = []
        full_text = []
        
        for i, segment in enumerate(segments):
            seg_model = TranscriptionSegment(
                id=i,
                seek=segment.seek,
                start=segment.start,
                end=segment.end,
                text=segment.text,
                tokens=segment.tokens,
                temperature=segment.temperature,
                avg_logprob=segment.avg_logprob,
                compression_ratio=segment.compression_ratio,
                no_speech_prob=segment.no_speech_prob,
                words=[
                    {"start": w.start, "end": w.end, "word": w.word, "probability": w.probability}
                    for w in (segment.words or [])
                ]
            )
            segment_list.append(seg_model)
            full_text.append(segment.text)
        
        return TranscriptionResult(
            text=" ".join(full_text),
            segments=segment_list,
            language=info.language,
            duration=info.duration
        )
```

### Task 4: Backend Selection Logic

```python
# src/screenscribe/audio_backends.py (continued)

def get_available_backends(model_name: str = "base") -> List[BackendInfo]:
    """Get information about all available backends."""
    backends = [
        MLXWhisperBackend(model_name),
        # WhisperCppBackend(model_name),  # Future implementation
        FasterWhisperBackend(model_name),
    ]
    
    return [backend.get_info() for backend in backends]

def get_best_backend(model_name: str = "base", preferred: Optional[str] = None) -> WhisperBackend:
    """
    Get the best available backend for current platform.
    
    Priority:
    1. User preference (if available)
    2. Platform-specific optimization (MLX on Apple Silicon)
    3. Universal fallback (faster-whisper)
    """
    backends = {
        "mlx": MLXWhisperBackend,
        "faster-whisper": FasterWhisperBackend,
        # "whisper-cpp": WhisperCppBackend,  # Future
    }
    
    # Try user preference
    if preferred and preferred in backends:
        backend_class = backends[preferred]
        backend = backend_class(model_name)
        if backend.is_available():
            logger.info(f"Using requested backend: {preferred}")
            return backend
        else:
            logger.warning(f"Requested backend '{preferred}' not available")
    
    # Auto-detect best backend
    # Priority order for auto-detection
    priority = ["mlx", "faster-whisper"]
    
    for name in priority:
        if name in backends:
            backend_class = backends[name]
            backend = backend_class(model_name)
            if backend.is_available():
                logger.info(f"Auto-selected backend: {name}")
                return backend
    
    # This should never happen
    raise RuntimeError("No audio transcription backend available")
```

### Task 5: Update AudioProcessor

```python
# src/screenscribe/audio.py

"""Audio processing module for screenscribe."""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .audio_backends import get_best_backend, get_available_backends
from .models import TranscriptionResult
from .config import config

logger = logging.getLogger(__name__)
console = Console()

class AudioProcessor:
    """Handles audio extraction and transcription using best available backend."""
    
    def __init__(self, model_name: str = "medium", backend: Optional[str] = None):
        """
        Initialize audio processor with platform-optimized backend.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            backend: Force specific backend (mlx, faster-whisper) or None for auto
        """
        self.model_name = model_name
        self.backend = get_best_backend(model_name, preferred=backend)
        self._checkpoint_file: Optional[Path] = None
        
        # Log backend selection
        backend_info = self.backend.get_info()
        console.print(
            f"🎙️ Audio backend: {backend_info.name} "
            f"({'GPU' if 'gpu' in backend_info.device else backend_info.device.upper()})",
            style="blue"
        )
    
    # ... rest of existing methods (extract_audio, etc.) ...
    
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio file using the selected backend."""
        logger.info(f"Transcribing audio: {audio_path}")
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Create progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task(
                f"Transcribing with {self.backend.get_info().name}...", 
                total=100
            )
            
            try:
                # Transcribe using backend
                result = self.backend.transcribe(audio_path, language)
                progress.update(task, completed=100)
                
                # Convert to dict for compatibility
                return {
                    "text": result.text,
                    "segments": [seg.dict() for seg in result.segments],
                    "language": result.language
                }
                
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                raise
```

### Task 6: Update CLI

```python
# src/screenscribe/cli.py (add to existing CLI)

@app.command()
def main(
    # ... existing arguments ...
    whisper_backend: Optional[str] = typer.Option(
        None,
        "--whisper-backend",
        help="Audio backend: mlx (Apple Silicon GPU), faster-whisper (universal), or auto"
    ),
    list_backends: bool = typer.Option(
        False,
        "--list-backends",
        help="List available audio backends and exit"
    ),
):
    """Process video/audio to structured notes."""
    
    # Handle backend listing
    if list_backends:
        from .audio_backends import get_available_backends
        
        console.print("\n🔍 Available Audio Backends:", style="bold")
        for info in get_available_backends(whisper_model):
            status = "✅" if info.available else "❌"
            device_info = f"{info.device}"
            if info.compute_type:
                device_info += f" ({info.compute_type})"
            
            console.print(f"  {status} {info.name}: {device_info}")
            if info.reason and not info.available:
                console.print(f"     {info.reason}", style="dim")
        
        raise typer.Exit(0)
    
    # Validate backend choice
    if whisper_backend and whisper_backend not in ["mlx", "faster-whisper", "whisper-cpp", "auto"]:
        console.print(
            f"❌ Invalid backend '{whisper_backend}'. "
            f"Choose from: mlx, faster-whisper, auto",
            style="red"
        )
        raise typer.Exit(1)
    
    # Pass backend to processing options
    options = ProcessingOptions(
        # ... existing options ...
        whisper_backend=whisper_backend if whisper_backend != "auto" else None,
    )
```

### Task 7: Update pyproject.toml

```toml
# pyproject.toml

[project]
name = "screenscribe"
# ... existing config ...

dependencies = [
    "typer>=0.9.0",
    "faster-whisper>=1.0.0",  # Keep as base dependency
    "opencv-python>=4.8.0",
    # ... rest of existing dependencies ...
]

[project.optional-dependencies]
# Platform-specific audio backends
apple = [
    "mlx-whisper>=0.2.0",  # Apple Silicon GPU acceleration
]

# Development dependencies
dev = [
    # ... existing dev deps ...
]

# Install all optional backends
all = [
    "screenscribe[apple]",
]

[project.scripts]
screenscribe = "screenscribe.cli:main"
```

## Testing & Validation

### Unit Tests

```python
# tests/test_audio_backends.py

import pytest
from pathlib import Path
import platform

from screenscribe.audio_backends import (
    MLXWhisperBackend, 
    FasterWhisperBackend,
    get_best_backend
)

class TestBackendDetection:
    def test_mlx_only_on_apple_silicon(self):
        backend = MLXWhisperBackend()
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            # May or may not be available depending on installation
            assert isinstance(backend.is_available(), bool)
        else:
            assert not backend.is_available()
    
    def test_faster_whisper_always_available(self):
        backend = FasterWhisperBackend()
        assert backend.is_available()
    
    def test_auto_selection(self):
        backend = get_best_backend()
        assert backend is not None
        assert backend.is_available()

class TestTranscription:
    @pytest.fixture
    def sample_audio(self, tmp_path):
        # Create or copy test audio file
        audio_file = tmp_path / "test.wav"
        # ... generate test audio ...
        return audio_file
    
    def test_backend_output_compatibility(self, sample_audio):
        """Ensure all backends produce compatible output."""
        from screenscribe.models import TranscriptionResult
        
        # Test each available backend
        for Backend in [MLXWhisperBackend, FasterWhisperBackend]:
            backend = Backend(model_name="tiny")  # Use tiny for speed
            if backend.is_available():
                result = backend.transcribe(sample_audio)
                
                # Validate output structure
                assert isinstance(result, TranscriptionResult)
                assert isinstance(result.text, str)
                assert isinstance(result.segments, list)
                assert isinstance(result.language, str)
```

### Integration Tests

```bash
# tests/test_integration.sh

#!/bin/bash
# Test multi-backend integration

# Test auto-detection
screenscribe test-video.mp4 --output /tmp/test-auto

# Test specific backends
screenscribe test-video.mp4 --output /tmp/test-mlx --whisper-backend mlx
screenscribe test-video.mp4 --output /tmp/test-faster --whisper-backend faster-whisper

# Test backend listing
screenscribe --list-backends

# Compare outputs
diff /tmp/test-auto/output.md /tmp/test-mlx/output.md
```

### Performance Benchmarks

```python
# scripts/benchmark_backends.py

import time
from pathlib import Path
import typer

from screenscribe.audio_backends import get_available_backends

app = typer.Typer()

@app.command()
def benchmark(
    audio_file: Path,
    model: str = "base",
    runs: int = 3
):
    """Benchmark all available backends."""
    
    for info in get_available_backends(model):
        if not info.available:
            print(f"⏭️  Skipping {info.name} (not available)")
            continue
            
        print(f"\n📊 Benchmarking {info.name} ({info.device})...")
        
        # Import backend
        if info.name == "mlx":
            from screenscribe.audio_backends import MLXWhisperBackend
            backend = MLXWhisperBackend(model)
        else:
            from screenscribe.audio_backends import FasterWhisperBackend
            backend = FasterWhisperBackend(model)
        
        # Run benchmark
        times = []
        for i in range(runs):
            start = time.time()
            result = backend.transcribe(audio_file)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Run {i+1}: {elapsed:.2f}s")
        
        avg_time = sum(times) / len(times)
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Words: {len(result.text.split())}")

if __name__ == "__main__":
    app()
```

## Anti-Patterns to Avoid

1. **DON'T hardcode device detection**:
   ```python
   # BAD: Assumes MPS availability based on platform
   if platform.system() == "Darwin":
       device = "mps"  # Will fail with faster-whisper!
   ```

2. **DON'T mix backend-specific code in AudioProcessor**:
   ```python
   # BAD: Backend-specific logic in main processor
   if self.backend == "mlx":
       import mlx_whisper  # Should be in backend class
   ```

3. **DON'T assume output format**:
   ```python
   # BAD: Assumes specific segment structure
   text = result["segments"][0]["text"]  # May not exist!
   
   # GOOD: Use normalized models
   text = result.segments[0].text if result.segments else ""
   ```

4. **DON'T ignore platform differences**:
   ```python
   # BAD: Same CPU threads for all platforms
   cpu_threads = 8  # M3 Ultra has 28 cores!
   
   # GOOD: Platform-aware optimization
   cpu_threads = int(os.cpu_count() * 0.85)
   ```

## Deployment & Migration

### Migration Path

1. **Phase 1**: Deploy with backward compatibility
   - Keep faster-whisper as default
   - MLX as opt-in via `--whisper-backend mlx`

2. **Phase 2**: Enable auto-detection
   - Auto-select MLX on Apple Silicon
   - Monitor for issues

3. **Phase 3**: Add whisper.cpp backend
   - Further performance improvements

### Installation Guide Updates

```markdown
# README.md updates

## Installation

### Basic Installation
pip install screenscribe

### Apple Silicon Optimized (M1/M2/M3)
pip install "screenscribe[apple]"

This enables GPU acceleration for 2-3x faster transcription.

### Verify Installation
screenscribe --list-backends
```

## Monitoring & Telemetry

Add backend selection to logs for debugging:

```python
# In AudioProcessor.__init__
logger.info(f"Audio backend selected: {backend_info.name}")
logger.info(f"Platform: {platform.system()} {platform.machine()}")
logger.info(f"Device: {backend_info.device} ({backend_info.compute_type})")
```

## Success Metrics

Track after deployment:
1. Performance improvement on Apple Silicon (target: 2-3x)
2. No regression on other platforms
3. Backend selection success rate
4. User satisfaction with auto-detection

## Future Considerations

1. **whisper.cpp integration**: For maximum performance
2. **Remote transcription**: Backend that delegates to API
3. **Streaming support**: Real-time transcription
4. **Model caching**: Share models between backends
5. **Quantization**: INT8 models for faster CPU inference
``` 