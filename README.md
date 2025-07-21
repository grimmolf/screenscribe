# screenscribe

<div align="center">

🎬 **Transform videos into structured, searchable notes with AI-powered analysis**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

</div>

**screenscribe** is a CLI tool that processes videos and screen recordings to extract both audio transcripts and visual context, synthesizing them into comprehensive, structured notes. Perfect for technical tutorials, presentations, lectures, and meetings.

**Key Features:**
- 🎤 High-quality transcription with OpenAI Whisper
- 👁️ AI-powered visual analysis with GPT-4 Vision  
- 📝 Output in Markdown or HTML format
- 📺 Support for YouTube videos and local files
- 🎯 Customizable AI prompts for different content types

## 🚀 Quick Start

```bash
# One-command install
curl -LsSf https://raw.githubusercontent.com/screenscribe/screenscribe/main/scripts/install.sh | bash

# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Process your first video
screenscribe video.mp4
```

## 📦 Installation

### Install

```bash
# One-command install (recommended)
curl -LsSf https://raw.githubusercontent.com/screenscribe/screenscribe/main/scripts/install.sh | bash
```

**Or manually:**
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install screenscribe
uv tool install screenscribe

# Install FFmpeg (required)
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg  
# Fedora: sudo dnf install ffmpeg
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

**Common Issues:**
- **FFmpeg not found** → Install FFmpeg for your OS
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

- **Issues**: [GitHub Issues](https://github.com/screenscribe/screenscribe/issues)
- **Contributing**: See [Development Guide](docs/DEVELOPMENT.md)
- **Discussions**: [GitHub Discussions](https://github.com/screenscribe/screenscribe/discussions)