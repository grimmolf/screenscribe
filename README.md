# screenscribe

<div align="center">

🎬 **Transform videos into structured, searchable notes with AI-powered analysis**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

</div>

screenscribe is a powerful CLI tool that processes videos and screen recordings to extract both audio transcripts and visual context, synthesizing them into comprehensive, structured notes. Perfect for technical tutorials, presentations, lectures, and meetings.

## 🚀 Quick Start

```bash
# One-command install
curl -LsSf https://raw.githubusercontent.com/screenscribe/screenscribe/main/scripts/install.sh | bash

# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Process your first video
screenscribe video.mp4
```

## ✨ Key Features

- **🎤 High-Quality Transcription**: Uses OpenAI Whisper for accurate speech-to-text conversion
- **👁️ Intelligent Frame Analysis**: Smart scene detection or interval-based sampling
- **🤖 AI-Powered Synthesis**: GPT-4 Vision combines audio and visual context for comprehensive insights
- **📝 Multiple Output Formats**: Generate Markdown or HTML with embedded thumbnails
- **📺 YouTube Support**: Process YouTube videos directly from URLs
- **🎯 Customizable Prompts**: Tailor AI analysis for your specific content type
- **⚡ High Performance**: Async processing with GPU acceleration support
- **🔧 Easy Installation**: Single-command install with automatic dependency management

## Quick Installation

### One-Command Install

```bash
curl -LsSf https://raw.githubusercontent.com/screenscribe/screenscribe/main/scripts/install.sh | bash
```

This script will:
- Install `uv` (if not already installed)
- Install FFmpeg for your OS
- Install screenscribe as a global command

### Manual Installation

If you prefer manual installation:

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install screenscribe
uv tool install screenscribe

# 3. Install FFmpeg
# macOS
brew install ffmpeg

# Ubuntu/Debian  
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

### Setup API Keys

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY='your_openai_api_key'
export ANTHROPIC_API_KEY='your_anthropic_api_key'  # optional fallback

# Add to your shell profile (.bashrc, .zshrc, etc.) to persist
echo 'export OPENAI_API_KEY="your_openai_api_key"' >> ~/.bashrc
```

## Usage

### Basic Usage

```bash
# Process a local video file
screenscribe video.mp4 --output notes/

# Process a YouTube video  
screenscribe "https://youtube.com/watch?v=..." --output notes/

# With custom options
screenscribe video.mp4 \
    --output notes/ \
    --format html \
    --whisper-model large \
    --sampling-mode interval \
    --interval 10
```

### Options

- `--output, -o`: Output directory (default: ./screenscribe_output)
- `--format, -f`: Output format - markdown or html (default: markdown)
- `--whisper-model`: Whisper model size - tiny, base, small, medium, large (default: medium)
- `--sampling-mode`: Frame sampling - scene or interval (default: scene)
- `--interval`: Interval for interval sampling in seconds (default: 5.0)
- `--scene-threshold`: Scene detection threshold (default: 0.3)
- `--llm`: LLM provider - openai, anthropic (default: openai)
- `--no-fallback`: Disable LLM fallbacks
- `--prompts-dir`: Custom directory for prompt templates
- `--verbose, -v`: Verbose output

### Examples

```bash
# Quick processing with tiny model
screenscribe demo.mp4 --whisper-model tiny --output quick/

# High-quality processing
screenscribe tutorial.mp4 --whisper-model large --format html

# Custom frame sampling
screenscribe presentation.mp4 --sampling-mode interval --interval 30
```

## Output

screenscribe generates:

- **notes.md** or **notes.html**: Main structured notes
- **transcript.json**: Raw transcription data
- **frames/**: Extracted video frames
- **thumbnails/**: Resized thumbnails for embedding
- **processing_result.json**: Complete processing metadata

## Customizing Prompts

screenscribe uses customizable prompt templates for LLM analysis. You can edit these to improve results for your specific content type.

### Default Prompts
Prompts are stored in the `prompts/` directory as markdown files:
- `synthesis.md`: Main prompt for analyzing frames with transcripts

### Custom Prompts
Create custom prompts in three ways:

1. **Edit default prompts**: Modify files in the `prompts/` directory
2. **Custom directory**: Use `--prompts-dir ./my-prompts/` 
3. **Environment variable**: Set `SCREENSCRIBE_PROMPTS_DIR=/path/to/prompts`

### Example: Technical Tutorial Prompt
```bash
# Copy and customize the default prompt
cp prompts/synthesis.md my-prompts/synthesis.md
# Edit my-prompts/synthesis.md for tutorial-specific analysis
screenscribe tutorial.mp4 --prompts-dir my-prompts/
```

See `prompts/README.md` for detailed prompt customization guide.

## 📚 Documentation

### User Guides
- **[Installation Guide](docs/user/installation.md)** - Complete installation instructions for all platforms
- **[Usage Guide](docs/user/usage.md)** - Comprehensive usage examples and tutorials  
- **[Prompt Customization](docs/user/prompt-customization.md)** - Customize AI analysis for your content
- **[Troubleshooting](docs/user/troubleshooting.md)** - Common issues and solutions

### Examples
- **[Real-World Examples](docs/examples/real-world-examples.md)** - See screenscribe in action
- **Performance benchmarks** and optimization tips
- **Integration examples** with Obsidian, Notion, and Jupyter

### For Developers
- **[Development Log](docs/CLAUDE_DEVELOPMENT_LOG.md)** - Project development history
- **[API Reference](docs/api-reference.md)** - Module documentation and architecture
- **[Contributing Guide](#contributing)** - How to contribute to screenscribe

## 🎯 Perfect For

- **📖 Educational Content**: Convert lectures and tutorials into searchable study notes
- **💼 Business Meetings**: Generate comprehensive meeting summaries with action items  
- **👨‍💻 Technical Training**: Extract code examples and concepts from programming videos
- **📊 Presentations**: Turn slide-based content into structured documentation
- **🎥 Content Creation**: Analyze your own videos for improved content planning

## Development

### Development Setup

```bash
# Clone the repository
git clone https://github.com/screenscribe/screenscribe.git
cd screenscribe

# Install development dependencies with uv
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/screenscribe --cov-report=term-missing

# Lint and format code
uv run ruff check src/ tests/ --fix
uv run black src/ tests/

# Install in development mode
uv pip install -e .
```

### Project Structure

```
screenscribe/
├── src/screenscribe/       # Main package
│   ├── cli.py             # CLI interface
│   ├── models.py          # Data models
│   ├── audio.py           # Audio processing
│   ├── video.py           # Video processing
│   ├── align.py           # Temporal alignment
│   ├── synthesis.py       # LLM synthesis
│   ├── output.py          # Output generation
│   ├── utils.py           # Utilities
│   └── config.py          # Configuration
├── tests/                 # Test suite
├── scripts/               # Installation scripts
└── docs/                  # Documentation
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg using your system package manager
2. **CUDA out of memory**: Use `--whisper-model tiny` or ensure CPU fallback
3. **API rate limits**: Reduce concurrency or use `--no-fallback`
4. **No audio stream**: Ensure video file has audio track

### Performance Tips

- Use `tiny` or `base` Whisper models for faster processing
- Scene detection is more efficient than interval sampling for most content
- GPU acceleration speeds up Whisper significantly
- Processing time is typically 1-2x video duration

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## Support

- Documentation: See [docs/](docs/) directory
- Issues: GitHub Issues
- Discussions: GitHub Discussions