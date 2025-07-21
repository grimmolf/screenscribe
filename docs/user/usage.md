# Usage Guide

This guide covers everything you need to know about using screenscribe effectively.

> 📖 **For the complete user experience**, see the **[User Manual](../USER_MANUAL.md)** which consolidates all user guidance, including advanced prompt customization, content optimization, and integration examples.

## Basic Usage

### Processing a Local Video

The simplest way to use screenscribe:

```bash
screenscribe video.mp4
```

This will:
- Process `video.mp4` using default settings
- Create output in `./screenscribe_output/` directory
- Generate Markdown notes with embedded thumbnails

### Processing a YouTube Video

screenscribe can directly process YouTube videos:

```bash
screenscribe "https://www.youtube.com/watch?v=VIDEO_ID"
```

The video will be downloaded temporarily and processed.

### Specifying Output Directory

Choose where to save your notes:

```bash
screenscribe video.mp4 --output ~/Documents/notes/
```

## Command-Line Options

### Core Options

**Input and Output:**
- `input` - Video file path or YouTube URL (required)
- `--output`, `-o` - Output directory (default: `./screenscribe_output`)
- `--format`, `-f` - Output format: `markdown` or `html` (default: `markdown`)

**Processing Options:**
- `--whisper-model` - Transcription accuracy: `tiny`, `base`, `small`, `medium`, `large` (default: `medium`)
- `--sampling-mode` - Frame extraction: `scene` or `interval` (default: `scene`)
- `--interval` - Seconds between frames for interval mode (default: `5.0`)
- `--scene-threshold` - Scene change sensitivity: 0.1 (sensitive) to 1.0 (less sensitive) (default: `0.3`)

**LLM Options:**
- `--llm` - LLM provider: `openai` or `anthropic` (default: `openai`)
- `--no-fallback` - Disable automatic fallback to backup LLM providers
- `--prompts-dir` - Custom directory for prompt templates

**Other:**
- `--verbose`, `-v` - Show detailed processing information

### Examples by Use Case

#### Technical Tutorials
For coding tutorials or technical presentations:

```bash
screenscribe tutorial.mp4 \
  --output ./tutorial-notes/ \
  --whisper-model large \
  --sampling-mode scene \
  --scene-threshold 0.2
```

- `large` model for accurate technical terminology
- `scene` mode captures slide changes
- Lower threshold (0.2) catches subtle transitions

#### Presentations and Slides
For slide-based content:

```bash
screenscribe presentation.mp4 \
  --format html \
  --sampling-mode scene \
  --scene-threshold 0.4
```

- HTML format for better presentation
- Scene mode perfect for slide changes
- Higher threshold (0.4) ignores minor movements

#### Interviews and Discussions
For talking-head style content:

```bash
screenscribe interview.mp4 \
  --sampling-mode interval \
  --interval 30 \
  --whisper-model medium
```

- Interval mode since visual changes are minimal
- 30-second intervals capture key moments
- Medium model sufficient for clear speech

#### Long-Form Content
For lengthy videos (>30 minutes):

```bash
screenscribe long-video.mp4 \
  --whisper-model base \
  --sampling-mode interval \
  --interval 60 \
  --output ./long-form-notes/
```

- Faster `base` model for efficiency
- 60-second intervals reduce processing time
- Separate output directory for organization

## Understanding the Output

### Generated Files

When screenscribe finishes processing, you'll find:

```
screenscribe_output/
├── notes.md                    # Main structured notes
├── notes.html                  # HTML version (if requested)
├── transcript.json             # Raw transcription data
├── processing_result.json      # Complete metadata
├── frames/                     # Extracted video frames
│   ├── frame_0000.jpg
│   ├── frame_0001.jpg
│   └── ...
└── thumbnails/                 # Resized thumbnails
    ├── thumb_frame_0000.jpg
    ├── thumb_frame_0001.jpg
    └── ...
```

### Notes Structure

The generated notes follow this structure:

**Header Section:**
- Video title and metadata
- Processing information
- Duration and technical details

**Timeline Section:**
- Chronologically ordered frames
- Each entry contains:
  - Timestamp and thumbnail
  - Transcript excerpt
  - Visual description
  - Key points extracted
  - Summary synthesis

**Example Note Entry:**
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

## Performance Optimization

### Speed vs. Quality Trade-offs

**Fastest Processing:**
```bash
screenscribe video.mp4 \
  --whisper-model tiny \
  --sampling-mode interval \
  --interval 10
```

**Best Quality:**
```bash
screenscribe video.mp4 \
  --whisper-model large \
  --sampling-mode scene \
  --scene-threshold 0.1
```

**Balanced (Recommended):**
```bash
screenscribe video.mp4 \
  --whisper-model medium \
  --sampling-mode scene
```

### Resource Management

**For Limited Memory:**
- Use smaller Whisper models (`tiny`, `base`, `small`)
- Increase interval time for interval sampling
- Process shorter video segments

**For Limited API Credits:**
- Use higher scene thresholds (fewer frames)
- Use interval sampling with larger intervals
- Enable `--no-fallback` to prevent backup API calls

## Working with Different Content Types

### Code Demonstrations
```bash
screenscribe coding-tutorial.mp4 \
  --whisper-model large \
  --sampling-mode scene \
  --scene-threshold 0.15
```

### Academic Lectures
```bash
screenscribe lecture.mp4 \
  --sampling-mode interval \
  --interval 45 \
  --whisper-model medium
```

### Product Demos
```bash
screenscribe product-demo.mp4 \
  --sampling-mode scene \
  --scene-threshold 0.25 \
  --format html
```

### Meeting Recordings
```bash
screenscribe meeting.mp4 \
  --sampling-mode interval \
  --interval 120 \
  --whisper-model base
```

## Advanced Usage

### Custom Prompts
See [Prompt Customization Guide](prompt-customization.md) for details on customizing LLM behavior.

### Batch Processing
Process multiple videos:

```bash
# Process all MP4 files in a directory
for video in *.mp4; do
    screenscribe "$video" --output "notes/${video%.mp4}"
done
```

### Environment Variables
Set default configurations:

```bash
export SCREENSCRIBE_PROMPTS_DIR=/path/to/custom/prompts
export OPENAI_API_KEY=your-api-key
export ANTHROPIC_API_KEY=your-backup-key
```

## Integration with Other Tools

### With Obsidian
Generated markdown files work perfectly with Obsidian:

1. Process videos into your Obsidian vault:
   ```bash
   screenscribe video.mp4 --output ~/ObsidianVault/Videos/
   ```

2. Images are properly linked and will display in Obsidian

### With Notion
Convert to Notion-compatible format:

1. Generate HTML output:
   ```bash
   screenscribe video.mp4 --format html
   ```

2. Import the HTML file into Notion

### With Jupyter Notebooks
Embed processing results in notebooks:

```python
# Display results in Jupyter
from IPython.display import Markdown, display
with open('screenscribe_output/notes.md', 'r') as f:
    display(Markdown(f.read()))
```

## Next Steps

- **[📖 Complete User Manual](../USER_MANUAL.md)** - Comprehensive guide with prompt customization, optimization, and integration examples
- **[Prompt Customization](prompt-customization.md)** - Detailed prompt engineering guide
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions  
- **[Real-World Examples](../examples/real-world-examples.md)** - See screenscribe in action