# Screenscribe Fabric Extension

This extension adds video processing capabilities to [Fabric](https://github.com/danielmiessler/fabric) through helper tools and specialized patterns.

## 🎯 Overview

Transform your video analysis workflow with Fabric's AI patterns:

```bash
# Basic video analysis
video_analyze tutorial.mp4 | fabric -p analyze_video_content

# Extract code from programming tutorials  
video_analyze coding_tutorial.mp4 | fabric -p extract_code_from_video

# Trading and financial analysis
video_analyze trading_webinar.mp4 | fabric -p analyze_trading_video
```

## 📦 Installation

### Prerequisites

1. **Fabric** - Install the [Fabric framework](https://github.com/danielmiessler/fabric)
2. **Go 1.21+** - For building the helper tools
3. **Python 3.9+** - For Whisper transcription
4. **FFmpeg** - For video processing
5. **jq** - For JSON processing (frame extraction)

### Install Dependencies

```bash
# macOS
brew install go python3 ffmpeg jq

# Ubuntu/Debian
sudo apt update
sudo apt install golang-go python3 python3-pip ffmpeg jq

# Fedora
sudo dnf install go python3 python3-pip ffmpeg jq
```

### Install Python Dependencies

```bash
# Required for transcription
pip3 install faster-whisper

# Optional: For Apple Silicon GPU acceleration (20-30x faster)
pip3 install mlx-whisper  # M1/M2/M3 Macs only

# Optional: Fallback transcription engine
pip3 install openai-whisper
```

### Build and Install Helper Tools

```bash
# Clone or navigate to the fabric-extension directory
cd fabric-extension

# Make scripts executable
chmod +x scripts/*.sh scripts/*.py

# Build Go helper tools
go mod download
go build -o bin/whisper_transcribe ./cmd/whisper_transcribe
go build -o bin/video_frames ./cmd/video_frames  
go build -o bin/video_analyze ./cmd/video_analyze

# Install to system PATH
sudo cp bin/* /usr/local/bin/
sudo cp scripts/whisper_wrapper.py /usr/local/bin/
sudo cp scripts/extract_frames.sh /usr/local/bin/

# Or install to user directory
mkdir -p ~/.local/bin
cp bin/* ~/.local/bin/
cp scripts/whisper_wrapper.py ~/.local/bin/
cp scripts/extract_frames.sh ~/.local/bin/

# Make sure ~/.local/bin is in your PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Install Fabric Patterns

```bash
# Copy patterns to your Fabric patterns directory
# (Adjust path based on your Fabric installation)
cp -r patterns/* ~/.config/fabric/patterns/
```

### Configuration (Optional)

Add to your `~/.config/fabric/.env`:

```bash
# Video processing defaults
VIDEO_WHISPER_MODEL=base
VIDEO_FRAME_INTERVAL=30
VIDEO_WHISPER_BACKEND=auto
```

## 🚀 Usage

### Basic Video Analysis

```bash
# Comprehensive video analysis
video_analyze presentation.mp4 | fabric -p analyze_video_content

# Transcript-only analysis
video_analyze --skip-frames audio.mp3 | fabric -p analyze_video_content

# Frames-only analysis  
video_analyze --skip-transcript silent_video.mp4 | fabric -p analyze_video_content
```

### Individual Helper Tools

```bash
# Just transcription
whisper_transcribe lecture.mp4 | fabric -p summarize_lecture

# Just frame extraction
video_frames tutorial.mp4 --interval 60 | fabric -p analyze_frames

# High-quality transcription with MLX (Apple Silicon)
whisper_transcribe --model large --backend mlx video.mp4 | fabric -p analyze_video_content
```

### Trading and Financial Analysis

```bash
# Comprehensive trading analysis
video_analyze trading_tutorial.mp4 | fabric -p analyze_trading_video

# Extract specific trading strategies
video_analyze strategy_video.mp4 | fabric -p extract_trading_strategy

# Technical analysis focus
video_analyze chart_analysis.mp4 | fabric -p extract_technical_analysis

# Market commentary processing
video_analyze market_update.mp4 | fabric -p analyze_market_commentary
```

### Advanced Workflows

```bash
# Chain multiple patterns for comprehensive analysis
video_analyze webinar.mp4 | \
  fabric -p analyze_trading_video | \
  fabric -p extract_actionable_trades | \
  fabric -p format_trade_journal

# Save intermediate results for multiple analyses
video_analyze workshop.mp4 > workshop_data.json
cat workshop_data.json | fabric -p analyze_video_content > summary.md
cat workshop_data.json | fabric -p extract_action_items > todos.md

# Combine with other Fabric features
video_analyze news_segment.mp4 | \
  fabric -p extract_main_topics | \
  fabric -p research_topics --search
```

## 🔧 Helper Tools Reference

### `video_analyze`

Main orchestrator tool that combines transcript and frame extraction.

```bash
video_analyze [OPTIONS] VIDEO_FILE

Options:
  --whisper-model MODEL     Whisper model (tiny, base, small, medium, large) [default: base]
  --whisper-backend BACKEND Backend (auto, mlx, faster-whisper, openai-whisper) [default: auto]
  --frame-interval SECONDS  Frame extraction interval [default: 30]
  --frame-format FORMAT     Frame format (base64, paths, both) [default: base64]
  --max-frames COUNT        Maximum frames to extract [default: 50]
  --skip-transcript         Skip transcript extraction (frames only)
  --skip-frames            Skip frame extraction (transcript only)
  --verbose, -v            Verbose output
```

### `whisper_transcribe`

Dedicated transcription tool.

```bash
whisper_transcribe [OPTIONS] VIDEO_FILE

Options:
  --model, -m MODEL        Whisper model size [default: base]
  --language, -l LANG      Force specific language
  --backend BACKEND        Transcription backend [default: auto]
  --verbose, -v           Verbose output
```

### `video_frames`

Dedicated frame extraction tool.

```bash
video_frames [OPTIONS] VIDEO_FILE

Options:
  --interval, -i SECONDS   Frame interval [default: 30]
  --format, -f FORMAT      Output format (base64, paths, both) [default: base64]
  --max-frames, -m COUNT   Maximum frames [default: 50]
  --quality, -q LEVEL      JPEG quality 1-5 [default: 2]
  --resize, -r WxH         Frame dimensions [default: 320x240]
  --verbose, -v           Verbose output
```

## 📋 Available Fabric Patterns

### General Video Analysis
- `analyze_video_content` - Comprehensive video analysis with timeline
- `extract_code_from_video` - Extract and format code snippets from tutorials

### Trading-Specific Patterns  
- `analyze_trading_video` - Complete trading education analysis
- `extract_technical_analysis` - Chart patterns and indicators
- `extract_trading_strategy` - Systematic trading strategies
- `analyze_market_commentary` - Market outlook and predictions

## ⚡ Performance Optimization

### Apple Silicon Acceleration

For 20-30x faster transcription on M1/M2/M3 Macs:

```bash
# Install MLX Whisper
pip3 install mlx-whisper

# Use MLX backend
video_analyze --whisper-backend mlx video.mp4 | fabric -p analyze_video_content

# Performance comparison (49-minute video):
# CPU only: ~3000s (50 minutes)
# MLX GPU:  ~103s (1.7 minutes)
```

### Model Selection

```bash
# Fast processing
video_analyze --whisper-model tiny video.mp4

# Best accuracy
video_analyze --whisper-model large video.mp4

# Balanced (recommended)
video_analyze --whisper-model base video.mp4  # Default
```

### Frame Extraction Optimization

```bash
# Fewer frames for faster processing
video_analyze --frame-interval 60 --max-frames 20 video.mp4

# More frames for detailed analysis
video_analyze --frame-interval 15 --max-frames 100 video.mp4

# Skip frames for audio-only content
video_analyze --skip-frames podcast.mp3
```

## 🛠️ Troubleshooting

### Common Issues

**"whisper_transcribe not found"**
- Ensure Go tools are built and in PATH
- Check `which whisper_transcribe`

**"ffmpeg not found"**
- Install FFmpeg for your operating system
- Verify with `ffmpeg -version`

**"No module named 'faster_whisper'"**
- Install Python dependencies: `pip3 install faster-whisper`

**Slow transcription on Apple Silicon**
- Install MLX: `pip3 install mlx-whisper`
- Use MLX backend: `--whisper-backend mlx`

**"Pattern not found" in Fabric**
- Copy patterns to Fabric directory: `cp -r patterns/* ~/.config/fabric/patterns/`
- Verify pattern location: `fabric -l | grep video`

### Performance Tips

1. **Use appropriate Whisper model**: `tiny` for speed, `large` for accuracy
2. **Enable Apple Silicon acceleration**: Install `mlx-whisper` and use `--whisper-backend mlx`
3. **Adjust frame extraction**: Increase `--frame-interval` for faster processing
4. **Skip unnecessary components**: Use `--skip-frames` for audio-only analysis

## 📄 JSON Output Format

The tools output structured JSON that Fabric patterns can process:

```json
{
  "transcript": {
    "text": "Complete transcript text...",
    "segments": [
      {"id": 0, "start": 0.0, "end": 5.2, "text": "Hello and welcome..."}
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
    "processed_at": 1703123456
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Fabric Extension for Screenscribe** - Bringing AI-powered video analysis to the Fabric ecosystem.