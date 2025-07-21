# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**screenscribe** is a CLI tool that processes videos and screen recordings to extract both audio transcripts and visual context, synthesizing them into structured Markdown or HTML notes. This is particularly valuable for technical content where visual elements (diagrams, charts, code demonstrations) are as important as spoken content.

## Architecture

This is a Python-based CLI application designed around a modular pipeline:

```
[Input Video/Audio] → [Audio Extraction + Transcription] → [Frame Extraction + Scene Detection] 
                   → [Temporal Alignment] → [LLM Synthesis] → [Markdown/HTML Output]
```

### Core Components (Target Structure)
- `src/screenscribe/cli.py` - Typer-based CLI entry point
- `src/screenscribe/audio.py` - Whisper integration for transcription
- `src/screenscribe/video.py` - Frame extraction and scene detection via ffmpeg
- `src/screenscribe/align.py` - Temporal alignment of transcript to frames
- `src/screenscribe/synthesis.py` - LLM-based content synthesis via LiteLLM
- `src/screenscribe/output.py` - Markdown/HTML generation
- `src/screenscribe/models.py` - Pydantic data models

## Development Commands

Since this is a new project with no existing build configuration, these commands will need to be established:

### Setup (To Be Created)
```bash
# Install dependencies
poetry install
./scripts/install_ffmpeg.sh

# Setup environment
cp .env.example .env
# Edit .env with API keys
```

### Testing (To Be Created)
```bash
# Run tests
poetry run pytest tests/ -v

# Run tests with coverage
poetry run pytest tests/ -v --cov=src/screenscribe --cov-report=term-missing
```

### Code Quality (To Be Created)
```bash
# Lint and format
poetry run ruff check src/ tests/ --fix
poetry run black src/ tests/
poetry run mypy src/
```

### Usage
```bash
# Basic usage
python -m screenscribe video.mp4 --output notes/

# With options
python -m screenscribe video.mp4 --output notes/ --format html --whisper-model medium
```

## Key Dependencies (Target)

- **faster-whisper**: Audio transcription engine (2-5x faster than openai-whisper)
- **opencv-python**: Video frame processing
- **yt-dlp**: YouTube video download support
- **litellm**: LLM provider abstraction with fallbacks
- **typer**: CLI framework
- **pydantic**: Data validation and modeling
- **ffmpeg-python**: Video processing wrapper

## System Dependencies

- **ffmpeg**: Required for video/audio processing
  - macOS: `brew install ffmpeg`
  - Fedora: `sudo dnf install ffmpeg`

## Configuration

Environment variables (via .env):
- `OPENAI_API_KEY`: For GPT-4 Vision synthesis
- `ANTHROPIC_API_KEY`: Fallback LLM provider
- `WHISPER_CACHE_DIR`: Model cache location (default: ~/.cache/whisper)

## Implementation Guidelines

### Error Handling Patterns
- Use graceful degradation (continue processing if individual components fail)
- Provide clear error messages with recovery suggestions
- Implement fallbacks (GPU → CPU for faster-whisper, primary → backup LLM)

### Performance Considerations
- Stream processing for large videos (avoid loading entire video into memory)
- Use scene detection for smart frame sampling vs. naive intervals
- Thumbnail generation at 320px width for LLM processing efficiency
- Async LLM requests with concurrency limits

### Critical Implementation Notes
- Always use pathlib.Path for cross-platform compatibility
- faster-whisper models are large (~1.5GB for medium) - handle first-download gracefully
- Check system dependencies (ffmpeg, CUDA) before processing
- Use temporary files for intermediate processing, clean up afterward
- Respect API rate limits and implement exponential backoff

## Testing Strategy

### Test Structure (To Be Created)
- `tests/fixtures/` - Sample video files for testing
- `tests/test_*.py` - Unit tests for each module
- `tests/test_integration.py` - End-to-end pipeline tests

### Validation Levels
1. **Syntax**: ruff, mypy, black
2. **Unit**: Individual module tests
3. **Integration**: Process sample 5-30 second videos
4. **Performance**: Ensure processing time < 2x video duration

## Development Guidelines

### Development Logging Requirements
**CRITICAL**: All development work MUST maintain the development log at `docs/CLAUDE_DEVELOPMENT_LOG.md`

Before each significant change:
1. Update the development log with:
   - **Context**: What problem are you solving?
   - **Changes**: Bullet list of key changes
   - **Validation**: How did you test?
2. Track progress in `docs/development-logs/CLAUDE_DEVELOPMENT_LOG.md`  
3. Use `[skip-dev-log]` flag only for emergency fixes

### Pre-Commit Workflow
1. Run tests: `pytest tests/`
2. Update development log: `docs/CLAUDE_DEVELOPMENT_LOG.md`
3. Security scan: `bandit -r src/backend/`
4. Update progress tracking in `docs/development-logs/`

### Development & Pre-Commit Checklist

**CRITICAL**  Every non-emergency change **must** be fully documented in `docs/CLAUDE_DEVELOPMENT_LOG.md`. Keep the commit message short; put the deep details in the log.

1. **Update the Development Log** (`docs/CLAUDE_DEVELOPMENT_LOG.md`)  
   - **Context** – What problem are you solving?  
   - **Changes** – Bullet list of key updates  
   - **Validation** – How you tested the changes  
   - **Notes / Links** – Extra discussion, screenshots, references  

**IMPORTANT** Use `[skip-dev-log]` **only** for emergency hot-fixes.

2. **Craft a Concise Commit Message**

   Commit message template:

   ```text
   <50–72-character summary>  (#<issue-id> | DEVLOG:<entry-id>)

   Optional short body (wrap at 72 chars).
   Leave deep details in CLAUDE_DEVELOPMENT_LOG.md.


### Code Style
- **Python**: Type hints everywhere, Pydantic for validation, async/await for I/O
- **TypeScript**: Strict mode, Vue 3 Composition API, no any types
- **Documentation**: Docstrings for all public functions, README for each module
- **Security**: Follow Red Hat security baseline for all implementations

### Testing Requirements
- Unit tests for all business logic (pytest)
- Integration tests for API endpoints
- E2E tests for critical user flows (Playwright)
- Minimum 80% code coverage

### Red Hat Security Practices
Apply Red Hat security baseline to all code:

#### Credentials Management
- ✓ Environment variables for all API keys (TRADOVATE_API_KEY, SCHWAB_CLIENT_ID, etc.)
- ✓ Secrets rotation every 90 days (document in security log)
- ✓ Never commit credentials (enforced via .gitignore)

#### Dependencies & Runtime
- ✓ Run vulnerability scanners in CI (bandit for Python, npm audit for JS)
- ✓ Pin all versions in uv.lock and package-lock.json
- ✓ Non-root containers only (USER 1000:1000 in Dockerfiles)
- ✓ Rate limiting on all API endpoints (implemented in FastAPI)
- ✓ Pydantic validation for all inputs

#### Audit & Compliance
- ✓ Security event logging (90-day retention)
- ✓ Quarterly dependency updates (tracked in CHANGELOG.md)
- ✓ OAuth2 token refresh logging

#### API Key Management
- All broker credentials stored in environment variables
- OAuth2 refresh tokens encrypted at rest
- Automatic token rotation with audit logging
- Rate limiting per Red Hat standards:
  - 100 requests/minute for authenticated users
  - 10 requests/minute for webhooks
  - Circuit breakers for broker APIs

#### Container Security
- Non-root user (1000:1000) in all containers
- Read-only root filesystem where possible
- Security scanning in CI pipeline
- Minimal base images (distroless preferred)

#### Input Validation
- Pydantic models for ALL external inputs
- Webhook signature verification (HMAC-SHA256)
- Order size validation against funded account rules
- SQL injection prevention via parameterized queries

### Git Workflow
- Feature branches from `main`
- Conventional commits (feat:, fix:, docs:, etc.)
- PR reviews required for all changes
- CI must pass before merge

## Current Status

This is a planning/design phase project. The current repository contains:
- `PRPs/prp_screenscribe_enhanced.md` - Detailed implementation blueprint
- `docs/prd_screenscribe.md` - Product requirements document

No code implementation exists yet. Development should follow the detailed blueprint in the PRP document.