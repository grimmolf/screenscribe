# Screenscribe Prompts

This directory contains the prompt templates used by screenscribe for LLM-based content synthesis. These prompts are stored as markdown files to make them easily editable and version-controllable.

## Available Prompts

### synthesis.md
The main prompt used to analyze video frames with their corresponding audio transcripts. This prompt instructs the LLM to:
- Describe visual content
- Correlate visual and audio information
- Extract key technical points
- Generate structured JSON output

## Using Custom Prompts

### Method 1: Edit Default Prompts
Simply edit the `.md` files in this directory. Changes will be automatically loaded on the next run.

### Method 2: Custom Prompt Directory
Use the `--prompts-dir` CLI option to specify a custom directory:

```bash
screenscribe video.mp4 --prompts-dir ./my-custom-prompts/
```

### Method 3: Environment Variable
Set the `SCREENSCRIBE_PROMPTS_DIR` environment variable:

```bash
export SCREENSCRIBE_PROMPTS_DIR=/path/to/custom/prompts
screenscribe video.mp4
```

## Prompt Variables

Prompts can use template variables that are automatically replaced:

- `{timestamp_str}`: Frame timestamp (HH:MM:SS format)
- `{time_window}`: Time window for transcript alignment (seconds)
- `{transcript_text}`: Relevant transcript text for this frame

## Creating Custom Prompts

1. Copy the default `synthesis.md` as a starting point
2. Modify the prompt text while keeping the same structure
3. Maintain the JSON output format specification
4. Use the available template variables as needed

## Prompt Engineering Tips

### For Better Accuracy
- Be specific about the type of content (technical, educational, presentation)
- Include examples of desired output format
- Specify what to focus on (code, diagrams, UI elements)

### For Consistency
- Keep the JSON output format unchanged
- Use consistent terminology throughout prompts
- Maintain the same level of detail expectations

### For Different Content Types
Create specialized prompts for different video types:
- `synthesis-tutorial.md`: For tutorial and how-to videos
- `synthesis-presentation.md`: For slides and presentations
- `synthesis-code.md`: For coding demonstrations

## Troubleshooting

### Prompt Not Loading
- Check file permissions (must be readable)
- Verify the file is valid markdown
- Ensure the prompt directory path is correct

### Poor Output Quality
- Add more specific instructions
- Include examples of good vs. bad outputs
- Adjust the prompt for your specific content type

### JSON Format Errors
- Ensure the JSON format specification is clear
- Add examples of the expected JSON structure
- Consider adding format validation instructions