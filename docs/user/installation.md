# Installation Guide

This guide covers all methods to install screenscribe on your system.

> 📖 **For comprehensive usage guidance**, see the **[User Manual](../USER_MANUAL.md)** which includes installation, usage, prompt customization, optimization, and troubleshooting.

## Quick Installation (Recommended)

### One-Command Install

The fastest way to get screenscribe running:

```bash
curl -LsSf https://raw.githubusercontent.com/screenscribe/screenscribe/main/scripts/install.sh | bash
```

This script will:
- ✅ Install `uv` (Python package manager) if needed
- ✅ Install FFmpeg for your operating system
- ✅ Install screenscribe as a global `screenscribe` command
- ✅ Verify the installation

After installation, you can run `screenscribe --help` to verify it's working.

## Manual Installation

If you prefer to install components manually:

### Step 1: Install uv

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload your shell or run:
source ~/.bashrc  # or ~/.zshrc
```

### Step 2: Install screenscribe

```bash
# Standard installation
uv tool install screenscribe

# Apple Silicon optimization (M1/M2/M3 Macs) - 20-30x faster transcription with GPU
uv tool install "screenscribe[apple]"
```

### Step 3: Install FFmpeg

FFmpeg is required for video processing:

**macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Fedora:**
```bash
sudo dnf install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
sudo dnf install ffmpeg
```

**Arch Linux:**
```bash
sudo pacman -S ffmpeg
```

**Windows:**
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add to PATH.

## Alternative Installation Methods

### From Source (Development)

If you want to contribute or need the latest features:

```bash
# Clone the repository
git clone https://github.com/screenscribe/screenscribe.git
cd screenscribe

# Install development dependencies
uv sync --dev

# Install in development mode
uv pip install -e .
```

### Using pipx

If you prefer pipx over uv:

```bash
pipx install screenscribe
```

Note: You'll still need to install FFmpeg separately.

## Setup API Keys

screenscribe requires API access to LLM providers for content synthesis:

### OpenAI (Recommended)

1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Set the environment variable:

```bash
export OPENAI_API_KEY="sk-your-api-key-here"

# Add to your shell profile for persistence:
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
```

### Anthropic (Optional Fallback)

For additional reliability, you can also set up Anthropic Claude:

```bash
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
```

## Verification

Test your installation:

```bash
# Check that screenscribe is installed
screenscribe --help

# Verify FFmpeg is working
ffmpeg -version

# Check available audio backends
screenscribe --list-backends test.mp4

# Example output on Apple Silicon:
# 🔍 Available Audio Backends:
#   ✅ mlx: gpu (float16)         # GPU acceleration available
#   ✅ faster-whisper: cpu (int8)  # CPU fallback
```

## Troubleshooting

### Common Issues

**Command not found: screenscribe**
- Ensure `uv`'s bin directory is in your PATH: `export PATH="$HOME/.local/bin:$PATH"`
- Restart your terminal or run `source ~/.bashrc`

**FFmpeg not found**
- Install FFmpeg using your system's package manager
- Verify with `ffmpeg -version`

**API key errors**
- Ensure your API keys are set correctly
- Check that your OpenAI/Anthropic account has sufficient credits

**Permission errors**
- On Linux/macOS, you might need to make scripts executable
- Try running with `--verbose` flag for more details

### System Requirements

- **Python**: 3.9 or higher
- **Memory**: At least 4GB RAM (8GB recommended for large videos)
- **Storage**: 2GB free space for model downloads
- **Network**: Internet connection for API calls and model downloads

### Platform-Specific Notes

**macOS:**
- Homebrew is required for automatic FFmpeg installation
- CRITICAL: Always install with `[apple]` dependencies for GPU acceleration on M1/M2/M3 Macs
- MLX backend provides 20-30x performance improvement over CPU-only processing

**Linux:**
- Most distributions are supported
- Some older distributions may need manual FFmpeg compilation

**Windows:**
- Windows 10/11 supported
- WSL recommended for the best experience
- Manual FFmpeg installation required

## Next Steps

Once installed, check out:
- **[📖 Complete User Manual](../USER_MANUAL.md)** - Everything you need to know about using screenscribe
- **[Usage Guide](usage.md)** - Basic commands and examples
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Real-World Examples](../examples/real-world-examples.md)** - See screenscribe in action