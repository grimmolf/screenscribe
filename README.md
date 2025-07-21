# screenscribe

<div align="center">

🎬 **Transform videos into structured, searchable notes with AI-powered analysis**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

</div>

**screenscribe** turns your videos into comprehensive, structured notes. It extracts audio transcripts, analyzes visual content with AI, and creates searchable documents. Perfect for lectures, meetings, tutorials, and any video content you want to reference later.

> 🧵 **New**: screenscribe now includes [Fabric integration](./fabric-extension/) for AI-powered video analysis patterns. Thanks to the amazing [Fabric project](https://github.com/danielmiessler/fabric) by Daniel Miessler for providing the pattern framework that makes advanced video analysis workflows possible.

## 🚀 Quick Start

```bash
# 1. Install screenscribe Fabric extension
cd fabric-extension && make build && make install

# 2. Set up Fabric with your AI provider (one-time setup)
fabric --setup

# 3. Process your first video
video_analyze video.mp4 | fabric -p analyze_video_content
```

**That's it!** Your video analysis will be saved as structured notes with transcripts and visual insights.

> 🔒 **Privacy-First**: screenscribe processes videos locally using Whisper and ffmpeg. Only the extracted text and frame data is sent to your chosen AI provider via Fabric for analysis.

## 🎯 What You Get

screenscribe creates comprehensive notes from your videos:

- **📝 Complete transcripts** - Every word spoken, timestamped
- **👁️ Visual analysis** - AI describes what's happening on screen  
- **🔗 Synchronized content** - Transcript and visuals aligned by time
- **📋 Structured output** - Clean Markdown or HTML with embedded images
- **🔍 Searchable notes** - Find exactly what you need quickly

### Example Output
From a 30-minute tutorial, you get:
- **Summary** - Key points and main takeaways
- **Timeline** - Important moments with timestamps  
- **Visual highlights** - Screenshots of key concepts
- **Action items** - Next steps and to-dos
- **Complete transcript** - Full text for reference

## 🎯 Perfect For

- **📚 Students** - Turn lectures into study guides
- **💼 Professionals** - Convert meetings into action items
- **👩‍💻 Developers** - Extract code from programming tutorials
- **📈 Traders** - Analyze trading education videos for strategies
- **🎓 Educators** - Create accessible content from recorded lessons
- **📺 Content creators** - Analyze competitor content and trends

## ⚡ Blazing Fast Performance

**Apple Silicon users get 20-30x faster processing:**

| Hardware | Processing Time | Speedup |
|----------|----------------|---------|
| M3 Ultra | 103s for 49min video | **29x faster** |
| M1/M2 Pro | 200s for 49min video | **20x faster** |
| Other platforms | Optimized CPU processing | Still fast! |

## 🎯 Basic Usage

### Process Any Video
```bash
# Extract video data (local processing only)
video_analyze lecture.mp4 > video_data.json

# Analyze with AI (uses your Fabric-configured AI provider)
video_analyze lecture.mp4 | fabric -p analyze_video_content

# Trading-specific analysis
video_analyze trading_webinar.mp4 | fabric -p analyze_trading_video

# Programming tutorial analysis
video_analyze coding_lesson.mp4 | fabric -p extract_code_from_video
```

### Processing Options
```bash
# Fast processing (good for previews)
video_analyze video.mp4 --whisper-model tiny | fabric -p analyze_video_content

# High quality transcription (best for important content)  
video_analyze video.mp4 --whisper-model large | fabric -p analyze_video_content

# Frames-only processing (skip transcription)
video_analyze video.mp4 --skip-transcript | fabric -p analyze_video_content

# Custom frame intervals
video_analyze video.mp4 --frame-interval 30 | fabric -p analyze_video_content
```

## 🧵 Advanced AI Analysis with Fabric

Supercharge your video analysis by combining screenscribe with [Fabric's AI patterns](https://github.com/danielmiessler/fabric):

```bash
# Install Fabric integration
cd fabric-extension && make build && make install

# Analyze videos with specialized AI patterns
video_analyze tutorial.mp4 | fabric -p analyze_video_content
video_analyze trading_webinar.mp4 | fabric -p analyze_trading_video  
video_analyze coding_lesson.mp4 | fabric -p extract_code_from_video

# Chain multiple AI analyses
video_analyze presentation.mp4 | \
  fabric -p analyze_video_content | \
  fabric -p extract_key_points | \
  fabric -p create_blog_post
```

**Available AI Patterns:**
- **General**: Comprehensive analysis, code extraction
- **Trading**: Market analysis, technical patterns, trading strategies
- **Education**: Key concepts, action items, summaries

## 📦 Installation

### Prerequisites
```bash
# Install required system dependencies
# macOS: brew install ffmpeg go jq
# Ubuntu: sudo apt install ffmpeg golang-go jq
# Windows: Download from respective websites

# Install Fabric (if not already installed)
go install github.com/danielmiessler/fabric@latest
```

### Install screenscribe (Golang/Fabric Method)
```bash
# Clone and build screenscribe Fabric extension
git clone https://github.com/grimmolf/screenscribe.git
cd screenscribe/fabric-extension

# Build and install tools
make build && make install

# Copy AI patterns to your Fabric configuration
cp -r patterns/* ~/.config/fabric/patterns/
```

### Set Up Fabric AI Provider
```bash
# Configure Fabric with your preferred AI provider (one-time setup)
fabric --setup

# This will guide you through setting up your AI provider
# All API configuration is handled by Fabric, not screenscribe
```

### Verify Installation
```bash
video_analyze --help
whisper_transcribe --help
video_frames --help

# Check available patterns
fabric -l | grep video
```

## 🎯 Common Use Cases

### For Students
```bash
# Turn lecture recordings into study guides
video_analyze lecture.mp4 | fabric -p analyze_video_content > study-guide.md

# Process multiple lectures
for file in lectures/*.mp4; do
  video_analyze "$file" | fabric -p analyze_video_content > "notes/$(basename "$file" .mp4)-notes.md"
done
```

### For Professionals  
```bash
# Convert meeting recordings to action items
video_analyze meeting.mp4 | fabric -p analyze_video_content | fabric -p extract_action_items

# Analyze conference talks
video_analyze conference-talk.mp4 --whisper-model large | fabric -p analyze_video_content
```

### For Developers
```bash
# Extract code from programming tutorials
video_analyze coding-tutorial.mp4 | fabric -p extract_code_from_video

# Create documentation from recorded demos
video_analyze demo.mp4 | fabric -p analyze_video_content | fabric -p create_documentation
```

### For Traders
```bash
# Analyze trading education content
video_analyze trading-course.mp4 | fabric -p analyze_trading_video
video_analyze market-analysis.mp4 | fabric -p extract_technical_analysis
```

## ⚙️ Configuration

### Fabric Integration
```bash
# List available video analysis patterns
fabric -l | grep video

# Use custom Fabric configurations
export FABRIC_CONFIG_HOME=~/.config/fabric

# Chain patterns for complex workflows
video_analyze tutorial.mp4 | \
  fabric -p analyze_video_content | \
  fabric -p extract_key_points | \
  fabric -p create_summary
```

### Advanced Options
```bash
# Use different Whisper models
video_analyze video.mp4 --whisper-model large

# Skip transcript or frames for faster processing
video_analyze video.mp4 --skip-transcript  # frames only
video_analyze video.mp4 --skip-frames      # transcript only

# Custom frame intervals
video_analyze video.mp4 --frame-interval 60  # one frame per minute
```

## 🛠️ Troubleshooting

**Common Issues:**

- **"video_analyze not found"** → Run `make install` from fabric-extension directory
- **"FFmpeg not found"** → Install FFmpeg for your operating system
- **Slow on Apple Silicon** → MLX backend auto-detects and provides 20x speedup
- **AI analysis errors** → Run `fabric --setup` to configure your AI provider
- **Out of memory** → Use `--whisper-model tiny` for large videos

**Performance Tips:**
- Apple Silicon users: MLX backend provides automatic GPU acceleration
- Use `--whisper-model tiny` for speed, `large` for accuracy
- Use `--skip-transcript` or `--skip-frames` for faster processing
- Fabric patterns can be chained for complex analysis workflows

**Need more help?** See our [Complete Troubleshooting Guide](docs/user/troubleshooting.md)

## 📚 Documentation

- **[Complete User Manual](docs/USER_MANUAL.md)** - Everything you need to know
- **[Installation Guide](docs/user/installation.md)** - Platform-specific setup
- **[Real-World Examples](docs/examples/real-world-examples.md)** - See it in action
- **[Fabric Integration Guide](docs/FABRIC_INTEGRATION.md)** - Advanced AI workflows

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Support & Contributing

- **Questions**: [GitHub Discussions](https://github.com/grimmolf/screenscribe/discussions)
- **Issues**: [GitHub Issues](https://github.com/grimmolf/screenscribe/issues)
- **Contributing**: See [Development Guide](docs/DEVELOPMENT.md)

---

## 🔧 For Developers

<details>
<summary>Click to expand developer information</summary>

### Development Setup

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
pytest tests/ -v

# Code quality checks
ruff check src/ tests/ --fix
black src/ tests/
mypy src/
```

### Architecture Overview

**screenscribe** is built as a modular pipeline:

```
[Video Input] → [Audio Extraction] → [Whisper Transcription]
                     ↓
[Frame Extraction] → [Temporal Alignment] → [LLM Synthesis] → [Output Generation]
```

### Key Components

- **`src/screenscribe/cli.py`** - Main CLI interface with multi-command structure
- **`src/screenscribe/audio.py`** - Multi-backend transcription (MLX, faster-whisper)  
- **`src/screenscribe/video.py`** - Frame extraction and scene detection
- **`src/screenscribe/synthesis.py`** - LLM-powered content analysis
- **`src/screenscribe/config_enhanced.py`** - Global configuration system
- **`fabric-extension/`** - Complete Fabric integration with Go helper tools

### Multi-Backend Audio System

screenscribe supports multiple transcription backends with automatic optimization:

- **MLX**: Apple Silicon GPU acceleration (20-30x faster on M1/M2/M3)
- **faster-whisper**: Universal CPU backend with optimization  
- **OpenAI Whisper**: Original implementation as fallback

Backend selection is automatic based on available hardware and installed dependencies.

### Advanced Features

- **Global Configuration**: Centralized settings at `~/.config/screenscribe/`
- **YouTube Integration**: Direct transcript extraction with Whisper fallback
- **External Transcripts**: Support for SRT, VTT, JSON, and plain text files
- **Self-Update System**: Automatic updates from GitHub
- **Fabric Integration**: AI pattern system for advanced analysis workflows
- **Apple Silicon Optimization**: GPU acceleration via MLX backend
- **Network Storage Handling**: Automatic local copying for performance
- **Graceful Interruption**: Ctrl+C handling with progress saving

### Fabric Extension

The `fabric-extension/` directory contains a complete integration with the [Fabric AI framework](https://github.com/danielmiessler/fabric):

- **Go Helper Tools**: `whisper_transcribe`, `video_frames`, `video_analyze`
- **Backend Scripts**: Python and shell scripts for video processing
- **AI Patterns**: Specialized patterns for video analysis workflows
- **Build System**: Complete Makefile-based build and test system

### Testing

```bash
# Run full test suite
pytest tests/ -v --cov=src/screenscribe

# Test specific components
pytest tests/test_audio_backends.py -v
pytest tests/test_integration_backends.py -v

# Test Fabric extension
cd fabric-extension && make test
```

### Performance Optimization

**Apple Silicon (M1/M2/M3)**:
- Install with `[apple]` dependencies for MLX backend
- Expect 20-30x transcription speedup with GPU acceleration
- Automatic fallback to optimized CPU processing if needed

**General Optimizations**:
- Network files automatically copied locally for better I/O
- Scene detection vs interval sampling based on content type
- Configurable quality settings for frame extraction
- Multi-threading for CPU-intensive operations

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the quality checks
5. Submit a pull request

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed contribution guidelines.

### Project Structure

```
screenscribe/
├── src/screenscribe/          # Main Python package
├── fabric-extension/          # Fabric AI integration
├── docs/                      # User and developer documentation  
├── tests/                     # Test suite
├── prompts/                   # Default AI prompts
├── scripts/                   # Installation and utility scripts
└── examples/                  # Example outputs and use cases
```

**Special Thanks**: To [Daniel Miessler](https://github.com/danielmiessler) and the [Fabric project](https://github.com/danielmiessler/fabric) for creating the powerful AI pattern framework that enables advanced video analysis workflows.

</details>