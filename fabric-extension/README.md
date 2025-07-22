# Screenscribe - AI-Powered Video Analysis for Fabric

Transform video content into structured insights using AI transcription and visual analysis. Screenscribe integrates seamlessly with [Fabric](https://github.com/danielmiessler/fabric) to provide comprehensive video understanding with specialized patterns for trading, education, and general content analysis.

## 🎯 Overview

Screenscribe combines multiple AI technologies to extract maximum value from video content:

- **MLX Whisper** - 20-30x faster transcription on Apple Silicon with GPU acceleration
- **Multi-backend support** - Automatic fallback between MLX, faster-whisper, and OpenAI Whisper
- **Frame analysis** - Intelligent visual content extraction at configurable intervals  
- **Visual captions** - Ollama vision model integration for chart and diagram analysis
- **YouTube support** - Direct URL processing with native transcript extraction
- **Trading focus** - Specialized patterns for financial video analysis

```bash
# Complete video analysis with AI-powered insights
scribe analyze trading_video.mp4 | fabric -p analyze_trading_video

# Extract trading strategies with visual analysis
scribe analyze --generate-captions chart_analysis.mp4 | fabric -p extract_trading_strategy

# YouTube video analysis with native transcripts
scribe analyze --youtube-transcript "https://youtube.com/watch?v=VIDEO_ID" | fabric -p summarize_lecture
```

## 🚀 Key Features

### Lightning-Fast Transcription
- **MLX Whisper** on Apple Silicon: 49-minute video in ~103 seconds (vs 3000+ seconds on CPU)
- **Automatic backend selection** with intelligent fallback
- **Multiple model sizes** from tiny (speed) to large (accuracy)

### Advanced Visual Analysis
- **Smart frame extraction** at configurable intervals
- **Ollama vision integration** for chart and diagram understanding
- **Two-pass processing** with fast + rich vision models
- **Base64 or file path output** formats

### Seamless Integration
- **Fabric patterns** for structured analysis workflows
- **JSON output** compatible with all Fabric patterns
- **YouTube URL support** with transcript extraction
- **Self-updating** via GitHub releases

## 📦 Installation

### Prerequisites

1. **Go 1.21+** - For building the scribe binary
2. **Python 3.9+** - For MLX/Whisper backends
3. **FFmpeg** - For video processing  
4. **Fabric** - [Install Fabric](https://github.com/danielmiessler/fabric)

### System Dependencies

```bash
# macOS
brew install go python3 ffmpeg

# Ubuntu/Debian
sudo apt install golang-go python3 python3-pip ffmpeg

# Fedora/RHEL
sudo dnf install go python3 python3-pip ffmpeg
```

### Python Dependencies

```bash
# Core transcription engine (required)
pip3 install faster-whisper

# Apple Silicon GPU acceleration (highly recommended for M1/M2/M3)
pip3 install mlx-whisper

# Optional fallback engine
pip3 install openai-whisper

# YouTube support (optional)
pip3 install yt-dlp
```

### Build and Install

```bash
# Clone or download the screenscribe repository
git clone https://github.com/grimmolf/screenscribe.git
cd screenscribe/fabric-extension

# Build and install to ~/.local/bin
make install

# Or install system-wide (requires sudo)
make install-system

# Ensure PATH includes installation directory
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Install Fabric Patterns

The Makefile automatically copies patterns to `~/.config/fabric/patterns/`. Verify installation:

```bash
fabric -l | grep video
```

### Optional: Ollama for Visual Analysis

For advanced visual caption generation:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended vision models
ollama pull moondream:1.8b    # Fast model for general captions
ollama pull qwen2.5vl:7b      # Rich model for detailed analysis
```

## 🔧 Usage

### Complete Video Analysis

```bash
# Comprehensive analysis with transcript and visual frames
scribe analyze presentation.mp4 | fabric -p analyze_video_content

# Skip frames for audio-only content
scribe analyze --skip-frames podcast.mp3 | fabric -p summarize_lecture

# Skip transcript for silent/visual content
scribe analyze --skip-transcript silent_demo.mp4 | fabric -p analyze_frames
```

### High-Performance Transcription

```bash
# Auto-select best backend (MLX on Apple Silicon, faster-whisper elsewhere)
scribe transcribe video.mp4 | fabric -p summarize_lecture

# Force MLX for maximum speed on Apple Silicon
scribe transcribe --backend mlx --model large video.mp4 | fabric -p analyze_video_content

# Use different model sizes
scribe transcribe --model tiny fast_video.mp4     # Fastest processing
scribe transcribe --model large important.mp4    # Best accuracy
```

### Visual Frame Analysis

```bash
# Extract frames every 60 seconds
scribe frames --interval 60 tutorial.mp4 | fabric -p analyze_frames

# High-detail extraction for presentations
scribe frames --interval 15 --max-frames 100 slides.mp4 | fabric -p extract_visual_content
```

### Advanced Visual Captions with Ollama

```bash
# Generate captions for trading charts and diagrams
scribe captions trading_video.mp4 | fabric -p extract_trading_strategy

# Two-pass processing: fast overview + detailed analysis
scribe captions --two-pass --rich-model qwen2.5vl:7b chart_analysis.mp4

# Process pre-extracted frames
scribe frames video.mp4 | scribe captions | fabric -p analyze_video_content
```

### YouTube Video Processing

```bash
# Full analysis with downloaded video
scribe analyze "https://www.youtube.com/watch?v=VIDEO_ID" | fabric -p analyze_video_content

# Use YouTube's native transcript (faster, requires captions)
scribe analyze --youtube-transcript "https://youtu.be/VIDEO_ID" | fabric -p summarize_lecture

# Extract key insights from trading education
scribe analyze --youtube-transcript "https://youtube.com/watch?v=TRADING_ID" | fabric -p analyze_trading_video
```

## 📊 Trading-Focused Workflows

Screenscribe includes specialized patterns for financial video analysis:

### Market Analysis

```bash
# Comprehensive trading video analysis
scribe analyze trading_tutorial.mp4 | fabric -p analyze_trading_video

# Extract specific trading strategies
scribe analyze strategy_video.mp4 | fabric -p extract_trading_strategy

# Technical analysis focus
scribe analyze chart_analysis.mp4 | fabric -p extract_technical_analysis

# Market commentary processing
scribe analyze market_update.mp4 | fabric -p analyze_market_commentary
```

### Advanced Trading Analysis with Visual Captions

```bash
# Complete workflow: transcript + visual analysis + strategy extraction
scribe analyze --generate-captions trading_course.mp4 | fabric -p extract_trading_strategy

# Two-pass visual analysis for detailed chart understanding
scribe analyze --generate-captions --captions-two-pass chart_webinar.mp4 | fabric -p extract_technical_analysis
```

### Multi-Step Analysis Workflows

```bash
# Chain multiple patterns for comprehensive insights
scribe analyze webinar.mp4 | \
  fabric -p analyze_trading_video | \
  fabric -p extract_actionable_trades | \
  fabric -p format_trade_journal

# Save intermediate results for multiple analyses
scribe analyze workshop.mp4 > workshop_data.json
cat workshop_data.json | fabric -p analyze_video_content > summary.md
cat workshop_data.json | fabric -p extract_action_items > todos.md
```

## ⚡ Performance Optimization

### Apple Silicon Acceleration

MLX Whisper provides dramatic performance improvements on M1/M2/M3 Macs:

```bash
# Performance comparison (49-minute video):
# CPU-only (faster-whisper): ~3000s (50 minutes)
# MLX GPU acceleration:      ~103s (1.7 minutes) - 30x faster!

# Enable MLX acceleration (automatic on Apple Silicon)
scribe analyze --whisper-backend mlx video.mp4 | fabric -p analyze_video_content
```

### Model Selection Guidelines

| Model | Speed | Accuracy | Use Case |
|-------|--------|----------|----------|
| `tiny` | Fastest | Basic | Quick previews, low-quality audio |
| `base` | Fast | Good | **Default** - balanced speed/accuracy |
| `small` | Medium | Better | Detailed analysis, clear audio |
| `medium` | Slow | Very Good | Important content, multiple speakers |
| `large` | Slowest | Best | Critical accuracy, complex audio |

```bash
# Optimize for speed
scribe analyze --whisper-model tiny --frame-interval 60 video.mp4

# Optimize for accuracy
scribe analyze --whisper-model large --frame-interval 15 video.mp4
```

### Frame Extraction Optimization

```bash
# Fewer frames for faster processing
scribe analyze --frame-interval 90 --max-frames 20 long_video.mp4

# More frames for detailed visual analysis
scribe analyze --frame-interval 10 --max-frames 200 presentation.mp4

# Skip unnecessary processing
scribe analyze --skip-frames audio_only.mp3      # Audio-only content
scribe analyze --skip-transcript silent_video.mp4 # Visual-only content
```

## 🛠️ CLI Reference

### Main Command: `scribe`

```bash
scribe [command] [flags]

Available Commands:
  analyze     Complete video analysis (transcript + frames + optional captions)
  transcribe  Extract transcript only using Whisper
  frames      Extract visual frames only
  captions    Generate visual captions using Ollama vision models
  update      Update scribe from GitHub releases
  uninstall   Remove scribe tools and patterns
  version     Show version information
  help        Help about any command

Global Flags:
  -v, --verbose   Verbose output
      --help      Show help
```

### `scribe analyze` - Complete Video Analysis

```bash
scribe analyze [flags] VIDEO_FILE_OR_YOUTUBE_URL

Whisper Options:
  --whisper-model string     Whisper model (tiny,base,small,medium,large) [default: base]
  --whisper-backend string   Backend (auto,mlx,faster-whisper,openai-whisper) [default: auto]

Frame Options:
  --frame-interval int       Frame extraction interval in seconds [default: 30]
  --frame-format string      Output format (base64,paths,both) [default: base64]
  --max-frames int           Maximum frames to extract [default: 50]
  --frame-quality int        JPEG quality 1-5 [default: 2]
  --frame-resize string      Frame dimensions [default: 320x240]

Processing Options:
  --skip-transcript          Skip transcript extraction (frames only)
  --skip-frames             Skip frame extraction (transcript only)
  --youtube-transcript      Use YouTube native transcript (YouTube URLs only)

Caption Generation:
  --generate-captions       Generate visual captions using Ollama
  --captions-model string   Ollama model for captions [default: moondream:1.8b]
  --captions-workers int    Parallel caption workers [default: 4]
  --captions-two-pass       Use two-pass processing (fast + rich models)
  --captions-rich-model string  Rich model for two-pass [default: qwen2.5vl:7b]
  --ollama-url string       Ollama API URL [default: http://localhost:11434]
```

### `scribe transcribe` - Transcript Only

```bash
scribe transcribe [flags] VIDEO_FILE

Options:
  --model string      Whisper model size [default: base]
  --language string   Force specific language
  --backend string    Transcription backend [default: auto]
```

### `scribe frames` - Frame Extraction Only

```bash
scribe frames [flags] VIDEO_FILE

Options:
  --interval int      Frame interval in seconds [default: 30]
  --format string     Output format (base64,paths,both) [default: base64]
  --max-frames int    Maximum frames to extract [default: 50]
  --quality int       JPEG quality 1-5 [default: 2]
  --resize string     Frame dimensions [default: 320x240]
```

### `scribe captions` - Visual Caption Generation

```bash
scribe captions [flags] [FRAME_JSON_OR_VIDEO_FILE]

Options:
  --model string         Ollama vision model [default: moondream:1.8b]
  --workers int          Parallel workers [default: 4]
  --two-pass            Use two-pass processing
  --rich-model string   Rich model for two-pass [default: qwen2.5vl:7b]
  --ollama-url string   Ollama API URL [default: http://localhost:11434]
```

## 📋 Available Fabric Patterns

### General Video Analysis
- **`analyze_video_content`** - Comprehensive video analysis with timeline
- **`extract_code_from_video`** - Extract and format code snippets from tutorials

### Trading-Specific Patterns
- **`analyze_trading_video`** - Complete trading education analysis
- **`extract_technical_analysis`** - Chart patterns and technical indicators
- **`extract_trading_strategy`** - Systematic trading strategies and setups
- **`analyze_market_commentary`** - Market outlook and predictions

## 📄 JSON Output Format

Screenscribe outputs structured JSON for seamless Fabric integration:

```json
{
  "transcript": {
    "text": "Complete transcript text...",
    "segments": [
      {"id": 0, "start": 0.0, "end": 5.2, "text": "Hello and welcome..."}
    ],
    "language": "en",
    "duration": 1847.3,
    "backend": "mlx-whisper",
    "source_file": "video.mp4",
    "model": "base",
    "timestamp": 1703123456.789
  },
  "frames": {
    "source_file": "video.mp4",
    "duration": 1847.3,
    "frame_interval": 30,
    "frame_count": 62,
    "frame_size": "320x240",
    "timestamp": 1703123456,
    "frames": [
      {"frame_number": 1, "timestamp": 0, "data": "base64_image_data..."}
    ]
  },
  "captions": {
    "source_file": "video.mp4",
    "processed_at": 1703123456,
    "total_frames": 62,
    "processed_time": 45.2,
    "models": ["moondream:1.8b", "qwen2.5vl:7b"],
    "frames": [
      {
        "frame": "frame_0001.jpg",
        "timestamp": 0,
        "caption": "Trading chart showing candlestick patterns with support levels marked",
        "confidence": 0.95
      }
    ]
  },
  "metadata": {
    "source_file": "video.mp4",
    "duration": 1847.3,
    "processed_at": 1703123456,
    "whisper_model": "base",
    "whisper_backend": "mlx-whisper",
    "frame_interval": 30,
    "frame_count": 62
  }
}
```

## 🔄 Management Commands

### Self-Update

```bash
# Update to latest version from GitHub
scribe update

# Or use flag form
scribe --update
```

### Uninstall

```bash
# Remove all scribe tools and patterns
scribe uninstall

# Or use flag form
scribe --uninstall
```

## 🛠️ Development and Building

### Build from Source

```bash
# Clone repository
git clone https://github.com/grimmolf/screenscribe.git
cd screenscribe/fabric-extension

# Build for current platform
make build

# Build for all platforms
make build-all

# Run tests
make test

# Install development version
make install
```

### Available Make Targets

- `make build` - Build scribe binary for current platform
- `make build-all` - Cross-compile for all supported platforms
- `make install` - Install to `~/.local/bin`
- `make install-system` - Install to `/usr/local/bin` (requires sudo)
- `make test` - Run functionality tests
- `make clean` - Remove build artifacts
- `make deps` - Show required dependencies
- `make uninstall` - Remove installed tools

## 🛠️ Troubleshooting

### Common Issues

**"scribe: command not found"**
- Ensure `~/.local/bin` is in PATH: `echo $PATH`
- Add to shell profile: `export PATH="$HOME/.local/bin:$PATH"`
- Reload shell: `source ~/.bashrc` or restart terminal

**"MLX whisper not available"**
- Install MLX: `pip3 install mlx-whisper`
- Only works on Apple Silicon (M1/M2/M3) Macs
- Falls back to faster-whisper automatically

**Slow transcription performance**
- On Apple Silicon: Install `mlx-whisper` for 30x speedup
- Use smaller models: `--whisper-model tiny`
- Check backend: `scribe analyze --whisper-backend mlx`

**"YouTube processing failed"**
- Install yt-dlp: `pip3 install yt-dlp`
- Update yt-dlp: `pip3 install --upgrade yt-dlp`
- Check URL format and video availability
- Some videos may be region-restricted

**"Ollama model not available"**
- Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
- Pull model: `ollama pull moondream:1.8b`
- Check Ollama service: `ollama list`

**"FFmpeg not found"**
- Install FFmpeg for your platform
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### Performance Tips

1. **Use MLX on Apple Silicon**: Install `mlx-whisper` for dramatic speed improvements
2. **Choose appropriate models**: `tiny` for speed, `large` for accuracy
3. **Adjust frame intervals**: Increase for faster processing, decrease for more detail
4. **Skip unnecessary components**: Use `--skip-frames` for audio-only content
5. **Batch processing**: Save intermediate JSON for multiple pattern analyses

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test: `make test`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Screenscribe** - Bringing AI-powered video analysis to the Fabric ecosystem with lightning-fast transcription and intelligent visual understanding.