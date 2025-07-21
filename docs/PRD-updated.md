## Product Requirements Document (PRD)

### 1. Overview

- **Project Name:** screenscribe
- **Objective:** Build a CLI tool that processes videos and screen/audio recordings (especially technical or instructional content) to produce structured, searchable notes in Markdown or HTML format.
- **Problem Statement:** Technical conversations, presentations, and tutorial videos often contain visual cues (e.g., diagrams, charts, interfaces) that are critical to understanding. Existing transcription and summarization tools are speech-first and don’t synthesize visual and verbal context together. YouTube's auto-transcription is often inaccurate or poorly aligned, making it inadequate for deep technical or visual content.
- **Success Metrics:**
  - Accurate summarization of video+audio content with visual references.
  - Easy CLI invocation with simple output formats.
  - Useful insights extracted from trading videos (e.g. strategy components, visual chart references).
  - Usability across macOS and Fedora systems.
  - Platform-optimized performance (GPU acceleration where available).

### 2. User Stories

| ID | Role                                                                                                                                            | Story |
| -- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| 1  | As a technical user, I want to record customer conversations and receive structured summaries of both what was said and what was shown.         |       |
| 2  | As a self-learner, I want to process YouTube trading strategy videos into actionable summaries with references to what is visible on the chart. |       |
| 3  | As a technical viewer, I want to extract key concepts from videos that combine spoken explanations with technical diagrams.                     |       |
| 4  | As a CLI user, I want a local, scriptable tool that outputs Markdown/HTML reports without requiring a web UI or online service.                 |       |
| 5  | As a user disappointed by YouTube’s auto-transcription, I want a more accurate transcription engine to generate reliable text from speech.      |       |

### 3. Core Features & Requirements

| Feature                | Description                                                   | Priority     |
| ---------------------- | ------------------------------------------------------------- | ------------ |
| Video/audio ingest     | Accept local files (mp4, mkv, etc.) or URLs                   | MVP          |
| Audio transcription    | Use Whisper or equivalent to convert speech to text           | MVP          |
| Visual frame sampling  | Capture keyframes, screen changes, or OCR segments            | MVP          |
| Temporal alignment     | Match transcript segments to visual frames                    | MVP          |
| Context synthesis      | Use LLM to synthesize structured notes with visual references | MVP          |
| CLI interface          | Simple command-line invocation                                | MVP          |
| HTML/Markdown output   | Export structured notes                                       | MVP          |
| YouTube video support  | Accept YouTube URLs and download/parse                        | Nice-to-have |
| Configurable pipelines | Swap components (e.g., LLM, OCR backend)                      | Nice-to-have |
| Timeline view          | Visual timeline or cue list of visual/audio events            | Nice-to-have |

### 4. System Architecture

- **CLI Tool** with pluggable modules:

  - `input`: local file, screen recording, or YouTube
  - `audio`: Whisper transcription
  - `video`: keyframe extraction or OCR
  - `fusion`: time-aligned summarization (via LLM)
  - `output`: markdown/html exporter

- **Data Flow:**

```
[input] → [audio extract + video scan] 
        → [transcribe + keyframe detect]
        → [align + synthesize]
        → [output.md or output.html]
```

### 5. Tech Stack

| Layer               | Technology Options                                                    |
| ------------------- | --------------------------------------------------------------------- |
| CLI Interface       | Python + Typer                                                        |
| Audio Transcription | Multi-backend: MLX Whisper (Mac), faster-whisper (universal), whisper.cpp |
| Frame Analysis      | OpenCV / ffmpeg / pytesseract                                        |
| LLM                 | OpenAI GPT-4 / Local (Mistral, Mixtral) via LiteLLM                 |
| Output              | Markdown + Pandoc → HTML                                             |
| Video Ingest        | yt-dlp / ffmpeg                                                      |
| Storage             | Local file system                                                    |

### 6. Non-Functional Requirements

- **Performance:** Must process videos under 30 mins in under 10 mins (goal)
  - M3 Ultra: Target 60-80s for 10-min audio with MLX backend
  - Linux/CUDA: Target 30-40s for 10-min audio with faster-whisper
  - CPU fallback: Acceptable up to 300s for 10-min audio
- **Security:** Offline-capable if using local models
- **Portability:** Must run on macOS (Intel & Apple Silicon), Linux, and Windows
- **Extensibility:** Modular pipeline architecture with pluggable audio backends
- **Error Handling:** Clear errors for missing dependencies or invalid input
- **Platform Detection:** Automatic selection of optimal backend for current system

### 7. Assumptions & Constraints

- Videos are primarily in English (initially)
- User has access to local GPU/CPU resources
- No need for live or real-time processing

### 8. Open Questions / Decisions

| Topic           | Question                                                                                                                           | Owner     | Status |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------- | --------- | ------ |
| LLM routing     | Allow user-configurable model routing via LiteLLM with fallback to OpenAI unless `--nofallback` is specified                       | Confirmed | Locked |
| Frame selection | Default to scene change detection using ffmpeg (e.g., `select='gt(scene,0.3)'`), with optional `--sampling-mode=interval` fallback | Confirmed | Locked |
| Audio model     | User-configurable Whisper model (e.g. `--whisper-model`), defaulting to `medium` for balance of speed and accuracy                 | Confirmed | Locked |
| Audio backend   | Multi-backend strategy: MLX (Apple Silicon), faster-whisper (universal), whisper.cpp (performance), with auto-detection            | Confirmed | Locked |

### 9. Technical Discoveries

#### Audio Backend Investigation (2025-01-21)

**Finding:** faster-whisper does not support Apple Silicon GPU acceleration (MPS/Metal). It only supports NVIDIA CUDA GPUs.

**Impact:** M3 Ultra and other Apple Silicon Macs cannot utilize GPU cores for transcription with current implementation.

**Solution:** Implement multi-backend audio transcription system:
- **MLX Whisper**: Apple Silicon GPU acceleration (2-3x faster than CPU)
- **faster-whisper**: Cross-platform with CUDA support for NVIDIA GPUs
- **whisper.cpp**: High-performance CPU/Neural Engine option
- **Auto-detection**: Platform-aware backend selection

**Performance Benchmarks (10-min audio):**
- M3 Ultra + MLX: ~60-80s
- M3 Ultra + CPU: ~180-200s  
- RTX 4090 + CUDA: ~30-40s
- whisper.cpp: ~20-40s (platform dependent)

