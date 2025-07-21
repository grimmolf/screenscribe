# screenscribe User Manual

**Complete guide to using screenscribe for video-to-notes conversion**

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)  
3. [Basic Usage](#basic-usage)
4. [Command Reference](#command-reference)
5. [Output Guide](#output-guide)
6. [Prompt Customization](#prompt-customization)
7. [Content Type Optimization](#content-type-optimization)
8. [Performance Tuning](#performance-tuning)
9. [Integration Examples](#integration-examples)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### What is screenscribe?

**screenscribe** transforms videos into structured, searchable notes by combining:
- 🎤 **Audio transcription** with faster-whisper (2-5x faster than OpenAI Whisper)
- 👁️ **Visual analysis** with GPT-4 Vision
- 📝 **Smart synthesis** into Markdown or HTML notes

### Perfect for:
- 📖 Educational content (lectures, tutorials)
- 💼 Business meetings and presentations  
- 👨‍💻 Technical training and code walkthroughs
- 📊 Conference talks and webinars
- 🎥 Content creation and analysis

### Quick Start

**For development/source code users:**

```bash
# 1. Navigate to screenscribe directory
cd /path/to/screenscribe/

# 2. Install from source
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install --editable .

# 3. Set your API key
export OPENAI_API_KEY="sk-your-key-here"

# 4. Process your first video
screenscribe video.mp4
```

---

## Installation

### Install from Release (Coming Soon)

Once published to PyPI, you'll be able to install with:

```bash
# One-command install (when released)
curl -LsSf https://raw.githubusercontent.com/screenscribe/screenscribe/main/scripts/install.sh | bash

# Or manually (when released)
uv tool install screenscribe
```

### Install for Development (Current)

**If you're working with source code or cloned this repository:**

```bash
# 1. Navigate to the project directory
cd /path/to/screenscribe/

# 2. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install screenscribe from source (editable mode)
uv tool install --editable .

# 3. Install FFmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Fedora: sudo dnf install ffmpeg
```

### Setup API Keys

**Required: OpenAI API Key**
```bash
export OPENAI_API_KEY="sk-your-key-here"

# Make permanent
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.bashrc
```

**Optional: Anthropic Fallback**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Update

**For development/source code users:**
```bash
# Navigate to screenscribe directory
cd /path/to/screenscribe/

# Pull latest changes
git pull origin main

# Reinstall with latest code
uv tool install --editable . --force
```

**For release users (when published):**
```bash
# Update to latest version
uv tool upgrade screenscribe

# Verify updated version
screenscribe --version  # (when version command is added)
```

**Check for Updates:**
- Watch the GitHub repository for releases
- Subscribe to release notifications
- Check the development log for latest features

### Uninstall

```bash
# Remove screenscribe
uv tool uninstall screenscribe

# Optional: Remove uv
curl -LsSf https://astral.sh/uv/uninstall.sh | sh
```

### Verification

```bash
screenscribe --help    # Verify installation
ffmpeg -version        # Verify FFmpeg
```

---

## Basic Usage

### Process Local Videos

```bash
# Basic usage
screenscribe video.mp4

# Specify output directory
screenscribe video.mp4 --output ~/Documents/notes/

# Choose output format
screenscribe video.mp4 --format html
```

### Process YouTube Videos

```bash
screenscribe "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Quick Examples

```bash
# Fast processing
screenscribe demo.mp4 --whisper-model tiny

# High quality
screenscribe tutorial.mp4 --whisper-model large --format html

# Custom location
screenscribe lecture.mp4 --output ./my-notes/
```

---

## Command Reference

### Core Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o` | Output directory | `./screenscribe_output` |
| `--format`, `-f` | Output format (markdown/html) | `markdown` |
| `--verbose`, `-v` | Show detailed progress | `false` |

### Transcription Options

| Option | Description | Default |
|--------|-------------|---------|
| `--whisper-model` | Model size (tiny/base/small/medium/large) | `medium` |

**Model Comparison:**
- `tiny`: Fastest, lower accuracy
- `base`: Good balance for simple content
- `small`: Better accuracy, still fast
- `medium`: **Recommended** - good accuracy/speed balance
- `large`: Best accuracy, slower

### Frame Extraction Options

| Option | Description | Default |
|--------|-------------|---------|
| `--sampling-mode` | Extraction method (scene/interval) | `scene` |
| `--interval` | Seconds between frames (interval mode) | `5.0` |
| `--scene-threshold` | Scene detection sensitivity (0.1-1.0) | `0.3` |

**Sampling Modes:**
- **Scene Detection**: Intelligent extraction at visual changes (recommended)
- **Interval**: Extract every N seconds (good for talking-head content)

### LLM Options

| Option | Description | Default |
|--------|-------------|---------|
| `--llm` | Provider (openai/anthropic) | `openai` |
| `--no-fallback` | Disable provider fallbacks | `false` |
| `--prompts-dir` | Custom prompt templates directory | `./prompts` |

### Full Command Example

```bash
screenscribe video.mp4 \
  --output ./notes/ \
  --format html \
  --whisper-model large \
  --sampling-mode scene \
  --scene-threshold 0.2 \
  --prompts-dir ./custom-prompts/ \
  --verbose
```

---

## Output Guide

### Generated Files

```
screenscribe_output/
├── notes.md                    # 📝 Main structured notes
├── notes.html                  # 🌐 HTML version (if requested)
├── transcript.json             # 📊 Raw transcription data
├── processing_result.json      # ⚙️ Processing metadata
├── frames/                     # 🖼️ Extracted video frames
│   ├── frame_0000.jpg
│   └── ...
└── thumbnails/                 # 🖼️ Resized thumbnails
    ├── thumb_frame_0000.jpg
    └── ...
```

### Notes Structure

**Header Section:**
- Video metadata and processing info
- Duration and technical details

**Timeline Section:**
- Chronologically ordered frames
- Each entry contains:
  - Timestamp and thumbnail
  - Transcript excerpt  
  - Visual description
  - AI-generated summary
  - Extracted key points

### Example Note Entry

```markdown
### [0:02:15] (135.4s)

[![Frame](thumbnails/thumb_frame_0005.jpg)](frames/frame_0005.jpg)

**Transcript:** "Now let's look at the function definition. As you can see here, we're using async await..."

**Summary:** Code editor showing Python async function implementation with syntax highlighting

**Visual:** IDE interface displaying Python code with async/await keywords highlighted

**Key Points:**
- Async function definition syntax
- Await keyword usage  
- Error handling in async functions
```

---

## Prompt Customization

### Why Customize Prompts?

Default prompts work well for general content, but customization improves results for specific domains:
- 🎯 **Better accuracy** for your content type
- 📚 **Domain-specific vocabulary** 
- 🔍 **Focused analysis** on relevant elements
- 📋 **Consistent output** format

### Customization Methods

#### Method 1: Edit Default Prompts (Easiest)

```bash
# Edit the main analysis prompt
nano prompts/synthesis.md
```

#### Method 2: Custom Directory

```bash
# Create custom prompts
mkdir my-prompts
cp prompts/synthesis.md my-prompts/

# Edit your version
nano my-prompts/synthesis.md

# Use with screenscribe
screenscribe video.mp4 --prompts-dir my-prompts/
```

#### Method 3: Environment Variable

```bash
export SCREENSCRIBE_PROMPTS_DIR=/path/to/custom/prompts
screenscribe video.mp4  # Automatically uses custom prompts
```

### Template Variables

Prompts support these variables:
- `{timestamp_str}` - Frame timestamp (HH:MM:SS)
- `{time_window}` - Time window for transcript alignment
- `{transcript_text}` - Relevant transcript text

### Content-Specific Examples

#### Programming Tutorials

```markdown
You are analyzing a programming tutorial video frame.

Focus on:
1. Code snippets and syntax highlighting
2. IDE features and interface elements  
3. Debugging information and error messages
4. File structures and project navigation
5. Terminal/console output

Frame timestamp: {timestamp_str}
Transcript: "{transcript_text}"

Provide JSON response:
{{
  "summary": "Brief coding concept description",
  "visual_description": "Detailed code/IDE content",
  "key_points": ["concept 1", "syntax detail 2", "best practice 3"]
}}
```

#### Business Presentations

```markdown
You are analyzing a business presentation video frame.

Focus on:
1. Slide titles and main headings
2. Charts, graphs, and data visualizations
3. Key metrics and business numbers
4. Strategic concepts and frameworks
5. Action items and recommendations

Frame timestamp: {timestamp_str}  
Transcript: "{transcript_text}"

Provide JSON response:
{{
  "summary": "Main business point or slide topic",
  "visual_description": "Description of slides/charts/visuals", 
  "key_points": ["insight 1", "metric 2", "recommendation 3"]
}}
```

#### Academic Lectures  

```markdown
You are analyzing an academic lecture video frame.

Focus on:
1. Theoretical concepts and definitions
2. Mathematical equations and formulas
3. Diagrams and conceptual models
4. References to academic literature
5. Examples and case studies

Frame timestamp: {timestamp_str}
Transcript: "{transcript_text}"

Provide JSON response:
{{
  "summary": "Academic concept being discussed",
  "visual_description": "Description of equations/diagrams/content",
  "key_points": ["concept 1", "formula 2", "example 3"]
}}
```

### Advanced Prompt Engineering

#### Add Context Instructions

```markdown
You are analyzing a React.js tutorial. Pay attention to:
- JSX syntax and component structure
- Hook usage (useState, useEffect, etc.)
- Props and state management
- Component lifecycle methods
```

#### Quality Guidelines

```markdown
Guidelines for analysis:
- Be specific about code concepts, avoid generic terms
- Identify specific UI components and purposes
- Note best practices or anti-patterns
- Extract actionable insights viewers can apply
```

#### Special Case Handling

```markdown
Special handling:
- If no code visible, focus on verbal explanations
- For error screens, describe error type and solutions
- For blank screens, note transition states or loading
```

### Testing Your Prompts

1. **Start small**: Test with 2-3 minute videos
2. **Process and review**: Check generated notes quality
3. **Iterate**: Refine prompts based on results
4. **A/B test**: Compare different approaches

```bash
# Test original vs custom
screenscribe test.mp4 --output test-original/
screenscribe test.mp4 --prompts-dir custom/ --output test-custom/
diff test-original/notes.md test-custom/notes.md
```

---

## Content Type Optimization

### Technical Tutorials

**Optimal Settings:**
```bash
screenscribe tutorial.mp4 \
  --whisper-model large \
  --sampling-mode scene \
  --scene-threshold 0.15 \
  --prompts-dir ./coding-prompts/
```

**Why:**
- `large` model for technical terminology accuracy
- `scene` mode captures code/slide changes
- Lower threshold (0.15) catches subtle transitions
- Custom prompts focus on code analysis

### Business Presentations

**Optimal Settings:**
```bash
screenscribe presentation.mp4 \
  --format html \
  --sampling-mode scene \
  --scene-threshold 0.4
```

**Why:**
- HTML format for better presentation
- Scene mode perfect for slide changes
- Higher threshold (0.4) ignores minor movements

### Academic Lectures

**Optimal Settings:**
```bash
screenscribe lecture.mp4 \
  --sampling-mode interval \
  --interval 45 \
  --whisper-model medium
```

**Why:**
- Interval mode for minimal visual changes
- 45-second intervals capture key concepts
- Medium model sufficient for clear academic speech

### Interviews & Discussions

**Optimal Settings:**
```bash
screenscribe interview.mp4 \
  --sampling-mode interval \
  --interval 120 \
  --whisper-model base
```

**Why:**
- Interval mode since visuals are minimal
- 2-minute intervals focus on major topics
- Base model adequate for conversation

### Long-Form Content (>30 min)

**Optimal Settings:**
```bash
screenscribe long-video.mp4 \
  --whisper-model base \
  --sampling-mode interval \
  --interval 60 \
  --output ./long-notes/
```

**Why:**
- Faster `base` model for efficiency
- 60-second intervals reduce processing time
- Separate directory for organization

---

## Performance Tuning

### Speed vs Quality Trade-offs

#### Fastest Processing
```bash
screenscribe video.mp4 \
  --whisper-model tiny \
  --sampling-mode interval \
  --interval 10
```

#### Best Quality
```bash
screenscribe video.mp4 \
  --whisper-model large \
  --sampling-mode scene \
  --scene-threshold 0.1
```

#### Balanced (Recommended)
```bash
screenscribe video.mp4 \
  --whisper-model medium \
  --sampling-mode scene
```

### Resource Management

#### For Limited Memory
- Use smaller Whisper models (`tiny`, `base`, `small`)
- Increase interval time for interval sampling
- Process shorter video segments

#### For Limited API Credits
- Use higher scene thresholds (fewer frames)
- Use interval sampling with larger intervals  
- Enable `--no-fallback` to prevent backup API calls

#### Performance Expectations

*Note: With faster-whisper, transcription is 2-5x faster than previous openai-whisper versions*

| Video Length | Processing Time | Peak RAM | API Calls | Disk Usage |
|-------------|----------------|----------|-----------|------------|
| 5 min       | 1-2 min        | ~1.5 GB  | 10-20     | ~50 MB     |
| 15 min      | 3-5 min        | ~2 GB    | 20-40     | ~150 MB    |
| 30 min      | 5-10 min       | ~3 GB    | 25-50     | ~300 MB    |
| 60 min      | 10-20 min      | ~4 GB    | 40-80     | ~600 MB    |

---

## Integration Examples

### With Obsidian

Process videos directly into your Obsidian vault:

```bash
# Process into Obsidian vault
screenscribe tutorial.mp4 --output ~/ObsidianVault/Videos/

# Images will be properly linked and display in Obsidian
```

### With Notion

Convert to Notion-compatible format:

```bash
# Generate HTML for Notion import
screenscribe presentation.mp4 --format html

# Import the HTML file into Notion
```

### With Jupyter Notebooks

Embed results in notebooks:

```python
# Display in Jupyter
from IPython.display import Markdown, display

with open('screenscribe_output/notes.md', 'r') as f:
    display(Markdown(f.read()))
```

### Batch Processing

Process multiple videos:

```bash
# Process all MP4 files
for video in *.mp4; do
    screenscribe "$video" --output "notes/${video%.mp4}"
done

# With parallel processing
ls *.mp4 | xargs -I {} -P 4 screenscribe {} --output "notes/{}"
```

### Automated Workflows

Create smart processing scripts:

```bash
#!/bin/bash
# smart-screenscribe.sh

case "$1" in
  *tutorial*|*coding*|*programming*)
    PROMPTS_DIR="./coding-prompts"
    ;;
  *presentation*|*business*|*meeting*)
    PROMPTS_DIR="./business-prompts"
    ;;
  *lecture*|*academic*)
    PROMPTS_DIR="./academic-prompts"
    ;;
  *)
    PROMPTS_DIR="./default-prompts"
    ;;
esac

screenscribe "$1" --prompts-dir "$PROMPTS_DIR" "${@:2}"
```

---

## Troubleshooting

### Installation Issues

#### "screenscribe not found in package registry"
**Problem**: Getting error when running `uv tool install screenscribe`

**Solution**: This error occurs because screenscribe isn't published to PyPI yet. Use the development installation method:
```bash
cd /path/to/screenscribe/
uv tool install --editable .
```

**Why**: 
- `uv tool install screenscribe` → Looks for package on PyPI (fails)
- `uv tool install --editable .` → Installs from local source code (works)

#### Command not found: screenscribe
```bash
# Add uv bin directory to PATH
export PATH="$HOME/.local/bin:$PATH"

# Restart terminal or reload shell
source ~/.bashrc
```

#### FFmpeg not found
```bash
# Install FFmpeg for your system
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Fedora: sudo dnf install ffmpeg

# Verify installation
ffmpeg -version
```

### Processing Issues

#### API Key Errors
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check API key format (should start with sk-)
# Ensure sufficient credits in your account
```

#### Out of Memory
```bash
# Use smaller Whisper model
screenscribe video.mp4 --whisper-model tiny

# Or process shorter segments
screenscribe video.mp4 --sampling-mode interval --interval 30
```

#### No Audio Stream
- Ensure video file has an audio track
- Try with a different video file
- Check video format compatibility

#### Poor Transcription Quality
- Use larger faster-whisper model (`medium` or `large`)
- Ensure good audio quality in source video
- Try different video if audio is unclear
- **Note**: faster-whisper includes Voice Activity Detection (VAD) which automatically improves transcription quality by filtering out non-speech audio

#### Poor Visual Analysis
- Use custom prompts for your content type
- Lower scene threshold for more frames
- Check that frames are being extracted properly

### Performance Issues

#### Slow Processing
```bash
# Use faster Whisper model
screenscribe video.mp4 --whisper-model base

# Reduce frame extraction
screenscribe video.mp4 --sampling-mode interval --interval 10

# Update to latest version for performance improvements
cd /path/to/screenscribe/ && git pull && uv tool install --editable . --force
```

**Performance Optimizations (Latest Updates)**:
- **Apple Silicon**: Automatically uses up to 85% of CPU cores (23/28 on M3 Ultra) + GPU acceleration
- **Network Storage**: Files on NAS/SMB/NFS automatically copied locally for ~10x speed improvement  
- **Interruption**: Single ctrl+c for graceful shutdown, double ctrl+c for immediate exit
- **Model Updates**: Now uses GPT-4o (faster, more accurate than deprecated vision-preview)

#### Network Storage Issues
If transcription is extremely slow (>5 minutes per 1 hour of video):

```bash
# Force local copying (enabled by default)
screenscribe video.mp4 --copy-from-nas

# Disable if you prefer network processing
screenscribe video.mp4 --no-copy-from-nas
```

**Detected Network Paths**: `/volumes/`, `/mnt/`, paths containing `nfs`, `smb`, `cifs`

#### High API Costs
```bash
# Reduce frame extraction
screenscribe video.mp4 --scene-threshold 0.5

# Disable fallbacks
screenscribe video.mp4 --no-fallback

# Use interval sampling with larger intervals
screenscribe video.mp4 --sampling-mode interval --interval 60
```

### Output Issues

#### Missing Images
- Check that frames directory exists in output
- Verify file permissions
- Ensure sufficient disk space

#### Broken Links in Markdown
- Use relative paths for portability
- Check image file extensions match
- Verify output directory structure

#### JSON Parsing Errors
- Check custom prompts for proper JSON format
- Ensure template variables are correctly used
- Verify no unescaped braces in prompts

### Getting Help

1. **Check logs**: Run with `--verbose` for detailed output
2. **Test with simple video**: Try with a short, clear video
3. **Check system requirements**: Ensure Python 3.9+, sufficient RAM
4. **Review documentation**: See detailed guides in `docs/user/`
5. **Report issues**: GitHub Issues for bug reports

### System Requirements

- **Python**: 3.9 or higher
- **Memory**: 4GB minimum, 8GB recommended
- **Storage**: 2GB for model downloads
- **Network**: Internet for API calls and downloads

---

## Additional Resources

### Documentation
- **[Installation Guide](docs/user/installation.md)** - Detailed installation
- **[Usage Guide](docs/user/usage.md)** - Comprehensive examples
- **[Troubleshooting](docs/user/troubleshooting.md)** - Common issues
- **[Examples](docs/examples/)** - Real-world use cases

### For Developers
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing and architecture

### Support
- **Issues**: [GitHub Issues](https://github.com/screenscribe/screenscribe/issues)
- **Discussions**: [GitHub Discussions](https://github.com/screenscribe/screenscribe/discussions)

---

*This manual covers the complete screenscribe user experience. For the latest updates and features, see the project repository.*