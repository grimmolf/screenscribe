# Makefile for Screenscribe Fabric Extension

.PHONY: build install clean test help uninstall build-all release-binaries

# Default target
help:
	@echo "Screenscribe Fabric Extension Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  build     - Build all Go helper tools for current platform"
	@echo "  build-all - Build for all supported platforms (macOS, Linux)"
	@echo "  install   - Install tools to local bin directory"
	@echo "  install-system - Install tools to system-wide bin directory (requires sudo)"
	@echo "  uninstall - Remove tools and patterns (uses video_analyze --uninstall)"
	@echo "  release-binaries - Create release binaries for distribution"
	@echo "  clean     - Remove build artifacts"
	@echo "  test      - Run basic functionality tests"
	@echo "  deps      - Install dependencies"
	@echo "  help      - Show this help message"
	@echo ""

# Version information
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
GIT_COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_DATE ?= $(shell date -u '+%Y-%m-%d_%H:%M:%S')

# Build flags
LDFLAGS = -ldflags "-s -w -X main.Version=$(VERSION) -X main.GitCommit=$(GIT_COMMIT) -X main.BuildDate=$(BUILD_DATE)"

# Build unified scribe tool for current platform
build:
	@echo "Building scribe unified CLI..."
	@echo "Version: $(VERSION)"
	@echo "Git Commit: $(GIT_COMMIT)" 
	@echo "Build Date: $(BUILD_DATE)"
	@mkdir -p bin
	go mod download
	go build $(LDFLAGS) -o bin/scribe ./cmd/scribe
	@echo "Build complete. Binary in ./bin/"

# Build for all supported platforms
build-all:
	@echo "Building scribe for all supported platforms..."
	@echo "Version: $(VERSION)"
	@echo "Git Commit: $(GIT_COMMIT)"
	@echo "Build Date: $(BUILD_DATE)"
	@mkdir -p dist/{macos-amd64,macos-arm64,linux-amd64,linux-arm64}
	go mod download
	
	@echo "Building for macOS AMD64..."
	GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o dist/macos-amd64/scribe ./cmd/scribe
	
	@echo "Building for macOS ARM64 (Apple Silicon)..."
	GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o dist/macos-arm64/scribe ./cmd/scribe
	
	@echo "Building for Linux AMD64 (Fedora/Ubuntu)..."
	GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o dist/linux-amd64/scribe ./cmd/scribe
	
	@echo "Building for Linux ARM64..."
	GOOS=linux GOARCH=arm64 go build $(LDFLAGS) -o dist/linux-arm64/scribe ./cmd/scribe
	
	@echo "Cross-compilation complete. Binaries in ./dist/"

# Install to user's local bin directory
install: build
	@echo "Installing to ~/.local/bin/..."
	@mkdir -p ~/.local/bin
	cp bin/scribe ~/.local/bin/
	cp scripts/whisper_wrapper.py ~/.local/bin/
	cp scripts/extract_frames.sh ~/.local/bin/
	cp scripts/youtube_helper.py ~/.local/bin/
	chmod +x ~/.local/bin/whisper_wrapper.py ~/.local/bin/extract_frames.sh ~/.local/bin/youtube_helper.py
	@echo "Installation complete. Make sure ~/.local/bin is in your PATH"
	@echo "Add this to your shell profile if needed:"
	@echo "  export PATH=\"\$$HOME/.local/bin:\$$PATH\""
	@echo ""
	@echo "For YouTube support, install yt-dlp:"
	@echo "  pip install yt-dlp"

# Install to system-wide bin directory
install-system: build
	@echo "Installing to /usr/local/bin/ (requires sudo)..."
	sudo cp bin/scribe /usr/local/bin/
	sudo cp scripts/whisper_wrapper.py /usr/local/bin/
	sudo cp scripts/extract_frames.sh /usr/local/bin/
	sudo cp scripts/youtube_helper.py /usr/local/bin/
	sudo chmod +x /usr/local/bin/whisper_wrapper.py /usr/local/bin/extract_frames.sh /usr/local/bin/youtube_helper.py
	@echo "System-wide installation complete."
	@echo ""
	@echo "For YouTube support, install yt-dlp:"
	@echo "  pip install yt-dlp"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf bin/ dist/ releases/
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
	@echo "Testing scribe CLI compilation..."
	@./bin/scribe --help >/dev/null && echo "✅ scribe builds and runs" || echo "❌ scribe failed"
	@./bin/scribe analyze --help >/dev/null && echo "✅ scribe analyze subcommand works" || echo "❌ scribe analyze failed"
	@./bin/scribe transcribe --help >/dev/null && echo "✅ scribe transcribe subcommand works" || echo "❌ scribe transcribe failed"
	@./bin/scribe frames --help >/dev/null && echo "✅ scribe frames subcommand works" || echo "❌ scribe frames failed"
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

# Uninstall tools and patterns
uninstall:
	@echo "Uninstalling scribe tools..."
	@if command -v scribe >/dev/null 2>&1; then \
		scribe uninstall; \
	else \
		echo "scribe not found in PATH. Manual cleanup may be required."; \
	fi

# Create release binaries with complete packages
release-binaries: build-all
	@echo "Creating release packages..."
	@rm -rf releases
	@mkdir -p releases
	
	# Copy support scripts to each platform directory
	@for platform in macos-amd64 macos-arm64 linux-amd64 linux-arm64; do \
		cp scripts/whisper_wrapper.py dist/$$platform/; \
		cp scripts/extract_frames.sh dist/$$platform/; \
		cp scripts/youtube_helper.py dist/$$platform/; \
		chmod +x dist/$$platform/whisper_wrapper.py dist/$$platform/extract_frames.sh dist/$$platform/youtube_helper.py; \
		cp -r patterns dist/$$platform/; \
		echo "#!/bin/bash" > dist/$$platform/install.sh; \
		echo "# scribe installation script for $$platform" >> dist/$$platform/install.sh; \
		echo "mkdir -p ~/.local/bin" >> dist/$$platform/install.sh; \
		echo "cp scribe whisper_wrapper.py extract_frames.sh youtube_helper.py ~/.local/bin/" >> dist/$$platform/install.sh; \
		echo "chmod +x ~/.local/bin/whisper_wrapper.py ~/.local/bin/extract_frames.sh ~/.local/bin/youtube_helper.py" >> dist/$$platform/install.sh; \
		echo "mkdir -p ~/.config/fabric/patterns" >> dist/$$platform/install.sh; \
		echo "cp -r patterns/* ~/.config/fabric/patterns/" >> dist/$$platform/install.sh; \
		echo "echo 'Installation complete! Make sure ~/.local/bin is in your PATH'" >> dist/$$platform/install.sh; \
		echo "echo 'For YouTube support, install yt-dlp: pip install yt-dlp'" >> dist/$$platform/install.sh; \
		chmod +x dist/$$platform/install.sh; \
	done
	
	# Create platform-specific archives
	@echo "Creating macOS Intel archive..."
	@cd dist && tar -czf ../releases/scribe-macos-amd64.tar.gz macos-amd64/
	
	@echo "Creating macOS Apple Silicon archive..."
	@cd dist && tar -czf ../releases/scribe-macos-arm64.tar.gz macos-arm64/
	
	@echo "Creating Linux x64 archive (Fedora/Ubuntu)..."
	@cd dist && tar -czf ../releases/scribe-linux-amd64.tar.gz linux-amd64/
	
	@echo "Creating Linux ARM64 archive..."
	@cd dist && tar -czf ../releases/scribe-linux-arm64.tar.gz linux-arm64/
	
	@echo "Release packages created in ./releases/"
	@ls -la releases/

# Build release version with optimizations (legacy)
release:
	@echo "Building release version..."
	@echo "Version: $(VERSION)"
	@mkdir -p bin
	go mod download
	CGO_ENABLED=0 go build $(LDFLAGS) -o bin/scribe ./cmd/scribe
	@echo "Release build complete."