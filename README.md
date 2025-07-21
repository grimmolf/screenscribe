# screenscribe

<div align="center">

🎬 **Transform videos into structured, searchable notes with AI-powered analysis**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

</div>

**screenscribe** is a CLI tool that processes videos and screen recordings to extract both audio transcripts and visual context, synthesizing them into comprehensive, structured notes. Perfect for technical tutorials, presentations, lectures, and meetings.

**Key Features:**
- 🎤 High-quality transcription with faster-whisper (2-5x faster than OpenAI Whisper)
- 👁️ AI-powered visual analysis with GPT-4 Vision  
- 📝 Output in Markdown or HTML format
- 📺 Support for YouTube videos and local files
- 🎯 Customizable AI prompts for different content types

## 🚀 Quick Start

**For development/source code users:**

```bash
# 1. Clone or download this repository
cd /path/to/screenscribe/

# 2. Install from source  
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install --editable .

# 3. Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# 4. Process your first video
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

# 4. Install FFmpeg (required)
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

# Reinstall with latest code
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
- `--verbose` - Show detailed progress

### Examples

```bash
# Fast processing
screenscribe demo.mp4 --whisper-model tiny

# High quality
screenscribe tutorial.mp4 --whisper-model large --format html

# Custom output location
screenscribe lecture.mp4 --output ./my-notes/
```

**See `screenscribe --help` for all options.**

## 📋 Output

screenscribe generates:
- **notes.md** or **notes.html** - Structured notes with transcripts and frame analysis
- **transcript.json** - Raw transcription data  
- **frames/** - Extracted video frames
- **thumbnails/** - Resized images for embedding

## 🎯 Customizing AI Analysis

You can customize how screenscribe analyzes your content by editing prompt templates:

```bash
# Use custom prompts for technical content
screenscribe tutorial.mp4 --prompts-dir ./my-prompts/

# Prompts are stored as editable markdown files
# See prompts/ directory for examples
```

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

**Runtime Issues:**
- **Out of memory** → Use `--whisper-model tiny` 
- **API errors** → Check your `OPENAI_API_KEY`
- **No audio** → Ensure video has audio track

**Performance Tips:**
- Use smaller Whisper models (`tiny`, `base`) for speed
- Processing typically takes 1-2x video duration
- GPU acceleration helps significantly

**Need help?** See [Troubleshooting Guide](docs/user/troubleshooting.md)

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Support & Contributing

- **Issues**: [GitHub Issues](https://github.com/grimmolf/screenscribe/issues)
- **Contributing**: See [Development Guide](docs/DEVELOPMENT.md)
- **Discussions**: [GitHub Discussions](https://github.com/grimmolf/screenscribe/discussions)
