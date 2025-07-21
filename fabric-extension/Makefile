# Makefile for Screenscribe Fabric Extension

.PHONY: build install clean test help

# Default target
help:
	@echo "Screenscribe Fabric Extension Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  build     - Build all Go helper tools"
	@echo "  install   - Install tools to local bin directory"
	@echo "  install-system - Install tools to system-wide bin directory (requires sudo)"
	@echo "  clean     - Remove build artifacts"
	@echo "  test      - Run basic functionality tests"
	@echo "  deps      - Install dependencies"
	@echo "  help      - Show this help message"
	@echo ""

# Build all Go tools
build:
	@echo "Building Go helper tools..."
	@mkdir -p bin
	go mod download
	go build -o bin/whisper_transcribe ./cmd/whisper_transcribe
	go build -o bin/video_frames ./cmd/video_frames
	go build -o bin/video_analyze ./cmd/video_analyze
	@echo "Build complete. Binaries in ./bin/"

# Install to user's local bin directory
install: build
	@echo "Installing to ~/.local/bin/..."
	@mkdir -p ~/.local/bin
	cp bin/* ~/.local/bin/
	cp scripts/whisper_wrapper.py ~/.local/bin/
	cp scripts/extract_frames.sh ~/.local/bin/
	chmod +x ~/.local/bin/whisper_wrapper.py ~/.local/bin/extract_frames.sh
	@echo "Installation complete. Make sure ~/.local/bin is in your PATH"
	@echo "Add this to your shell profile if needed:"
	@echo "  export PATH=\"\$$HOME/.local/bin:\$$PATH\""

# Install to system-wide bin directory
install-system: build
	@echo "Installing to /usr/local/bin/ (requires sudo)..."
	sudo cp bin/* /usr/local/bin/
	sudo cp scripts/whisper_wrapper.py /usr/local/bin/
	sudo cp scripts/extract_frames.sh /usr/local/bin/
	sudo chmod +x /usr/local/bin/whisper_wrapper.py /usr/local/bin/extract_frames.sh
	@echo "System-wide installation complete."

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf bin/
	go mod tidy
	@echo "Clean complete."

# Install dependencies
deps:
	@echo "Installing dependencies..."
	@echo "Go dependencies:"
	go mod download
	@echo ""
	@echo "Python dependencies (you may need to install these manually):"
	@echo "  pip3 install faster-whisper"
	@echo "  pip3 install mlx-whisper  # Apple Silicon only"
	@echo "  pip3 install openai-whisper  # fallback"
	@echo ""
	@echo "System dependencies (install with your package manager):"
	@echo "  - ffmpeg (video processing)"
	@echo "  - jq (JSON processing)"
	@echo "  - python3"

# Basic functionality tests
test: build
	@echo "Running basic functionality tests..."
	@echo ""
	@echo "Testing Go tool compilation..."
	@./bin/whisper_transcribe --help >/dev/null && echo "✅ whisper_transcribe builds and runs" || echo "❌ whisper_transcribe failed"
	@./bin/video_frames --help >/dev/null && echo "✅ video_frames builds and runs" || echo "❌ video_frames failed"
	@./bin/video_analyze --help >/dev/null && echo "✅ video_analyze builds and runs" || echo "❌ video_analyze failed"
	@echo ""
	@echo "Testing script dependencies..."
	@python3 scripts/whisper_wrapper.py --help >/dev/null 2>&1 && echo "✅ whisper_wrapper.py runs" || echo "❌ whisper_wrapper.py failed (check Python deps)"
	@bash scripts/extract_frames.sh --help >/dev/null 2>&1 && echo "✅ extract_frames.sh runs" || echo "❌ extract_frames.sh failed"
	@echo ""
	@echo "Testing system dependencies..."
	@command -v ffmpeg >/dev/null && echo "✅ ffmpeg found" || echo "❌ ffmpeg not found"
	@command -v jq >/dev/null && echo "✅ jq found" || echo "❌ jq not found"  
	@command -v python3 >/dev/null && echo "✅ python3 found" || echo "❌ python3 not found"
	@echo ""
	@echo "Testing Python modules..."
	@python3 -c "import json; print('✅ json module available')" 2>/dev/null || echo "❌ json module not available"
	@python3 -c "import faster_whisper; print('✅ faster-whisper available')" 2>/dev/null || echo "ℹ️  faster-whisper not installed (pip3 install faster-whisper)"
	@python3 -c "import mlx_whisper; print('✅ mlx-whisper available')" 2>/dev/null || echo "ℹ️  mlx-whisper not installed (Apple Silicon only)"
	@echo ""
	@echo "Pattern files:"
	@ls -la patterns/*/system.md 2>/dev/null && echo "✅ Fabric patterns found" || echo "❌ No patterns found"

# Development target - runs tests after each build
dev: clean build test

# Build release version with optimizations
release:
	@echo "Building release version..."
	@mkdir -p bin
	go mod download
	CGO_ENABLED=0 go build -ldflags "-s -w" -o bin/whisper_transcribe ./cmd/whisper_transcribe
	CGO_ENABLED=0 go build -ldflags "-s -w" -o bin/video_frames ./cmd/video_frames
	CGO_ENABLED=0 go build -ldflags "-s -w" -o bin/video_analyze ./cmd/video_analyze
	@echo "Release build complete."