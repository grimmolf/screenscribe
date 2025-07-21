#!/bin/bash

# FFmpeg installation script for screenscribe
# Supports macOS and Fedora Linux

set -e

echo "🎬 Installing FFmpeg for screenscribe..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Detected macOS"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install FFmpeg via Homebrew
    echo "🍺 Installing FFmpeg via Homebrew..."
    brew install ffmpeg
    
elif [[ -f /etc/fedora-release ]]; then
    echo "🎩 Detected Fedora Linux"
    
    # Enable RPM Fusion free repository (required for FFmpeg)
    echo "📦 Enabling RPM Fusion repository..."
    sudo dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm || true
    
    # Install FFmpeg
    echo "🎬 Installing FFmpeg via DNF..."
    sudo dnf install -y ffmpeg ffmpeg-devel
    
elif [[ -f /etc/debian_version ]]; then
    echo "🐧 Detected Debian/Ubuntu"
    
    # Update package list
    echo "📦 Updating package list..."
    sudo apt update
    
    # Install FFmpeg
    echo "🎬 Installing FFmpeg via APT..."
    sudo apt install -y ffmpeg
    
elif [[ -f /etc/arch-release ]]; then
    echo "🏛️ Detected Arch Linux"
    
    # Install FFmpeg
    echo "🎬 Installing FFmpeg via Pacman..."
    sudo pacman -S --noconfirm ffmpeg
    
else
    echo "❌ Unsupported operating system"
    echo "Please install FFmpeg manually:"
    echo "  - macOS: brew install ffmpeg"
    echo "  - Fedora: sudo dnf install ffmpeg"
    echo "  - Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  - Arch: sudo pacman -S ffmpeg"
    echo "  - Windows: Download from https://ffmpeg.org/download.html"
    exit 1
fi

# Verify installation
echo "🔍 Verifying FFmpeg installation..."
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version | head -n 1)
    echo "✅ FFmpeg installed successfully: $ffmpeg_version"
else
    echo "❌ FFmpeg installation failed"
    exit 1
fi

# Check for ffprobe (should be included with FFmpeg)
if command -v ffprobe &> /dev/null; then
    echo "✅ FFprobe is available"
else
    echo "⚠️  FFprobe not found (usually included with FFmpeg)"
fi

echo "🎉 FFmpeg installation complete!"
echo ""
echo "Next steps:"
echo "1. Set up your API keys in .env file"
echo "2. Run: poetry install"
echo "3. Test with: python -m screenscribe --help"