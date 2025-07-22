# Screenscribe - AI Video Analysis for Fabric

Transform any video into structured insights using AI transcription and visual analysis. Purpose-built for [Fabric](https://github.com/danielmiessler/fabric) with 20-30x faster processing on Apple Silicon.

## ⚡ Quick Start (30 seconds)

```bash
# 1. Install (if you have Go 1.21+, FFmpeg, and Fabric)
make install-scribe

# 2. Analyze any video instantly
scribe analyze your_video.mp4 | fabric -p analyze_video_content

# 3. Extract trading strategies from financial videos
scribe analyze trading_video.mp4 | fabric -p extract_trading_strategy
```

**✅ Success check**: You should see JSON output with transcript and analysis.

## 📋 Prerequisites Checklist

Before installing, ensure you have:

- [ ] **Go 1.21+** - `go version` should show 1.21+
- [ ] **FFmpeg** - `ffmpeg -version` should work  
- [ ] **Fabric** - `fabric --version` should work
- [ ] **Python 3.8+** - For Whisper models: `python3 --version`

**Optional for enhanced performance:**
- [ ] **Apple Silicon Mac** - For 30x faster MLX transcription
- [ ] **Ollama** - For visual chart analysis: `ollama --version`

## 🎯 What You Can Do

### Simple Examples (Start Here)

```bash
# Basic transcription
scribe transcribe lecture.mp4

# YouTube video analysis
scribe analyze "https://youtube.com/watch?v=VIDEO_ID" | fabric -p summarize_lecture

# Extract frames every 30 seconds
scribe frames tutorial.mp4 --interval 30
```

### Powerful Workflows

```bash
# Trading strategy extraction with transcript only
scribe analyze trading_course.mp4 | fabric -p extract_trading_strategy

# Trading strategy with visual analysis (CORRECT pipeline)
scribe analyze --generate-captions --captions-two-pass --captions-rich-model qwen2.5vl:72b trading_course.mp4 | fabric -p extract_trading_strategy

# Batch process multiple videos
for video in *.mp4; do
  scribe analyze "$video" | fabric -p analyze_video_content > "${video%.mp4}_analysis.md"
done
```

### Advanced Use Cases

```bash
# High-frequency trading analysis with frame-by-frame charts
scribe analyze --frame-interval 5 --generate-captions day_trading.mp4 | fabric -p extract_trading_strategy

# Multi-modal analysis: audio + visual content  
scribe analyze --model large --generate-captions --captions-two-pass webinar.mp4 | fabric -p comprehensive_analysis

# Process with specific models
scribe transcribe --backend mlx --model large audio.mp3
scribe captions --model qwen2.5vl:7b --workers 8 video.mp4
```

## 📦 Installation

### Method 1: Quick Install (Recommended)

```bash
# Clone and build
git clone https://github.com/grimmolf/screenscribe.git
cd screenscribe/fabric-extension
make install-scribe

# Verify installation
scribe --version
```

### Method 2: Manual Build

```bash
cd screenscribe/fabric-extension
go mod download
go build -o scribe cmd/scribe/main.go
cp scribe ~/.local/bin/
```

### Method 3: Performance Setup (Apple Silicon)

```bash
# Install for 30x faster transcription
pip3 install mlx-whisper

# Install for visual analysis
brew install ollama
ollama pull moondream:1.8b  # Fast model
ollama pull qwen2.5vl:7b   # Detailed model
```

**✅ Installation check**: Run `scribe analyze --help` - you should see usage options.

## 🚀 Key Features

**Performance** 
- 30x faster on Apple Silicon (MLX Whisper: 49min video → 103 seconds)
- Automatic backend selection with fallback
- Parallel processing for visual analysis

**AI Integration**
- Multi-model Whisper support (tiny → large)  
- Ollama vision models for chart analysis
- Two-pass processing (fast + detailed)

**Workflow Integration**
- Native Fabric pattern support
- YouTube URL processing
- Structured JSON output
- Self-updating from GitHub

## 🎓 Usage Patterns

### For Traders
```bash
# ICT mentorship video → trading strategy (faithful extraction)
scribe analyze ict_lesson.mp4 | fabric -p extract_trading_strategy

# Chart analysis with visual captions for comprehensive strategies
scribe analyze --generate-captions chart_review.mp4 | fabric -p extract_trading_strategy

# High-quality analysis with premium vision models
scribe analyze --generate-captions --captions-two-pass --captions-rich-model qwen2.5vl:72b trading_video.mp4 | fabric -p extract_trading_strategy
```

**🎯 Pattern Features**
- **Anti-hallucination**: Only extracts concepts explicitly mentioned by speaker
- **Faithful terminology**: Uses speaker's exact language (e.g., ICT's "seeking liquidity")  
- **Missing section handling**: Shows "*Not discussed*" for omitted concepts
- **Quote validation**: Includes direct quotes supporting each extracted point

### For Educators  
```bash
# Lecture → structured notes
scribe analyze lecture.mp4 | fabric -p create_study_notes

# YouTube course → summary
scribe analyze --youtube-transcript "https://youtube.com/watch?v=ID" | fabric -p summarize_lecture
```

### For Content Creators
```bash
# Video → blog post
scribe analyze tutorial.mp4 | fabric -p create_blog_post

# Podcast → show notes  
scribe transcribe podcast.mp3 | fabric -p create_show_notes
```

## 🔧 Management

```bash
# Update to latest version
scribe update

# Uninstall completely  
scribe uninstall

# Check installation
scribe version
```

## 🛠️ Troubleshooting

**"scribe: command not found"**
```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc  # or restart terminal
```

**Slow transcription**
```bash
# Install MLX for Apple Silicon (30x faster)
pip3 install mlx-whisper

# Use smaller/faster model
scribe transcribe --whisper-model tiny video.mp4
```

**"Unknown flag" errors**
- Use `--rich-model` (not `--keyframe-model`)
- Check flags with: `scribe [command] --help`

**YouTube processing fails**
```bash
pip3 install --upgrade yt-dlp
```

**Ollama model issues**
```bash
# Install and setup
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull moondream:1.8b
ollama list  # verify
```

**Pipeline failures** ("failed to read frames from stdin")
```bash
# WRONG: This fails because analyze outputs transcript, captions expects frames
scribe analyze video.mp4 | scribe captions --two-pass | fabric -p extract_trading_strategy

# CORRECT: Use single command with integrated captions
scribe analyze --generate-captions --captions-two-pass video.mp4 | fabric -p extract_trading_strategy
```

**AI hallucination** (adding concepts not in video)
- The `extract_trading_strategy` pattern now requires explicit mentions only
- Sections not discussed by speaker are marked "*Not discussed*"
- Uses speaker's exact terminology instead of conventional trading concepts

## 📚 Advanced Configuration

<details>
<summary>📖 Complete CLI Reference</summary>

### Core Commands

```bash
# Analysis (main command)
scribe analyze [video_file_or_url] [flags]

# Individual components  
scribe transcribe [video_file_or_url] [flags]
scribe frames [video_file] [flags] 
scribe captions [video_or_frame_data] [flags]
```

### Transcription Flags
```bash
--whisper-model string    Model size: tiny,small,base,medium,large (default: base)
--whisper-backend string  Backend: auto,mlx,faster-whisper,openai-whisper (default: auto)
--whisper-language string Language code (default: auto-detect)
```

### Frame Extraction Flags
```bash
--frame-interval int    Seconds between frames (default: 30)
--max-frames int       Maximum frames to extract (default: 50) 
--frame-format string  Output format: paths,base64 (default: paths)
```

### Caption Generation Flags
```bash
--model string          Vision model (default: moondream:1.8b)
--rich-model string     Rich model for two-pass (default: qwen2.5vl:7b)
--two-pass             Use fast + rich models
--workers int          Parallel workers (default: 4)
--ollama-url string    Ollama API URL (default: http://localhost:11434)
```

### Analysis Flags (combines all above)
```bash
--generate-captions     Include visual analysis
--captions-two-pass    Use two-pass for captions
--skip-frames          Audio-only processing
--youtube-transcript   Use YouTube's transcript
```

</details>

<details>
<summary>🏗️ Architecture & Development</summary>

**Technology Stack**
- **Core**: Go 1.21+ with Cobra CLI framework
- **Transcription**: MLX Whisper (Apple Silicon), faster-whisper, OpenAI Whisper  
- **Vision**: Ollama integration with vision models
- **Media**: FFmpeg for frame extraction
- **AI Integration**: Native Fabric pattern support

**Project Structure**
```
cmd/scribe/
├── main.go                 # CLI entry point and orchestration
├── caption_processor.go    # Ollama vision integration  
├── errors.go              # Comprehensive error handling
├── frame_selector.go      # Trading-focused frame selection
├── ollama_client.go       # Ollama API client
└── transcript_processor.go # Multi-backend transcription
```

**Performance Benchmarks**
- **MLX Whisper (Apple Silicon)**: 49min video → 103 seconds
- **faster-whisper (CPU)**: 49min video → 3000+ seconds  
- **Frame extraction**: 50 frames → 2-5 seconds
- **Vision analysis**: 50 frames → 30-120 seconds (model dependent)

</details>

## 🤝 Contributing & Support

- **Issues**: [GitHub Issues](https://github.com/grimmolf/screenscribe/issues)
- **Discussions**: [GitHub Discussions](https://github.com/grimmolf/screenscribe/discussions)
- **Documentation**: Additional patterns in `patterns/` directory

## 📄 License

MIT License - See LICENSE file for details.

---

**Pro Tip**: Start with simple examples, then gradually explore advanced features. The tool is designed to grow with your needs from basic transcription to sophisticated multi-modal analysis.