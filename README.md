# screenscribe

<div align="center">

🎬 **Transform videos into structured, searchable notes with AI-powered analysis**

[![Go](https://img.shields.io/badge/go-1.21+-00ADD8.svg)](https://golang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Fabric](https://img.shields.io/badge/Fabric-Integration-purple.svg)](https://github.com/danielmiessler/fabric)

</div>

**screenscribe** turns your videos into comprehensive, structured notes. It extracts audio transcripts, analyzes visual content with AI, and creates searchable documents. Perfect for lectures, meetings, tutorials, and any video content you want to reference later.

> 🧵 **New**: screenscribe now includes [Fabric integration](./fabric-extension/) for AI-powered video analysis patterns. Thanks to the amazing [Fabric project](https://github.com/danielmiessler/fabric) by Daniel Miessler for providing the pattern framework that makes advanced video analysis workflows possible.

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
# Fast processing (good for previews)
scribe analyze video.mp4 --whisper-model tiny | fabric -p analyze_video_content

# High quality transcription (best for important content)  
scribe analyze video.mp4 --whisper-model large | fabric -p analyze_video_content

# Frames-only processing (skip transcription)
scribe analyze video.mp4 --skip-transcript | fabric -p analyze_video_content

# Custom frame intervals
scribe analyze video.mp4 --frame-interval 30 | fabric -p analyze_video_content
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

### Self-Update
```bash
# Update scribe tools from GitHub
scribe update
```

### Uninstallation
```bash
# Remove scribe tools and Fabric patterns
scribe uninstall

# Alternative: use Makefile (from source directory)
make uninstall
```

## 🛠️ Troubleshooting

**Common Issues:**

- **"scribe not found"** → Run `make install` from fabric-extension directory, ensure `~/.local/bin` is in PATH
- **"FFmpeg not found"** → Install FFmpeg for your operating system
- **Slow on Apple Silicon** → MLX backend auto-detects and provides 20x speedup
- **AI analysis errors** → Run `fabric --setup` to configure your AI provider
- **Out of memory** → Use `--whisper-model tiny` for large videos
- **YouTube download fails** → Install/update yt-dlp: `pip install --upgrade yt-dlp`
- **YouTube transcript not found** → Use `--youtube-transcript` only if video has captions available

**Performance Tips:**
- Apple Silicon users: MLX backend provides automatic GPU acceleration
- Use `--whisper-model tiny` for speed, `large` for accuracy
- Use `--skip-transcript` or `--skip-frames` for faster processing
- YouTube transcripts: Use `--youtube-transcript` for faster processing when captions are available
- Fabric patterns can be chained for complex analysis workflows

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