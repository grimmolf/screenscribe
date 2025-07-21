# Development Guide

This document provides comprehensive information for developers working on screenscribe, including setup, architecture, and contribution guidelines.

## 🚀 Quick Development Setup

```bash
# Clone the repository
git clone https://github.com/grimmolf/screenscribe.git
cd screenscribe

# Build and install development version
cd fabric-extension
make build && make install

# Install patterns
cp -r patterns/* ~/.config/fabric/patterns/

# Run tests
make test

# Cross-platform development
make build-all              # Build for all platforms
make release-binaries       # Create distribution packages
make clean                  # Clean all build artifacts
```

## 🏗️ Architecture Overview

**screenscribe** is built as a modular pipeline around the Fabric AI framework:

```
[Video Input] → [Audio Extraction] → [Whisper Transcription]
                     ↓
[Frame Extraction] → [JSON Output] → [Fabric Patterns] → [AI Analysis]
```

### Core Architecture

The project consists of two main components:

1. **Local Processing Pipeline** (Go/Python/Shell)
   - Video/audio processing with ffmpeg
   - Multi-backend Whisper transcription
   - Frame extraction and encoding
   - JSON output generation

2. **AI Analysis Layer** (Fabric Integration)
   - Fabric pattern system for specialized analysis
   - LLM provider abstraction
   - Pattern chaining and workflow composition

## 📁 Project Structure

```
screenscribe/
├── fabric-extension/          # Main Fabric integration (Go-based)
│   ├── cmd/                   # Go CLI applications
│   │   ├── video_analyze/     # Main orchestrator tool
│   │   ├── whisper_transcribe/ # Transcription tool
│   │   └── video_frames/      # Frame extraction tool
│   ├── scripts/               # Backend scripts
│   │   ├── whisper_wrapper.py # Python Whisper backends
│   │   ├── extract_frames.sh  # Shell frame extraction
│   │   └── youtube_helper.py  # YouTube integration (yt-dlp)
│   ├── patterns/              # Fabric AI patterns
│   │   ├── analyze_video_content/
│   │   ├── extract_code_from_video/
│   │   └── analyze_trading_video/
│   └── Makefile              # Build system
├── src/screenscribe/         # Legacy Python package (deprecated)
├── docs/                     # Documentation
├── examples/                 # Example videos and outputs
└── README.md                 # User documentation
```

## 🔧 Key Components

### Go Helper Tools

#### `scribe` - Unified CLI
- **Purpose**: Single command-line interface with subcommands for all video analysis tasks
- **Location**: `fabric-extension/cmd/scribe/`
- **Subcommands**:
  - `scribe analyze` - Complete video analysis (transcript + frames)
  - `scribe transcribe` - Whisper transcription only
  - `scribe frames` - Frame extraction only
  - `scribe update` - Self-update from GitHub
  - `scribe uninstall` - Remove tools and patterns
- **Features**: 
  - Cross-platform binary compilation
  - Multiple Whisper backend support
  - YouTube URL detection and processing
  - YouTube transcript extraction with yt-dlp
  - Configurable frame extraction

### Backend Scripts

#### `whisper_wrapper.py` - Python Whisper Integration
- **Purpose**: Multi-backend Whisper transcription with fallbacks
- **Key Features**:
  - MLX backend for Apple Silicon GPU acceleration (20-30x speedup)
  - faster-whisper for CPU optimization
  - OpenAI Whisper as fallback
  - Automatic backend selection based on hardware

#### `extract_frames.sh` - Shell Frame Processing
- **Purpose**: Advanced ffmpeg-based frame extraction
- **Features**: Scene detection, interval sampling, quality control

## 🎯 Multi-Backend Audio System

screenscribe supports multiple transcription backends with automatic optimization:

### Backend Priority (Auto-Selection)
1. **MLX** (Apple Silicon only) - GPU acceleration, 20-30x faster
2. **faster-whisper** - CPU optimized, universal compatibility
3. **OpenAI Whisper** - Original implementation, fallback

### Backend Selection Logic
```python
# Automatic selection in whisper_wrapper.py
if platform.system() == "Darwin" and platform.machine() == "arm64":
    try:
        import mlx_whisper
        return transcribe_with_mlx(...)
    except ImportError:
        pass
# Fall back to faster-whisper or OpenAI Whisper
```

### MLX Integration
- **Models**: Mapped to HuggingFace repositories (e.g., `mlx-community/whisper-base`)
- **API**: Uses `path_or_hf_repo` parameter for model specification
- **Performance**: 20-30x speedup on M1/M2/M3 Macs

## 🧩 Fabric Pattern System

### Available Patterns

#### General Video Analysis
- **`analyze_video_content`** - Comprehensive video analysis with timeline
- **`extract_code_from_video`** - Programming tutorial code extraction

#### Trading-Specific Patterns
- **`analyze_trading_video`** - Complete trading education analysis
- **`extract_technical_analysis`** - Chart patterns and technical indicators
- **`extract_trading_strategy`** - Strategy identification and extraction
- **`analyze_market_commentary`** - Market outlook analysis

### Pattern Development
```bash
# Create new pattern
mkdir -p fabric-extension/patterns/my_new_pattern
echo "# IDENTITY and PURPOSE..." > fabric-extension/patterns/my_new_pattern/system.md

# Install pattern
cp -r fabric-extension/patterns/my_new_pattern ~/.config/fabric/patterns/

# Test pattern
video_analyze sample.mp4 | fabric -p my_new_pattern
```

## 🔄 Build System

### Development Commands
```bash
# Development workflow
make clean                    # Clean all artifacts
make build                   # Build for current platform
make test                    # Run tests and validation
make install                 # Install to ~/.local/bin/

# Cross-platform builds
make build-all               # Build for all platforms
make release-binaries        # Create distribution packages

# Platform-specific builds
GOOS=darwin GOARCH=arm64 go build -o bin/video_analyze-mac-arm64 ./cmd/video_analyze
GOOS=linux GOARCH=amd64 go build -o bin/video_analyze-linux-amd64 ./cmd/video_analyze
```

### Supported Platforms
- **macOS**: AMD64 (Intel), ARM64 (Apple Silicon)
- **Linux**: AMD64 (x86_64), ARM64 (aarch64)
- **Windows**: AMD64 (planned)

### Binary Optimization
- **Flags**: `-ldflags "-s -w"` for size optimization
- **CGO**: Disabled for maximum compatibility
- **Static linking**: Self-contained binaries

## 🧪 Testing

### Test Categories

#### Unit Tests
```bash
# Go tool tests
cd fabric-extension
make test

# Python backend tests (if applicable)
pytest tests/ -v
```

#### Integration Tests
```bash
# End-to-end workflow tests
video_analyze examples/sample.mp4 | fabric -p analyze_video_content

# Backend compatibility tests
whisper_transcribe examples/sample.mp4 --backend mlx
whisper_transcribe examples/sample.mp4 --backend faster-whisper
```

#### Cross-Platform Tests
```bash
# Test all platform builds
make build-all
for platform in dist/*/; do
  echo "Testing $(basename $platform)..."
  $platform/video_analyze --help
done
```

### Test Data
- **Sample Videos**: `examples/` directory
- **Expected Outputs**: JSON schemas and reference files
- **Performance Benchmarks**: Processing time measurements

## 🔄 Advanced Features

### Global Configuration
- **Location**: `~/.config/screenscribe/` (planned enhancement)
- **Settings**: Default models, backends, quality settings
- **User Preferences**: Custom patterns, output formats

### YouTube Integration (Legacy)
- **Feature**: Direct transcript extraction from YouTube
- **Fallback**: Whisper transcription for videos without transcripts
- **Status**: Available in legacy Python codebase

### External Transcript Support (Legacy)
- **Formats**: SRT, VTT, JSON, plain text
- **Integration**: Combines with frame analysis
- **Status**: Available in legacy Python codebase

### Self-Update System
- **Mechanism**: GitHub releases download and installation
- **Command**: `video_analyze --update`
- **Process**: Download → Extract → Build → Install → Pattern Update

### Network Storage Handling (Legacy)
- **Feature**: Automatic local copying for performance
- **Use Case**: Processing videos on network drives
- **Status**: Available in legacy Python codebase

## 🚀 Performance Optimization

### Apple Silicon (M1/M2/M3)
- **MLX Backend**: GPU acceleration via Metal Performance Shaders
- **Installation**: Automatic detection and utilization
- **Performance**: 20-30x transcription speedup
- **Fallback**: Graceful degradation to CPU processing

### General Optimizations
- **Multi-threading**: CPU-intensive operations parallelized
- **Memory Management**: Streaming processing for large videos
- **I/O Optimization**: Local file copying for network storage
- **Quality Settings**: Configurable trade-offs between speed and accuracy

### Benchmark Results
| Hardware | Video Length | Processing Time | Speedup |
|----------|-------------|----------------|---------|
| M3 Ultra (MLX) | 49 minutes | 103 seconds | 29x |
| M1 Pro (MLX) | 49 minutes | 200 seconds | 20x |
| Intel i7 (faster-whisper) | 49 minutes | 15 minutes | 3x |

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/screenscribe.git
   cd screenscribe
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Develop and Test**
   ```bash
   cd fabric-extension
   make build && make test
   ```

4. **Code Quality**
   ```bash
   # Go formatting
   go fmt ./...
   
   # Go linting
   golangci-lint run
   
   # Python formatting (for scripts)
   black scripts/
   ruff check scripts/
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Clear description of changes
   - Test results and performance impact
   - Documentation updates if needed

### Contribution Guidelines

#### Code Style
- **Go**: Follow standard Go conventions, use `gofmt`
- **Python**: PEP 8 compliance, type hints required
- **Shell**: POSIX compliance where possible
- **Documentation**: Clear comments and README updates

#### Testing Requirements
- **Unit Tests**: All new functions must have tests
- **Integration Tests**: End-to-end workflow validation
- **Cross-Platform**: Verify builds work on target platforms
- **Performance**: No regressions in processing speed

#### Security Practices
- **Input Validation**: Sanitize all user inputs
- **Path Safety**: Prevent directory traversal attacks
- **Dependency Management**: Pin versions, regular updates
- **Secrets**: No hardcoded credentials or API keys

### Issue Reporting
- **Bug Reports**: Include system info, reproduction steps, expected vs actual behavior
- **Feature Requests**: Clear use case, proposed implementation, backwards compatibility
- **Performance Issues**: Benchmark data, system specifications

## 📋 Development Log Requirements

All development work must maintain the development log at `docs/CLAUDE_DEVELOPMENT_LOG.md`:

### Pre-Commit Checklist
1. **Update Development Log**
   - Context: What problem are you solving?
   - Changes: Bullet list of key updates
   - Validation: How did you test?

2. **Code Quality**
   - Run tests: `make test`
   - Check formatting: `go fmt ./...`
   - Lint code: `golangci-lint run`

3. **Documentation**
   - Update README if user-facing changes
   - Update this DEVELOPMENT.md if architecture changes
   - Add code comments for complex logic

## 🎯 Future Roadmap

### Planned Features
- **Windows Support**: Cross-compilation and testing
- **Docker Integration**: Containerized deployment
- **Web Interface**: Browser-based video upload and analysis
- **Batch Processing**: Queue system for multiple videos
- **Custom Models**: Support for fine-tuned Whisper models

### Architecture Improvements
- **Plugin System**: Extensible backend architecture
- **Configuration Management**: Advanced settings and profiles
- **Performance Monitoring**: Built-in benchmarking and profiling
- **Error Recovery**: Graceful handling of partial failures

### Integration Enhancements
- **Cloud Storage**: S3, Google Drive, Dropbox support
- **Video Platforms**: Enhanced YouTube, Vimeo integration
- **Export Formats**: PDF, DOCX, Notion integration
- **Real-time Processing**: Live stream analysis

## 📞 Developer Support

- **Discord**: Join the Fabric community for real-time discussion
- **GitHub Issues**: Technical problems and feature requests
- **Documentation**: This guide and inline code comments
- **Code Review**: Active maintainer feedback on pull requests

---

**Happy Coding!** 🚀

For questions about this development guide, please open an issue or join the community discussions.