# screenscribe

<div align="center">

🎬 **Transform videos into structured, searchable notes with AI-powered analysis**

[![Go](https://img.shields.io/badge/go-1.21+-00ADD8.svg)](https://golang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Fabric](https://img.shields.io/badge/Fabric-Integration-purple.svg)](https://github.com/danielmiessler/fabric)

</div>

**screenscribe** turns your videos into comprehensive, structured notes. It extracts audio transcripts, analyzes visual content with AI, and creates searchable documents. Perfect for lectures, meetings, tutorials, and any video content you want to reference later.

> 🍎 **Apple Silicon**: Get **20-30x faster** transcription with automatic MLX GPU acceleration on M1/M2/M3 Macs!

> 🧵 **Latest**: Enhanced unified `scribe` CLI with version support, flexible update/uninstall options, and intelligent Apple Silicon auto-detection. Built on the amazing [Fabric project](https://github.com/danielmiessler/fabric) by Daniel Miessler.

## 🚀 Quick Start

```bash
# 1. Install system dependencies
# macOS: brew install ffmpeg go jq
# Ubuntu: sudo apt install ffmpeg golang-go jq

# 2. Install Fabric (if not already installed)
go install github.com/danielmiessler/fabric@latest

# 3. Install screenscribe
git clone https://github.com/grimmolf/screenscribe.git
cd screenscribe/fabric-extension
make build && make install

# 4. Set up Fabric with your AI provider (one-time setup)
fabric --setup

# 5. Process your first video
scribe analyze video.mp4 | fabric -p analyze_video_content
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

**Intelligent Auto-Detection & Apple Silicon Optimization:**

| Hardware | Backend | Processing Time | Speedup |
|----------|---------|----------------|---------|
| **Apple Silicon** | MLX (GPU) | 103s for 49min video | **29x faster** |
| M1/M2/M3 | MLX → faster-whisper | Auto-detects best option | **20-30x** |
| Other Platforms | faster-whisper | CPU-optimized processing | **3x faster** |

✅ **Auto-detects platform and selects optimal backend**  
✅ **Predownloads MLX models for offline reliability**  
✅ **Graceful fallbacks ensure it always works**

## 🎯 Basic Usage

### Process Any Video
```bash
# Extract video data (local processing only)
scribe analyze lecture.mp4 > video_data.json

# Analyze with AI (uses your Fabric-configured AI provider)
scribe analyze lecture.mp4 | fabric -p analyze_video_content

# Trading-specific analysis
scribe analyze trading_webinar.mp4 | fabric -p analyze_trading_video

# Programming tutorial analysis
scribe analyze coding_lesson.mp4 | fabric -p extract_code_from_video
```

### Processing Options
```bash
# Automatic backend selection (recommended - auto-detects Apple Silicon)
scribe analyze video.mp4 | fabric -p analyze_video_content

# Fast processing (good for previews)
scribe analyze video.mp4 --whisper-model tiny | fabric -p analyze_video_content

# High quality transcription (uses MLX GPU on Apple Silicon automatically)
scribe analyze video.mp4 --whisper-model medium | fabric -p analyze_video_content

# Force specific backend (if needed)
scribe analyze video.mp4 --whisper-backend mlx | fabric -p analyze_video_content
scribe analyze video.mp4 --whisper-backend faster-whisper | fabric -p analyze_video_content

# Processing-only options
scribe analyze video.mp4 --skip-transcript | fabric -p analyze_video_content  # frames only
scribe analyze video.mp4 --skip-frames | fabric -p analyze_video_content      # transcript only

# Custom frame intervals
scribe analyze video.mp4 --frame-interval 60 | fabric -p analyze_video_content
```

### YouTube Video Processing
```bash
# Process YouTube videos directly (requires yt-dlp)
scribe analyze "https://www.youtube.com/watch?v=VIDEO_ID" | fabric -p analyze_video_content

# Use YouTube's native transcripts (faster, when available)
scribe analyze --youtube-transcript "https://youtu.be/VIDEO_ID" | fabric -p summarize_lecture

# YouTube with custom frame intervals
scribe analyze --frame-interval 120 "https://youtube.com/watch?v=VIDEO_ID" | fabric -p extract_code_from_video

# YouTube transcript only (no video download)
scribe analyze --youtube-transcript --skip-frames "https://youtube.com/watch?v=VIDEO_ID" | fabric -p analyze_video_content
```

## 🧵 Advanced AI Analysis with Fabric

Supercharge your video analysis by combining screenscribe with [Fabric's AI patterns](https://github.com/danielmiessler/fabric):

```bash
# Analyze videos with specialized AI patterns
scribe analyze tutorial.mp4 | fabric -p analyze_video_content
scribe analyze trading_webinar.mp4 | fabric -p analyze_trading_video  
scribe analyze coding_lesson.mp4 | fabric -p extract_code_from_video

# Chain multiple AI analyses
scribe analyze presentation.mp4 | \
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
# macOS
brew install ffmpeg go jq

# Ubuntu/Debian
sudo apt install ffmpeg golang-go jq

# Fedora/RHEL
sudo dnf install ffmpeg go jq

# Install Fabric (if not already installed)
go install github.com/danielmiessler/fabric@latest

# For Apple Silicon: Install MLX for 20-30x speedup (optional but recommended)
pip install mlx-whisper

# For YouTube support (optional)
pip install yt-dlp
```

### Install screenscribe

**Option 1: Build from Source**
```bash
# Clone and build screenscribe Fabric extension
git clone https://github.com/grimmolf/screenscribe.git
cd screenscribe/fabric-extension

# Build and install tools (installs to ~/.local/bin/)
make build && make install

# For Apple Silicon: Predownload MLX models for offline reliability (recommended)
python3 scripts/predownload_mlx_models.py --auto

# Copy AI patterns to your Fabric configuration
cp -r patterns/* ~/.config/fabric/patterns/

# Make sure ~/.local/bin is in your PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Option 2: Pre-built Binaries**
```bash
# Download pre-built release for your platform:
# - screenscribe-macos-amd64.tar.gz (macOS Intel)
# - screenscribe-macos-arm64.tar.gz (macOS Apple Silicon)  
# - screenscribe-linux-amd64.tar.gz (Fedora/Ubuntu x64)
# - screenscribe-linux-arm64.tar.gz (Linux ARM64)

# Extract and install
tar -xzf screenscribe-[platform].tar.gz
cd [platform-directory]
./install.sh
```

### Configure Fabric
```bash
# Configure Fabric with your preferred AI provider (one-time setup)
fabric --setup

# This will guide you through setting up your AI provider
# Fabric handles all API configuration - no additional setup needed
```

### Verify Installation
```bash
# Check that scribe is installed
scribe --help
scribe analyze --help
scribe transcribe --help
scribe frames --help

# Check available patterns
fabric -l | grep video
```

## 🎯 Common Use Cases

### For Students
```bash
# Turn lecture recordings into study guides
scribe analyze lecture.mp4 | fabric -p analyze_video_content > study-guide.md

# Process multiple lectures
for file in lectures/*.mp4; do
  scribe analyze "$file" | fabric -p analyze_video_content > "notes/$(basename "$file" .mp4)-notes.md"
done
```

### For Professionals  
```bash
# Convert meeting recordings to action items
scribe analyze meeting.mp4 | fabric -p analyze_video_content | fabric -p extract_action_items

# Analyze conference talks
scribe analyze conference-talk.mp4 --whisper-model large | fabric -p analyze_video_content
```

### For Developers
```bash
# Extract code from programming tutorials
scribe analyze coding-tutorial.mp4 | fabric -p extract_code_from_video

# Create documentation from recorded demos
scribe analyze demo.mp4 | fabric -p analyze_video_content | fabric -p create_documentation
```

### For Traders
```bash
# Analyze trading education content
scribe analyze trading-course.mp4 | fabric -p analyze_trading_video
scribe analyze market-analysis.mp4 | fabric -p extract_technical_analysis
```

## ⚙️ Configuration

### Advanced Options
```bash
# Use different Whisper models
scribe analyze video.mp4 --whisper-model large

# Skip transcript or frames for faster processing
scribe analyze video.mp4 --skip-transcript  # frames only
scribe analyze video.mp4 --skip-frames      # transcript only

# Custom frame intervals
scribe analyze video.mp4 --frame-interval 60  # one frame per minute

# Force specific backend
scribe analyze video.mp4 --whisper-backend mlx      # Apple Silicon GPU
scribe analyze video.mp4 --whisper-backend faster-whisper  # CPU optimization

# Individual tools for specific tasks
scribe transcribe video.mp4 --model large | fabric -p summarize_lecture
scribe frames video.mp4 --interval 120 | fabric -p extract_visual_content
```

### Fabric Pattern Chaining
```bash
# List available video analysis patterns
fabric -l | grep video

# Chain patterns for complex workflows
scribe analyze tutorial.mp4 | \
  fabric -p analyze_video_content | \
  fabric -p extract_key_points | \
  fabric -p create_summary
```

## 🔄 Updates & Management

### Version Information
```bash
# Check version
scribe --version
scribe version  # detailed info with git commit and build date
```

### Self-Update (Multiple Ways)
```bash
# Update scribe tools from GitHub (both forms work)
scribe update
scribe --update
```

### Uninstallation (Multiple Ways)
```bash
# Remove scribe tools and Fabric patterns (both forms work)
scribe uninstall
scribe --uninstall

# Alternative: use Makefile (from source directory)
make uninstall
```

### Apple Silicon Model Management
```bash
# Check MLX model cache status
python3 scripts/predownload_mlx_models.py

# Predownload all models for offline use
python3 scripts/predownload_mlx_models.py --auto
```

## 🛠️ Troubleshooting

**Common Issues:**

- **"scribe not found"** → Run `make install` from fabric-extension directory, ensure `~/.local/bin` is in PATH
- **"FFmpeg not found"** → Install FFmpeg for your operating system
- **Apple Silicon not using MLX** → Install MLX: `pip install mlx-whisper`, then run predownload script
- **"float16 compute type error"** → Auto-detection will fix this; use `--whisper-backend auto` 
- **MLX model download failed** → Run `python3 scripts/predownload_mlx_models.py --auto`
- **AI analysis errors** → Run `fabric --setup` to configure your AI provider
- **Out of memory** → Use `--whisper-model tiny` for large videos
- **YouTube download fails** → Install/update yt-dlp: `pip install --upgrade yt-dlp`
- **Pattern not found** → Ensure patterns installed: `cp -r patterns/* ~/.config/fabric/patterns/`

**Performance Tips:**
- **Apple Silicon**: Install MLX (`pip install mlx-whisper`) for automatic 20-30x GPU acceleration
- **Model Selection**: Use `tiny` for speed, `medium` for balanced performance, `large` for accuracy
- **Selective Processing**: Use `--skip-transcript` or `--skip-frames` for faster processing
- **YouTube Optimization**: Use `--youtube-transcript` when captions are available (much faster)
- **Offline Reliability**: Run `python3 scripts/predownload_mlx_models.py --auto` to cache models
- **Workflow Chaining**: Fabric patterns can be chained for complex analysis workflows

**Get More Help:**
- Check the `--help` flag on any command
- See [Fabric Integration Guide](./docs/FABRIC_INTEGRATION.md) for advanced workflows
- For development and contributing, see [Development Guide](./DEVELOPMENT.md)

## 📚 Documentation

- **[Fabric Integration Guide](./docs/FABRIC_INTEGRATION.md)** - Advanced AI workflows and pattern usage
- **[Development Guide](./DEVELOPMENT.md)** - For developers and contributors

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Support & Contributing

- **Questions**: [GitHub Discussions](https://github.com/grimmolf/screenscribe/discussions)
- **Issues**: [GitHub Issues](https://github.com/grimmolf/screenscribe/issues)
- **Contributing**: See [Development Guide](./DEVELOPMENT.md)

---

**Special Thanks**: To [Daniel Miessler](https://github.com/danielmiessler) and the [Fabric project](https://github.com/danielmiessler/fabric) for creating the powerful AI pattern framework that enables advanced video analysis workflows.