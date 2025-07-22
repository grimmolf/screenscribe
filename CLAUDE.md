# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**screenscribe** is an AI-powered video analysis tool that transforms videos into structured, searchable notes. Built as a Go-based CLI application that integrates with the Fabric AI framework by Daniel Miessler.

## Architecture

**Technology Stack:**
- Primary: Go 1.21+ (unified `scribe` CLI application)
- Backend: Python 3 (Whisper transcription), Shell scripts (ffmpeg frame extraction)
- AI Integration: Fabric patterns for LLM-powered analysis
- Build: Makefile with cross-compilation support

**Processing Pipeline:**
```
[Video Input] → [Audio Extraction + Whisper] → [Frame Extraction] → [JSON Output] → [Fabric AI Analysis]
```

**Multi-Backend Audio System:**
- MLX (Apple Silicon GPU acceleration - 20-30x speedup)
- faster-whisper (CPU optimization) 
- OpenAI Whisper (fallback)

## Development Commands

**Build System (from `/fabric-extension/`):**
```bash
make build          # Build for current platform
make build-all      # Cross-compile for all platforms  
make install        # Install to ~/.local/bin/
make test           # Run functionality tests
make clean          # Remove build artifacts
make release-binaries # Create distribution packages
```

**Testing:**
```bash
# Functionality tests
make test

# End-to-end workflow validation
scribe analyze examples/sample.mp4 | fabric -p analyze_video_content

# Backend-specific testing
scribe transcribe --backend mlx sample.mp4
```

## Project Structure

**Main Implementation:**
- `/fabric-extension/` - Go-based CLI and scripts (active development)
- `/fabric-extension/cmd/scribe/` - Unified CLI application (main.go ~970 lines)
- `/fabric-extension/scripts/` - Python/Shell backend processing
- `/fabric-extension/patterns/` - Fabric AI patterns for video analysis

**Key Files:**
- `fabric-extension/Makefile` - Build system with cross-compilation
- `fabric-extension/go.mod` - Go dependencies (cobra CLI framework)
- `fabric-extension/scripts/whisper_wrapper.py` - Multi-backend Whisper integration
- `fabric-extension/scripts/extract_frames.sh` - ffmpeg-based frame extraction

**Legacy:**
- `/src/screenscribe/` - Deprecated Python package (being phased out)

## CLI Usage

**Unified `scribe` command with subcommands:**
```bash
# Complete video analysis (transcript + frames) - auto-detects Apple Silicon
scribe analyze video.mp4 | fabric -p analyze_video_content

# Individual components with backend control
scribe transcribe --model medium --backend auto lecture.mp4 
scribe frames --interval 60 tutorial.mp4

# Version information
scribe --version              # Quick version
scribe version                # Detailed version with build info

# Management (multiple forms supported)
scribe update / scribe --update           # Self-update from GitHub
scribe uninstall / scribe --uninstall     # Remove tools and patterns
```

**YouTube Integration:**
- Direct URL processing with transcript extraction
- yt-dlp integration for video download and native transcript extraction

## Dependencies

**System Requirements:**
- ffmpeg (video processing)
- jq (JSON processing)
- python3, Go 1.21+

**Python Packages:**
- faster-whisper (CPU optimization)
- mlx-whisper (Apple Silicon GPU acceleration - 20-30x speedup)  
- yt-dlp (YouTube integration)
- openai-whisper (fallback)

**Go Dependencies:**
- github.com/spf13/cobra (CLI framework)

## AI Analysis Patterns

**Available Fabric Patterns:**
- `analyze_video_content` - Comprehensive video analysis with timeline
- `extract_code_from_video` - Programming tutorial code extraction
- `analyze_trading_video` - Trading education analysis
- `extract_technical_analysis` - Chart patterns and indicators

**Pattern Usage:**
```bash
# Chain multiple patterns
scribe analyze tutorial.mp4 | fabric -p analyze_video_content | fabric -p extract_key_points
```

## Performance Optimizations

**Apple Silicon Acceleration:**
- MLX backend provides 20-30x speedup on M1/M2/M3 Macs
- Automatic hardware detection and backend selection
- Graceful fallback to CPU processing

**Cross-Platform Distribution:**
- Pre-built binaries for macOS (Intel/ARM) and Linux (AMD64/ARM64)
- Self-contained ~7MB binaries with cross-compilation support
- Complete installation packages in `releases/` directory

## Development Notes

**Recent Migration:** Project migrated from Python-based to Go-based Fabric extension for better performance and distribution.

**Build Process:** Uses cross-compilation to create binaries for all supported platforms simultaneously.

**Privacy-First Design:** Videos are processed locally - only extracted text and frame data sent to AI providers via Fabric.

**Self-Updating:** Built-in update mechanism downloads and installs latest releases from GitHub.

**Apple Silicon Optimization:** Intelligent auto-detection with MLX GPU acceleration (20-30x speedup), proper compute type handling, and offline model caching.

**Version Management:** Build-time version injection with git commit tracking and detailed version information.