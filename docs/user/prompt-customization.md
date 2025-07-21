# Prompt Customization Guide

screenscribe uses Large Language Models (LLMs) to analyze video frames and synthesize content. You can customize these prompts to get better results for your specific content type.

> 📖 **For a complete guide** including usage, optimization, and integration, see the **[User Manual](../USER_MANUAL.md)** which consolidates all user guidance.

## Understanding Prompts

### What are Prompts?
Prompts are instructions given to the LLM that determine how it analyzes your video frames. They control:
- What the LLM focuses on (code, diagrams, text, etc.)
- How it describes visual elements
- What kind of insights it extracts
- The format of the output

### Default Behavior
By default, screenscribe uses a general-purpose prompt optimized for technical content that:
- Describes visual elements
- Correlates audio and visual information
- Extracts key technical points
- Generates structured JSON output

## Prompt System Architecture

### File Structure
Prompts are stored as markdown files in the `prompts/` directory:

```
prompts/
├── README.md           # Documentation
└── synthesis.md        # Main analysis prompt
```

### Template Variables
Prompts support these variables:
- `{timestamp_str}` - Frame timestamp (HH:MM:SS format)
- `{time_window}` - Time window for transcript alignment (seconds)
- `{transcript_text}` - Relevant transcript text for this frame

## Customization Methods

### Method 1: Edit Default Prompts (Easiest)

Simply edit the existing prompt file:

```bash
# Edit the default synthesis prompt
nano prompts/synthesis.md
```

Changes take effect immediately on the next run.

### Method 2: Custom Prompt Directory

Create your own prompt directory:

```bash
# Create custom prompts
mkdir my-custom-prompts
cp prompts/synthesis.md my-custom-prompts/

# Edit your custom version
nano my-custom-prompts/synthesis.md

# Use with screenscribe
screenscribe video.mp4 --prompts-dir my-custom-prompts/
```

### Method 3: Environment Variable

Set a global custom prompts directory:

```bash
export SCREENSCRIBE_PROMPTS_DIR=/path/to/custom/prompts
screenscribe video.mp4  # Will automatically use custom prompts
```

## Content-Specific Prompt Examples

### For Programming Tutorials

Create `prompts/synthesis-coding.md`:

```markdown
# Coding Tutorial Prompt

## Prompt Template

```
You are analyzing a programming tutorial video frame with its audio transcript.

Frame timestamp: {timestamp_str}
Transcript (±{time_window}s): "{transcript_text}"

Focus your analysis on:
1. Code snippets and syntax highlighting
2. IDE features and interface elements
3. Debugging information and error messages
4. File structures and project navigation
5. Terminal/console output

Provide response in this JSON format:
{{
  "summary": "Brief description of coding concept being demonstrated",
  "visual_description": "Detailed description of code, IDE, or terminal content",
  "key_points": ["specific coding concept 1", "syntax detail 2", "best practice 3"]
}}
```
```

### For Business Presentations

Create `prompts/synthesis-business.md`:

```markdown
# Business Presentation Prompt

## Prompt Template

```
You are analyzing a business presentation video frame with its audio transcript.

Frame timestamp: {timestamp_str}
Transcript (±{time_window}s): "{transcript_text}"

Focus your analysis on:
1. Slide titles and main headings
2. Charts, graphs, and data visualizations
3. Key metrics and business numbers
4. Strategic concepts and frameworks
5. Action items and recommendations

Provide response in this JSON format:
{{
  "summary": "Main business point or slide topic",
  "visual_description": "Description of slides, charts, or visual aids",
  "key_points": ["business insight 1", "metric 2", "recommendation 3"]
}}
```
```

### For Academic Lectures

Create `prompts/synthesis-academic.md`:

```markdown
# Academic Lecture Prompt

## Prompt Template

```
You are analyzing an academic lecture video frame with its transcript.

Frame timestamp: {timestamp_str}
Transcript (±{time_window}s): "{transcript_text}"

Focus your analysis on:
1. Theoretical concepts and definitions
2. Mathematical equations and formulas
3. Diagrams and conceptual models
4. References to academic literature
5. Examples and case studies

Provide response in this JSON format:
{{
  "summary": "Academic concept or theory being discussed",
  "visual_description": "Description of equations, diagrams, or academic content",
  "key_points": ["theoretical concept 1", "formula 2", "example 3"]
}}
```
```

## Advanced Prompt Engineering

### Adding Context Instructions

Include specific context about your content:

```markdown
You are analyzing a React.js tutorial video. Pay special attention to:
- JSX syntax and component structure
- Hook usage (useState, useEffect, etc.)
- Props and state management
- Component lifecycle methods
```

### Improving Output Quality

Add quality guidelines:

```markdown
Guidelines for high-quality analysis:
- Be specific about code concepts, don't use generic terms
- Identify specific UI components and their purposes
- Note any best practices or anti-patterns demonstrated
- Extract actionable insights the viewer can apply
```

### Handling Special Cases

Include instructions for edge cases:

```markdown
Special handling:
- If no code is visible, focus on speaker's verbal explanations
- For error screens, describe the error type and potential solutions
- For blank screens, note transition states or loading indicators
```

## Using Multiple Prompts

### Prompt Selection by Content Type

You can maintain different prompts for different video types:

```bash
# For coding content
screenscribe tutorial.mp4 --prompts-dir ./coding-prompts/

# For business content
screenscribe presentation.mp4 --prompts-dir ./business-prompts/

# For academic content
screenscribe lecture.mp4 --prompts-dir ./academic-prompts/
```

### Conditional Prompt Loading

Create a script to choose prompts automatically:

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
  *lecture*|*academic*|*university*)
    PROMPTS_DIR="./academic-prompts"
    ;;
  *)
    PROMPTS_DIR="./default-prompts"
    ;;
esac

screenscribe "$1" --prompts-dir "$PROMPTS_DIR" "${@:2}"
```

## Testing and Iteration

### Test Your Prompts

1. Start with a short test video (2-3 minutes)
2. Process with your custom prompt
3. Review the generated notes for quality
4. Iterate on the prompt based on results

### A/B Testing Prompts

Compare different prompt approaches:

```bash
# Test original prompt
screenscribe test-video.mp4 --output test-original/

# Test custom prompt
screenscribe test-video.mp4 --prompts-dir custom/ --output test-custom/

# Compare results
diff test-original/notes.md test-custom/notes.md
```

### Quality Metrics

Evaluate your prompts based on:
- **Accuracy**: How well does it describe what's actually shown?
- **Relevance**: Does it focus on the most important elements?
- **Consistency**: Does it maintain the same style across frames?
- **Actionability**: Are the insights useful for the viewer?

## Common Prompt Issues

### Problem: Generic Descriptions
**Solution**: Add specific vocabulary and examples to your prompt

### Problem: Missing Visual Details
**Solution**: Explicitly instruct the LLM to describe visual elements

### Problem: Inconsistent Output Format
**Solution**: Provide clear JSON schema with examples

### Problem: Irrelevant Focus
**Solution**: Add negative instructions ("Don't focus on...")

## Best Practices

### Do's
- ✅ Be specific about your content domain
- ✅ Provide clear output format specifications
- ✅ Include examples of good vs. bad outputs
- ✅ Test with representative content
- ✅ Iterate based on results

### Don'ts
- ❌ Don't make prompts too long (LLMs have limits)
- ❌ Don't change the JSON output format (breaks parsing)
- ❌ Don't remove template variables
- ❌ Don't forget to escape braces in the prompt `{{` `}}`

## Troubleshooting

### Prompt Not Loading
- Check file permissions and path
- Verify markdown format is correct
- Ensure template variables are present

### Poor Quality Output
- Add more specific instructions
- Include domain-specific vocabulary
- Provide examples in the prompt

### JSON Parsing Errors
- Verify the JSON format specification is clear
- Check for unescaped braces in the prompt
- Test the prompt with a simple example

## Next Steps

- **[📖 Complete User Manual](../USER_MANUAL.md)** - Comprehensive guide with usage, optimization, and integration examples
- **[Usage Guide](usage.md)** - Learn more about screenscribe options
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions  
- **[Real-World Examples](../examples/real-world-examples.md)** - See prompt customization in action