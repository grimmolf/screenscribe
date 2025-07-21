# Video Frame Synthesis Prompt

## Description
This prompt is used to analyze video frames with their corresponding audio transcripts and generate structured summaries that combine both visual and auditory information.

## Variables Available
- `{timestamp_str}`: Formatted timestamp (HH:MM:SS) of the current frame
- `{time_window}`: Time window in seconds used for transcript alignment  
- `{transcript_text}`: Transcript text from segments near this frame timestamp

## Prompt Template

```
You are analyzing a technical video frame with its corresponding audio transcript.

Frame timestamp: {timestamp_str}
Transcript (±{time_window}s): "{transcript_text}"

Analyze this frame and create a structured summary that:
1. Describes what is visually shown
2. Explains how it relates to what is being said
3. Extracts key technical points or concepts
4. Notes any important visual elements (diagrams, code, charts)

Provide response in this JSON format:
{{
  "summary": "Brief synthesis of audio and visual content",
  "visual_description": "What is shown in the frame",
  "key_points": ["point 1", "point 2", ...]
}}
```

## Customization Tips

### For Technical Content
- Focus on code snippets, diagrams, and technical terminology
- Emphasize visual-audio correlation for complex concepts
- Extract actionable insights and key learning points

### For Presentation Content
- Highlight slide titles, bullet points, and visual aids
- Connect speaker's points to visual elements
- Summarize main ideas and supporting evidence

### For Tutorial Content  
- Emphasize step-by-step instructions
- Note UI elements, buttons, and navigation
- Connect spoken instructions to visual demonstrations

## Output Format
The prompt expects JSON output with three fields:
- **summary**: Concise synthesis of visual and audio content
- **visual_description**: Detailed description of what's shown in the frame
- **key_points**: Array of important points or insights (optional)