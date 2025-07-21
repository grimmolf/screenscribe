# Screenscribe + Fabric Integration

**Transform video analysis with AI patterns**

## 🧵 Overview

screenscribe now includes comprehensive integration with [Fabric](https://github.com/danielmiessler/fabric) by Daniel Miessler, providing advanced AI-powered video analysis workflows through Fabric's pattern ecosystem.

### What is Fabric?

[Fabric](https://github.com/danielmiessler/fabric) is an open-source framework that augments humans using AI by providing a modular pattern system for various AI tasks. Created by Daniel Miessler, Fabric enables users to chain AI patterns together for complex workflows.

### screenscribe + Fabric = Powerful Video Analysis

By integrating screenscribe's video processing capabilities with Fabric's AI patterns, users can:

- **Extract insights** from videos using specialized AI patterns
- **Chain multiple analyses** for comprehensive understanding
- **Customize workflows** for specific content types
- **Leverage existing Fabric patterns** for post-processing

## 🚀 Quick Start

### 1. Install Fabric
```bash
# Install Fabric (if not already installed)
go install github.com/danielmiessler/fabric@latest
```

### 2. Build screenscribe Fabric Extension
```bash
# Navigate to the Fabric extension
cd fabric-extension

# Build and install helper tools
make build && make install

# Copy patterns to your Fabric configuration
cp -r patterns/* ~/.config/fabric/patterns/
```

### 3. Analyze Videos with Fabric
```bash
# Basic video analysis
video_analyze tutorial.mp4 | fabric -p analyze_video_content

# Trading-specific analysis
video_analyze trading_webinar.mp4 | fabric -p analyze_trading_video

# Extract code from programming tutorials
video_analyze coding_tutorial.mp4 | fabric -p extract_code_from_video
```

## 🔧 Helper Tools

The Fabric extension provides three main helper tools:

### `video_analyze` - Main Orchestrator
Combines transcript extraction and frame analysis into comprehensive JSON output for Fabric patterns.

```bash
video_analyze [OPTIONS] VIDEO_FILE

# Key options:
--whisper-model MODEL     # Whisper model (tiny, base, small, medium, large)
--whisper-backend BACKEND # Backend (auto, mlx, faster-whisper, openai-whisper)
--frame-interval SECONDS  # Frame extraction interval
--skip-transcript         # Transcript-only analysis
--skip-frames            # Frame-only analysis
```

### `whisper_transcribe` - Dedicated Transcription
High-performance transcription with multi-backend support.

```bash
whisper_transcribe [OPTIONS] VIDEO_FILE

# Supports MLX (Apple Silicon), faster-whisper, and OpenAI Whisper backends
```

### `video_frames` - Frame Extraction
Advanced frame extraction with flexible output formats.

```bash
video_frames [OPTIONS] VIDEO_FILE

# Supports base64, file paths, or both output formats
```

## 📋 Fabric Patterns

### General Video Analysis
- **`analyze_video_content`** - Comprehensive video analysis with timeline and key points
- **`extract_code_from_video`** - Extract and format code snippets from programming tutorials

### Trading-Specific Patterns
- **`analyze_trading_video`** - Complete trading education analysis with market insights
- **`extract_technical_analysis`** - Chart pattern recognition and technical indicators
- **`extract_trading_strategy`** - Systematic trading strategy extraction
- **`analyze_market_commentary`** - Market outlook and prediction analysis

## 🔄 Workflow Examples

### Basic Analysis Chain
```bash
# Analyze → Extract → Create
video_analyze presentation.mp4 | \
  fabric -p analyze_video_content | \
  fabric -p extract_key_points | \
  fabric -p create_blog_post
```

### Trading Education Pipeline
```bash
# Complete trading analysis workflow
video_analyze trading_tutorial.mp4 | \
  fabric -p analyze_trading_video | \
  fabric -p extract_actionable_trades | \
  fabric -p format_trade_journal
```

### Programming Tutorial Processing
```bash
# Extract code and create documentation
video_analyze coding_tutorial.mp4 | \
  fabric -p extract_code_from_video | \
  fabric -p create_documentation | \
  fabric -p add_explanations
```

### Multi-Format Processing
```bash
# Save intermediate results for different analyses
video_analyze workshop.mp4 > workshop_data.json

# Process for different purposes
cat workshop_data.json | fabric -p analyze_video_content > summary.md
cat workshop_data.json | fabric -p extract_action_items > todos.md
cat workshop_data.json | fabric -p extract_key_quotes > quotes.md
```

## ⚡ Performance Features

### Apple Silicon Optimization
- **MLX backend** provides 20-30x GPU acceleration on M1/M2/M3 Macs
- **Automatic detection** and optimal backend selection
- **Intelligent fallbacks** to ensure compatibility

### Flexible Processing
- **Skip components** for faster processing (transcript-only or frames-only)
- **Configurable quality** and resolution settings
- **Multiple output formats** for different use cases

## 📊 JSON Output Format

The helper tools output structured JSON that Fabric patterns can process:

```json
{
  "transcript": {
    "text": "Complete transcript text...",
    "segments": [
      {"id": 0, "start": 0.0, "end": 5.2, "text": "Introduction..."}
    ],
    "language": "en",
    "duration": 1847.3,
    "backend": "mlx-whisper"
  },
  "frames": {
    "source_file": "video.mp4",
    "frame_count": 62,
    "frame_interval": 30,
    "frames": [
      {"frame_number": 1, "timestamp": 0, "data": "base64_image_data..."}
    ]
  },
  "metadata": {
    "source_file": "video.mp4",
    "duration": 1847.3,
    "processed_at": 1703123456,
    "whisper_backend": "mlx-whisper"
  }
}
```

## 🛠️ Installation & Setup

### System Requirements
- **Go 1.21+** (for helper tools)
- **Python 3.9+** (for Whisper integration)  
- **FFmpeg** (for video processing)
- **jq** (for JSON processing)
- **Fabric** (AI pattern framework)

### Build from Source
```bash
# Clone screenscribe repository
git clone https://github.com/grimmolf/screenscribe.git
cd screenscribe/fabric-extension

# Install dependencies
make deps

# Build and test
make build && make test

# Install tools
make install

# Copy patterns to Fabric
cp -r patterns/* ~/.config/fabric/patterns/
```

### Verify Installation
```bash
# Check tools are working
video_analyze --help
whisper_transcribe --help
video_frames --help

# Verify Fabric patterns
fabric -l | grep video
```

## 🙏 Credits

Special thanks to [Daniel Miessler](https://github.com/danielmiessler) and the [Fabric project](https://github.com/danielmiessler/fabric) for creating the powerful AI pattern framework that makes these advanced video analysis workflows possible.

The Fabric integration demonstrates the power of composable AI tools - by combining screenscribe's video processing capabilities with Fabric's pattern ecosystem, users can create sophisticated analysis pipelines that would be difficult to achieve with either tool alone.

## 📚 Learn More

- **[Fabric Extension Documentation](../fabric-extension/README.md)** - Complete technical documentation
- **[Fabric Project](https://github.com/danielmiessler/fabric)** - Learn about Fabric's AI pattern system
- **[screenscribe Documentation](../README.md)** - Main screenscribe documentation
- **[Trading Analysis Examples](../examples/trading-analysis/)** - Real-world examples

---

**screenscribe + Fabric** - Bringing AI-powered video analysis to the Fabric ecosystem.