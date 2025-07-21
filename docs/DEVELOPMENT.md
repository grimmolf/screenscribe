# Development Guide

This guide provides developers with the complete context for understanding, contributing to, and extending screenscribe.

## Project Narrative: WHY → HOW → WHAT

### 🎯 WHY: The Problem We Solved

**See: [Product Requirements Document (PRD)](prd_screenscribe.md)**

screenscribe was created to solve a fundamental gap in video content analysis:

**The Core Problem:**
- Technical videos contain critical visual information that pure transcription misses
- Existing tools focus on speech-only analysis, ignoring visual context
- Manual note-taking from videos is time-consuming and error-prone
- Visual elements (diagrams, code, charts) are as important as spoken content

**User Pain Points:**
- Developers spending hours manually documenting code walkthroughs
- Students missing visual details from online lectures  
- Business teams unable to extract insights from presentation recordings
- Content creators needing better analysis of their own material

**Market Gap:**
- No existing tools combine visual + audio analysis effectively
- YouTube auto-captions are inaccurate and lack visual context
- Transcription services ignore the critical visual component

**Our Solution:**
A CLI tool that processes videos to extract both audio transcripts and visual context, synthesizing them into comprehensive, structured notes using AI.

### 🛠️ HOW: Our Development Approach

**See: [Product Requirements Prompt (PRP)](../PRPs/prp_screenscribe_enhanced.md)**

Our development followed a comprehensive PRP that detailed:

**Technical Architecture:**
```
[Input Video/Audio] → [Audio Extraction + Transcription] → [Frame Extraction + Scene Detection] 
                   → [Temporal Alignment] → [LLM Synthesis] → [Markdown/HTML Output]
```

**Key Design Principles:**
1. **Stream Processing**: Handle large videos without memory exhaustion
2. **Graceful Degradation**: Continue processing even if components fail
3. **User Feedback**: Clear progress indicators and meaningful error messages
4. **Extensibility**: Modular pipeline architecture for easy component swapping
5. **Local-First**: Capable of fully offline operation with local models

**Implementation Strategy:**
- Python-based CLI with Typer for user interface
- faster-whisper for high-quality transcription (2-5x faster with Voice Activity Detection)
- FFmpeg + OpenCV for video processing
- LiteLLM for multi-provider LLM integration
- Pydantic for robust data validation
- Async/await patterns for optimal performance

**Quality Standards:**
- Comprehensive error handling with fallbacks
- Cross-platform compatibility (macOS, Linux, Windows)  
- Production-ready with proper logging and validation
- Extensive test suite with realistic fixtures

### 📋 WHAT: What We Actually Built

**See: [Development Log](CLAUDE_DEVELOPMENT_LOG.md)**

The development log chronicles our actual implementation across multiple iterations:

**DEVLOG-001: Initial Project Setup**
- Created CLAUDE.md with project overview and development guidelines
- Established the foundation for the complete implementation

**DEVLOG-002: Complete PRP Implementation**
- Full CLI tool with all core features
- Modular pipeline: audio → video → alignment → synthesis → output
- Production-ready code with comprehensive error handling
- Cross-platform support and dependency management

**DEVLOG-003: uv Packaging Conversion**
- Migrated from Poetry to uv for simpler user installation
- Single-command install: `curl -LsSf <script> | bash`
- Global `screenscribe` command available after installation

**DEVLOG-004: Externalized Prompts**
- Moved hardcoded prompts to editable markdown files
- Template system with variable substitution
- User customization without touching code

**DEVLOG-005: Comprehensive Documentation**
- Complete user documentation suite
- Real-world examples with performance benchmarks
- Professional presentation ready for open source

## Architecture Deep Dive

### Module Structure
```
src/screenscribe/
├── cli.py          # Entry point and argument parsing
├── models.py       # Pydantic data models
├── audio.py        # Whisper integration
├── video.py        # FFmpeg + OpenCV processing
├── align.py        # Temporal alignment algorithms
├── synthesis.py    # LLM integration via LiteLLM
├── output.py       # Markdown/HTML generation
├── utils.py        # Shared utilities
└── config.py       # Configuration management
```

### Data Flow
1. **Input Validation**: Check video format, dependencies, API keys
2. **Audio Processing**: Extract audio track, transcribe with Whisper
3. **Video Processing**: Extract frames via scene detection or intervals
4. **Temporal Alignment**: Match transcript segments to video frames
5. **LLM Synthesis**: Analyze frames with visual + audio context
6. **Output Generation**: Create structured Markdown/HTML notes

### Key Technical Decisions

**Why faster-whisper?**
- 2-5x faster processing than openai-whisper
- Enhanced accuracy with Voice Activity Detection (VAD)
- Better GPU memory management and efficiency
- Active development vs stagnant openai-whisper
- Local processing capability with improved performance
- Multiple model sizes for speed/quality trade-offs

**Why Scene Detection?**
- More intelligent than naive interval sampling
- Captures meaningful visual transitions
- Reduces unnecessary processing of static content

**Why LiteLLM?**
- Multi-provider support (OpenAI, Anthropic, local models)
- Automatic fallbacks for reliability
- Unified interface for different vision models

**Why Pydantic?**
- Runtime validation of complex data structures
- Type safety for all data models
- Clear API contracts between modules

## Development Workflow

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/screenscribe/screenscribe.git
cd screenscribe

# Install development dependencies
uv sync --dev

# Install system dependencies
./scripts/install_ffmpeg.sh

# Run tests to verify setup
uv run pytest tests/ -v
```

### Development Commands

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Lint and format
make lint
make format

# Build package
make build

# Install in development mode
uv pip install -e .
```

### Contributing Guidelines

1. **Understanding the Codebase**
   - Read this development guide first
   - Review the PRD to understand user needs
   - Check the PRP for implementation context
   - Look at the development log for implementation history

2. **Making Changes**
   - Create feature branch from `main`
   - Follow existing code patterns and architecture
   - Add comprehensive tests for new functionality
   - Update documentation as needed

3. **Code Standards**
   - Type hints for all public functions
   - Docstrings following Google style
   - Error handling with user-friendly messages
   - Cross-platform compatibility

4. **Testing Requirements**
   - Unit tests for all business logic
   - Integration tests for end-to-end workflows
   - Mock external dependencies (LLM APIs, FFmpeg)
   - Test with representative video content

### Extension Points

**Adding New Output Formats**
1. Extend `OutputGenerator` with new format method
2. Add format validation to `ProcessingOptions`
3. Update CLI argument parsing
4. Add tests with sample outputs

**Supporting New LLM Providers**
1. Add provider configuration to `ContentSynthesizer`
2. Implement authentication in `_setup_llm()`
3. Add to fallback chain in router configuration
4. Test with representative content

**Custom Frame Extraction Methods**
1. Add new sampling mode to `VideoProcessor`
2. Implement extraction logic following existing patterns
3. Update CLI options and validation
4. Add performance benchmarks

## Performance Optimization

### Bottlenecks and Solutions

**Whisper Transcription (Largest bottleneck)**
- Solution: Use appropriate model size for content
- Optimization: GPU acceleration when available
- Fallback: Automatic CPU fallback for memory constraints

**LLM API Calls (Second largest bottleneck)**
- Solution: Async processing with concurrency limits
- Optimization: Efficient prompt templates
- Fallback: Multiple provider support

**Frame Extraction (Usually fast)**
- Solution: Scene detection vs. naive intervals
- Optimization: Pre-scaling for scene analysis
- Consideration: Balance threshold sensitivity

### Resource Usage Patterns

| Video Length | Peak RAM | Processing Time | API Calls | Disk Usage |
|-------------|----------|-----------------|-----------|------------|
| 5 min       | ~2 GB    | 2-3 min        | 10-20     | ~50 MB     |
| 15 min      | ~3 GB    | 5-8 min        | 20-40     | ~150 MB    |
| 30 min      | ~4 GB    | 8-15 min       | 25-50     | ~300 MB    |
| 60 min      | ~6 GB    | 15-30 min      | 40-80     | ~600 MB    |

## Debugging and Troubleshooting

### Common Development Issues

**Whisper Model Loading Failures**
- Check available memory and model size compatibility
- Verify CUDA setup for GPU acceleration
- Ensure network connectivity for first-time downloads

**FFmpeg Integration Problems**
- Verify FFmpeg installation and PATH configuration
- Check video codec compatibility
- Test with known-good sample videos

**LLM API Issues**
- Validate API key format and permissions
- Check network connectivity and proxy settings
- Monitor rate limits and implement backoff

### Debug Mode

Enable verbose logging for detailed debugging:

```bash
screenscribe video.mp4 --verbose
```

This provides:
- Detailed processing steps
- Timing information for each stage
- API request/response logging
- File operation tracking

## Future Roadmap

### Planned Features
- Real-time video stream processing
- OCR integration for text-heavy content
- Multi-language support beyond English
- Plugin system for custom processing stages
- Web interface for non-CLI users

### Technical Debt
- Migrate to async file I/O throughout
- Implement proper caching for repeated processing
- Add more comprehensive error recovery
- Optimize memory usage for very long videos

### Community Contributions
- Example prompt templates for different domains
- Integration guides for popular tools
- Performance optimizations
- Platform-specific installers

## Related Documentation

### For Users
- **[📖 Complete User Manual](USER_MANUAL.md)** - Everything users need to know about screenscribe
- **[Installation Guide](user/installation.md)** - Platform-specific installation details
- **[Troubleshooting](user/troubleshooting.md)** - Common issues and solutions
- **[Real-World Examples](examples/real-world-examples.md)** - See screenscribe in action

### For Developers  
- **[API Reference](api-reference.md)** - Technical API documentation and module details
- **[Development Log](CLAUDE_DEVELOPMENT_LOG.md)** - Complete development history

---

This development guide provides the complete context for understanding screenscribe's evolution from problem identification through implementation. For specific technical details, consult the API reference and source code.