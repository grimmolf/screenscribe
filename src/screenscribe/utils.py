"""Utility functions for screenscribe."""

import logging
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
import subprocess
import shutil


console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    return shutil.which('ffmpeg') is not None


def check_dependencies() -> list[str]:
    """Check system dependencies and return list of missing ones."""
    missing = []
    
    if not check_ffmpeg():
        missing.append("ffmpeg")
    
    return missing


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for cross-platform compatibility."""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing periods and spaces
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized


def get_video_metadata(video_path: Path) -> dict:
    """Extract video metadata using ffprobe."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        metadata = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in metadata.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        format_info = metadata.get("format", {})
        
        return {
            "title": format_info.get("tags", {}).get("title", video_path.stem),
            "duration": float(format_info.get("duration", 0)),
            "fps": eval(video_stream.get("r_frame_rate", "30/1")),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "codec": video_stream.get("codec_name", "unknown")
        }
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to extract video metadata: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse ffprobe output: {e}")


def create_progress_bar(description: str) -> Progress:
    """Create a standardized progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    )


def load_prompt_template(prompt_name: str, prompts_dir: Optional[Path] = None) -> str:
    """
    Load a prompt template from markdown file.
    
    Args:
        prompt_name: Name of the prompt (without .md extension)
        prompts_dir: Custom prompts directory (optional)
        
    Returns:
        The prompt template content
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
        RuntimeError: If prompt file is invalid
    """
    if prompts_dir is None:
        # Use default prompts directory relative to the package
        package_dir = Path(__file__).parent.parent.parent
        prompts_dir = package_dir / "prompts"
    
    prompt_file = prompts_dir / f"{prompt_name}.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    try:
        content = prompt_file.read_text(encoding="utf-8")
        
        # Extract the actual prompt from markdown
        # Look for the prompt template section
        lines = content.split('\n')
        in_prompt_block = False
        prompt_lines = []
        
        for line in lines:
            if line.strip() == "```" and in_prompt_block:
                break
            elif line.strip() == "```" and not in_prompt_block:
                in_prompt_block = True
            elif in_prompt_block:
                prompt_lines.append(line)
        
        if not prompt_lines:
            raise RuntimeError(f"No prompt template found in {prompt_file}")
        
        return '\n'.join(prompt_lines)
        
    except Exception as e:
        raise RuntimeError(f"Failed to load prompt from {prompt_file}: {e}")


def format_prompt_template(template: str, **kwargs) -> str:
    """
    Format a prompt template with variables.
    
    Args:
        template: The prompt template string
        **kwargs: Variables to substitute in the template
        
    Returns:
        Formatted prompt string
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise RuntimeError(f"Missing template variable: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to format prompt template: {e}")