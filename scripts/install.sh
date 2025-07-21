#!/bin/bash

# screenscribe installation script
# Installs screenscribe CLI with a single command using uv

set -e

echo "🎬 Installing screenscribe CLI..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_status "uv not found. Installing uv..."
    
    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Source the shell profile to make uv available
    if [[ -f "$HOME/.cargo/env" ]]; then
        source "$HOME/.cargo/env"
    fi
    
    # Check if uv is now available
    if ! command -v uv &> /dev/null; then
        print_error "Failed to install uv. Please install manually:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    print_success "uv installed successfully"
else
    print_status "uv found: $(uv --version)"
fi

# Install FFmpeg
print_status "Checking FFmpeg installation..."

if ! command -v ffmpeg &> /dev/null; then
    print_status "FFmpeg not found. Installing..."
    
    # Detect OS and install FFmpeg
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            print_error "Homebrew not found. Please install FFmpeg manually:"
            echo "  brew install ffmpeg"
            exit 1
        fi
    elif [[ -f /etc/fedora-release ]]; then
        sudo dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm || true
        sudo dnf install -y ffmpeg
    elif [[ -f /etc/debian_version ]]; then
        sudo apt update && sudo apt install -y ffmpeg
    elif [[ -f /etc/arch-release ]]; then
        sudo pacman -S --noconfirm ffmpeg
    else
        print_warning "Unknown OS. Please install FFmpeg manually:"
        echo "  - macOS: brew install ffmpeg"
        echo "  - Ubuntu/Debian: sudo apt install ffmpeg"
        echo "  - Fedora: sudo dnf install ffmpeg"
        echo "  - Arch: sudo pacman -S ffmpeg"
    fi
    
    # Verify FFmpeg installation
    if ! command -v ffmpeg &> /dev/null; then
        print_error "FFmpeg installation failed. Please install manually."
        exit 1
    fi
    
    print_success "FFmpeg installed successfully"
else
    print_status "FFmpeg found: $(ffmpeg -version | head -n 1 | cut -d' ' -f3)"
fi

# Install screenscribe using uv
print_status "Installing screenscribe CLI..."

# Create a tools environment and install screenscribe
uv tool install screenscribe

# Verify installation
if command -v screenscribe &> /dev/null; then
    print_success "screenscribe installed successfully!"
    echo ""
    echo "🎉 Installation complete!"
    echo ""
    echo "Next steps:"
    echo "1. Set up your API keys:"
    echo "   export OPENAI_API_KEY='your_openai_api_key'"
    echo "   export ANTHROPIC_API_KEY='your_anthropic_api_key'  # optional"
    echo ""
    echo "2. Test the installation:"
    echo "   screenscribe --help"
    echo ""
    echo "3. Process your first video:"
    echo "   screenscribe video.mp4 --output notes/"
    echo ""
    echo "📚 Documentation: https://github.com/screenscribe/screenscribe#readme"
else
    print_error "Installation failed. screenscribe command not found."
    print_status "Try adding uv's bin directory to your PATH:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "  # Add this to your shell profile (.bashrc, .zshrc, etc.)"
    exit 1
fi