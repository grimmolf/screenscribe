# screenscribe

<div align="center">

🎬 **Transform videos into structured, searchable notes with AI-powered analysis**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

</div>

**screenscribe** is a CLI tool that processes videos and screen recordings to extract both audio transcripts and visual context, synthesizing them into comprehensive, structured notes. Perfect for technical tutorials, presentations, lectures, and meetings.

> 🧵 **New**: screenscribe now includes [Fabric integration](./fabric-extension/) for AI-powered video analysis patterns. Thanks to the amazing [Fabric project](https://github.com/danielmiessler/fabric) by Daniel Miessler for providing the pattern framework that makes advanced video analysis workflows possible.

**Key Features:**
- 🎤 **Multi-backend transcription** - Intelligent backend selection with platform optimization
- ⚡ **Apple Silicon GPU acceleration** - 2-8x faster on M1/M2/M3 Macs with MLX backend
- 🚀 **Auto backend detection** - Automatically selects MLX (Apple Silicon) or faster-whisper (universal)
- 👁️ **AI-powered visual analysis** with GPT-4o Vision  
- 📝 **Multiple output formats** - Markdown or HTML with embedded thumbnails
- 🧵 **Fabric AI integration** - Use with [Fabric patterns](https://github.com/danielmiessler/fabric) for advanced workflows
- 📺 **Enhanced YouTube support** - Direct transcript extraction with Whisper fallback
- 📄 **External transcript support** - Use existing transcripts (JSON, SRT, VTT, plain text)
- 🔧 **Global configuration system** - Centralized settings at ~/.config/screenscribe/
- 🔄 **Self-update capability** - Update directly from GitHub
- 🎯 **Customizable AI prompts** - Global prompt directory with easy customization
- ⚡ **Smart NAS handling** - automatically copies network files locally for 10x performance boost
- 🛑 **Responsive interruption** - graceful ctrl+c handling with progress saving
- 🔗 **Multi-command CLI** - config, update, and processing sub-commands

## 🚀 Quick Start

**For development/source code users:**

```bash
# 1. Clone or download this repository
cd /path/to/screenscribe/

# 2. Install from source (with Apple Silicon optimization)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Apple Silicon Macs (M1/M2/M3) - GPU acceleration 2-8x faster
uv tool install --editable './[apple]'

# Other platforms
uv tool install --editable .

# 3. Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# 4. Verify backend selection (optional)
screenscribe --list-backends test.mp4  # Shows available transcription engines

# 5. Process your first video
screenscribe video.mp4
```

## 📦 Installation

### Install from Release (Coming Soon)

Once published to PyPI, you'll be able to install with:

```bash
# One-command install (when released)
curl -LsSf https://raw.githubusercontent.com/screenscribe/screenscribe/main/scripts/install.sh | bash

# Or manually (when released)
uv tool install screenscribe

# For Apple Silicon GPU acceleration (when released)
uv tool install "screenscribe[apple]"
```

### Install for Development (Current)

**If you're working with the source code or cloned this repository:**

```bash
# 1. Navigate to the project directory
cd /path/to/screenscribe/

# 2. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install screenscribe from source (editable mode)
uv tool install --editable .

# 4. For Apple Silicon GPU acceleration (M1/M2/M3 Macs)
uv tool install --editable ".[apple]"

# 5. Install FFmpeg (required)
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg  
# Fedora: sudo dnf install ffmpeg
```

**Why use `--editable .`?**
- Installs from your local source code (not PyPI)
- Changes to code reflect immediately without reinstall
- Perfect for development and testing

### Update

**For development/source code users:**
```bash
# Navigate to screenscribe directory
cd /path/to/screenscribe/

# Pull latest changes
git pull

# Reinstall with latest code (Apple Silicon users - IMPORTANT: Use [apple] for GPU acceleration)
uv tool install --editable './[apple]' --force

# Or for other platforms:
uv tool install --editable . --force
```

**For release users (when published):**
```bash
# Update to latest version
uv tool upgrade screenscribe
```

### Uninstall

```bash
# Remove screenscribe
uv tool uninstall screenscribe

# Optional: Remove uv if you don't use it for other projects
curl -LsSf https://astral.sh/uv/uninstall.sh | sh
```

### Setup

Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your_openai_api_key'

# Make it permanent (add to ~/.bashrc, ~/.zshrc, etc.)
echo 'export OPENAI_API_KEY="your_key_here"' >> ~/.bashrc
```

## ⚡ Performance

**Apple Silicon Performance (M1/M2/M3 Macs)**:
- **MLX Backend**: 2-8x faster transcription with GPU acceleration
- **Automatic Selection**: MLX backend automatically chosen on Apple Silicon
- **Real-world Results**: 49-minute video transcribed in 103 seconds with MLX GPU (vs 3000+ seconds CPU-only)

**Backend Selection**:
```bash
# Check available backends
screenscribe --list-backends

# Example output on Apple Silicon:
# 🔍 Available Audio Backends:
#   ✅ mlx: gpu (float16)         # Apple Silicon GPU acceleration  
#   ✅ faster-whisper: cpu (int8)  # Universal CPU fallback

# Force specific backend (optional)
screenscribe video.mp4 --whisper-backend mlx           # Apple Silicon GPU
screenscribe video.mp4 --whisper-backend faster-whisper # Universal CPU
```

**Performance Tips**:
- Use `--whisper-model tiny` for fastest processing
- Use `--whisper-model large` for best accuracy  
- MLX backend provides best performance on Apple Silicon
- System automatically copies network files locally for better performance

## 🎯 Usage

### Basic Usage

```bash
# Process a local video
screenscribe video.mp4

# Process a YouTube video
screenscribe "https://youtube.com/watch?v=..."

# Specify output directory and format
screenscribe video.mp4 --output notes/ --format html
```

### Common Options

- `--output` - Output directory (default: ./screenscribe_output)
- `--format` - Output format: markdown or html (default: markdown)
- `--whisper-model` - Model size: tiny, base, small, medium, large (default: medium)
- `--whisper-backend` - Transcription backend: auto, faster-whisper, mlx (default: auto)
- `--list-backends` - Show available backends and exit
- `--verbose` - Show detailed progress

### Examples

```bash
# Fast processing
screenscribe demo.mp4 --whisper-model tiny

# Apple Silicon GPU acceleration (M1/M2/M3 Macs)
screenscribe tutorial.mp4 --whisper-backend mlx

# High quality with automatic backend selection
screenscribe tutorial.mp4 --whisper-model large --format html

# Custom output location
screenscribe lecture.mp4 --output ./my-notes/

# Show available transcription backends
screenscribe --list-backends
```

**See `screenscribe --help` for all options.**

## ⚡ Apple Silicon Acceleration

**Get 2-8x faster transcription on M1/M2/M3 Macs:**

### Installation
```bash
# Install with Apple Silicon GPU support
cd /path/to/screenscribe/
uv tool install --editable "./[apple]"
```

### Performance Benefits
- **M1/M2/M3 GPU acceleration** via MLX backend
- **2-8x faster** transcription compared to CPU-only processing
- **Automatic detection** - uses GPU when available, falls back to optimized CPU
- **Zero configuration** - works out of the box

### Usage
```bash
# Automatic backend selection (recommended)
screenscribe video.mp4

# Force Apple Silicon GPU backend
screenscribe video.mp4 --whisper-backend mlx

# Show available backends on your system
screenscribe --list-backends
```

### Performance Comparison
| Hardware | Backend | 49min Video | Speedup |
|----------|---------|-------------|---------|
| M3 Ultra | CPU only | ~3000s (50min) | 1x |
| M3 Ultra | MLX (GPU) | ~103s (1.7min) | **29x** |
| M1 Pro | CPU only | ~4000s (67min) | 1x |
| M1 Pro | MLX (GPU) | ~200s (3.3min) | **20x** |

**Note**: MLX backend requires `pip install "screenscribe[apple]"` and is only available on Apple Silicon Macs.

## ⚙️ Configuration & Advanced Features

### Global Configuration System

screenscribe now features a comprehensive configuration system with global settings:

```bash
# Initialize configuration (creates ~/.config/screenscribe/)
screenscribe config init

# Show current configuration
screenscribe config show

# Validate configuration
screenscribe config validate
```

The global configuration includes:
- **API endpoints and keys** - Configure multiple LLM providers
- **Global prompts directory** - Customize AI analysis prompts globally
- **Processing defaults** - Set preferred sampling modes, models, and backends
- **YouTube settings** - Control transcript extraction behavior
- **Update settings** - Auto-update preferences

### Enhanced YouTube Support

Extract transcripts directly from YouTube when available, with Whisper fallback:

```bash
# Use YouTube's built-in transcripts (default behavior)
screenscribe "https://youtube.com/watch?v=..." --use-youtube-transcripts

# Force Whisper transcription (skip YouTube transcripts)  
screenscribe "https://youtube.com/watch?v=..." --no-youtube-transcripts

# Use external transcript file with any video
screenscribe video.mp4 --transcript-file transcript.srt
screenscribe "https://youtube.com/watch?v=..." --transcript-file custom.json
```

**Supported transcript formats:**
- **JSON** - screenscribe native format with timing
- **SRT** - Standard subtitle format 
- **VTT** - WebVTT subtitle format
- **Plain text** - Raw text without timing

### Self-Update System

Keep screenscribe up-to-date automatically:

```bash
# Check for updates
screenscribe update check

# Install latest stable release
screenscribe update install

# Install latest development version
screenscribe update install --dev

# Manual update (development users)
git pull && uv tool install --editable './[apple]' --force
```

### Global Prompts Directory

Customize AI analysis globally at `~/.config/screenscribe/prompts/`:

```bash
# Initialize creates default prompts
screenscribe config init

# Use global prompts (default)
screenscribe video.mp4

# Use custom prompts directory
screenscribe video.mp4 --prompts-dir ./my-custom-prompts/

# Edit global prompts
code ~/.config/screenscribe/prompts/synthesis.md
```

### Multi-Command CLI

screenscribe now features a professional multi-command structure:

- `screenscribe [video]` - Process video (default command)
- `screenscribe config` - Configuration management
- `screenscribe update` - Update management
- `screenscribe --list-backends` - List available backends

## 📋 Output

screenscribe generates:
- **notes.md** or **notes.html** - Structured notes with transcripts and frame analysis
- **transcript.json** - Raw transcription data  
- **frames/** - Extracted video frames
- **thumbnails/** - Resized images for embedding

## 🎯 Customizing AI Analysis

screenscribe provides powerful prompt customization through the global configuration system:

```bash
# Initialize global prompts directory (first time only)
screenscribe config init

# Edit global prompts (applies to all processing)
code ~/.config/screenscribe/prompts/synthesis.md
code ~/.config/screenscribe/prompts/trading.md  # Specialized for financial content

# Use project-specific prompts
screenscribe tutorial.mp4 --prompts-dir ./my-prompts/

# Show current configuration including prompts directory
screenscribe config show
```

**Global vs Local Prompts:**
- **Global prompts** (`~/.config/screenscribe/prompts/`) - Applied to all videos automatically
- **Local prompts** (`--prompts-dir`) - Override global prompts for specific projects
- **Built-in prompts** - Default fallback if no custom prompts found

## 📚 Documentation

**📖 Complete User Manual:** **[USER_MANUAL.md](docs/USER_MANUAL.md)** - Everything you need to know about using screenscribe

**Additional User Guides:**
- **[Installation Guide](docs/user/installation.md)** - Platform-specific installation  
- **[Troubleshooting](docs/user/troubleshooting.md)** - Common issues and solutions
- **[Real-World Examples](docs/examples/real-world-examples.md)** - See screenscribe in action

**👨‍💻 For Developers:**
- **[Development Guide](docs/DEVELOPMENT.md)** - Complete developer documentation, architecture, and contribution guidelines

## 🎯 Perfect For

- 📖 Educational content (lectures, tutorials) 
- 💼 Business meetings and presentations
- 👨‍💻 Technical training and code walkthroughs
- 📊 Conference talks and webinars
- 🎥 Content creation and analysis

## 🛠️ Troubleshooting

**Installation Issues:**
- **"screenscribe not found in package registry"** → Use `uv tool install --editable .` for development/source code
- **"command not found: screenscribe"** → Add `~/.local/bin` to your PATH
- **FFmpeg not found** → Install FFmpeg for your OS
- **MLX backend not available** → Use `uv tool install --editable './[apple]' --force` (note the `[apple]` part)

**Runtime Issues:**
- **Out of memory** → Use `--whisper-model tiny` or `--whisper-backend faster-whisper`
- **API errors** → Check your `OPENAI_API_KEY`
- **No audio** → Ensure video has audio track
- **Slow transcription** → Check `screenscribe --list-backends` to verify MLX is available on Apple Silicon

**Performance Tips:**
- **Apple Silicon users**: CRITICAL - Install with `"./[apple]"` for 20-30x faster GPU transcription via MLX backend
- **Verify GPU acceleration**: Use `screenscribe --list-backends` to confirm MLX shows as `✅ mlx: gpu (float16)`
- **Backend auto-selection**: MLX automatically chosen on Apple Silicon, faster-whisper on other platforms
- **Network storage**: Files on NAS/network drives are automatically copied locally for 10x better performance
- **Model selection**: Use `tiny` for speed, `large` for accuracy - MLX handles all sizes efficiently
- **Interruption**: Single ctrl+c for graceful shutdown, double ctrl+c for immediate exit
- **Expected performance**: 49-minute video processes in ~2 minutes on Apple Silicon GPU (vs ~50 minutes CPU-only)

**Need help?** See [Troubleshooting Guide](docs/user/troubleshooting.md)

## 🧵 Fabric Integration

screenscribe includes comprehensive [Fabric](https://github.com/danielmiessler/fabric) integration for advanced AI-powered video analysis workflows:

### Quick Fabric Setup
```bash
# Install Fabric (if not already installed)
go install github.com/danielmiessler/fabric@latest

# Build screenscribe Fabric extension
cd fabric-extension && make build && make install

# Copy patterns to Fabric
cp -r patterns/* ~/.config/fabric/patterns/
```

### Fabric Usage Examples
```bash
# Basic video analysis with Fabric
video_analyze tutorial.mp4 | fabric -p analyze_video_content

# Trading-specific analysis
video_analyze trading_webinar.mp4 | fabric -p analyze_trading_video

# Extract code from programming tutorials
video_analyze coding_tutorial.mp4 | fabric -p extract_code_from_video

# Chain multiple Fabric patterns
video_analyze presentation.mp4 | \
  fabric -p analyze_video_content | \
  fabric -p extract_key_points | \
  fabric -p create_blog_post
```

### Available Fabric Patterns
- **General**: `analyze_video_content`, `extract_code_from_video`
- **Trading**: `analyze_trading_video`, `extract_technical_analysis`, `extract_trading_strategy`, `analyze_market_commentary`

**Learn more**: See [Fabric Extension Documentation](./fabric-extension/README.md)

Special thanks to [Daniel Miessler](https://github.com/danielmiessler) and the [Fabric project](https://github.com/danielmiessler/fabric) for creating the powerful AI pattern framework that enables advanced video analysis workflows.

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Support & Contributing

- **Issues**: [GitHub Issues](https://github.com/grimmolf/screenscribe/issues)
- **Contributing**: See [Development Guide](docs/DEVELOPMENT.md)
- **Discussions**: [GitHub Discussions](https://github.com/grimmolf/screenscribe/discussions)
