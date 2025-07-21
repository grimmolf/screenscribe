"""CLI interface for screenscribe."""

import asyncio
import time
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from .models import ProcessingOptions, VideoMetadata
from .utils import setup_logging, check_dependencies, get_video_metadata, sanitize_filename
from .config import config

console = Console()
app = typer.Typer(help="Process videos and screen recordings to structured notes")


def validate_inputs(
    input_path: str,
    output_dir: Path,
    format: str,
    sampling_mode: str,
    whisper_model: str,
    llm_provider: str
) -> None:
    """Validate CLI inputs."""
    # Check format
    if format not in ["markdown", "html"]:
        console.print("❌ Error: format must be 'markdown' or 'html'", style="red")
        raise typer.Exit(1)
    
    # Check sampling mode
    if sampling_mode not in ["scene", "interval"]:
        console.print("❌ Error: sampling-mode must be 'scene' or 'interval'", style="red")
        raise typer.Exit(1)
    
    # Check if input is URL or local file
    if not input_path.startswith(("http://", "https://")):
        video_path = Path(input_path)
        if not video_path.exists():
            console.print(f"❌ Error: Video file not found: {video_path}", style="red")
            raise typer.Exit(1)
    
    # Check system dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        console.print(f"❌ Error: Missing dependencies: {', '.join(missing_deps)}", style="red")
        console.print("Please install missing dependencies and try again.", style="red")
        raise typer.Exit(1)
    
    # Check configuration
    config_errors = config.validate()
    if config_errors:
        console.print("❌ Configuration errors:", style="red")
        for error in config_errors:
            console.print(f"  - {error}", style="red")
        raise typer.Exit(1)


async def process_youtube(url: str, output_dir: Path, options: ProcessingOptions) -> None:
    """Process YouTube video."""
    import yt_dlp
    import tempfile
    
    console.print(f"📺 Downloading YouTube video: {url}")
    
    # Create temporary directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(temp_path / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                title = sanitize_filename(info.get('title', 'video'))
                
                # Download video
                ydl.download([url])
                
                # Find downloaded file
                downloaded_files = list(temp_path.glob('*'))
                if not downloaded_files:
                    raise RuntimeError("Failed to download video")
                
                video_path = downloaded_files[0]
                
                # Update options with YouTube metadata
                options.youtube_url = url
                
                # Process the downloaded video
                await process_local_file(video_path, output_dir, options, youtube_title=title, youtube_url=url)
                
        except Exception as e:
            console.print(f"❌ Error downloading YouTube video: {e}", style="red")
            raise typer.Exit(1)


async def process_local_file(
    video_path: Path, 
    output_dir: Path, 
    options: ProcessingOptions,
    youtube_title: Optional[str] = None,
    youtube_url: Optional[str] = None
) -> None:
    """Process local video file."""
    from .audio import AudioProcessor
    from .video import VideoProcessor
    from .align import TemporalAligner
    from .synthesis import ContentSynthesizer
    from .output import OutputGenerator
    
    start_time = time.time()
    
    try:
        # Step 1: Extract metadata
        console.print("📊 Extracting video metadata...")
        metadata_dict = get_video_metadata(video_path)
        
        # Use YouTube title if available
        if youtube_title:
            metadata_dict["title"] = youtube_title
        
        metadata = VideoMetadata(
            title=metadata_dict["title"],
            duration=metadata_dict["duration"],
            fps=metadata_dict["fps"],
            width=metadata_dict["width"],
            height=metadata_dict["height"],
            codec=metadata_dict["codec"],
            source_path=video_path,
            youtube_url=youtube_url
        )
        
        console.print(f"📹 Video: {metadata.title} ({metadata.duration_str})")
        
        # Initialize processors
        audio_processor = AudioProcessor(options.whisper_model, backend=options.whisper_backend)
        video_processor = VideoProcessor(
            options.sampling_mode,
            options.interval_seconds,
            options.scene_threshold
        )
        aligner = TemporalAligner()
        synthesizer = ContentSynthesizer(
            options.llm_provider,
            no_fallback=options.no_fallback,
            prompts_dir=options.prompts_dir
        )
        
        # Step 2: Extract and transcribe audio
        console.print("🎵 Extracting audio...")
        audio_path = await audio_processor.extract_audio(video_path, copy_from_nas=options.copy_from_nas)
        
        console.print("🎤 Transcribing audio...")
        transcript_data = audio_processor.transcribe(audio_path, language=None)
        
        # Save transcript
        transcript_file = output_dir / "transcript.json"
        import json
        transcript_file.write_text(json.dumps(transcript_data, indent=2))
        
        # Parse segments
        from .models import TranscriptSegment
        segments = [TranscriptSegment(**seg) for seg in transcript_data["segments"]]
        console.print(f"📝 Transcribed {len(segments)} segments")
        
        # Step 3: Extract frames
        console.print("🎬 Extracting frames...")
        if options.sampling_mode == "scene":
            frames = video_processor.extract_frames_scene(video_path, output_dir)
        else:
            frames = video_processor.extract_frames_interval(video_path, output_dir)
        
        console.print(f"📸 Extracted {len(frames)} frames")
        
        # Step 4: Align transcript with frames
        console.print("🔗 Aligning transcript with frames...")
        aligned = aligner.align(segments, frames)
        
        # Step 5: Synthesize content
        console.print("🤖 Synthesizing content...")
        synthesis_results = await synthesizer.synthesize_all(aligned)
        
        # Step 6: Generate output
        console.print("📝 Generating output...")
        from .models import ProcessingResult
        
        result = ProcessingResult(
            video_metadata=metadata,
            processing_options=options,
            transcript_segments=segments,
            frames=frames,
            aligned_content=aligned,
            synthesis_results=synthesis_results,
            output_file=output_dir / f"notes.{options.output_format}",
            processing_time=time.time() - start_time
        )
        
        output_gen = OutputGenerator(options.output_format)
        output_file = output_gen.generate(result, output_dir)
        
        # Clean up temp audio
        if audio_path.exists():
            audio_path.unlink()
        
        # Success message
        console.print(f"✅ Processing complete! Output saved to: {output_file}", style="green")
        console.print(f"⏱️  Processing time: {result.processing_time:.1f}s", style="blue")
        
    except Exception as e:
        console.print(f"❌ Error during processing: {e}", style="red")
        if options.verbose:
            import traceback
            console.print(traceback.format_exc(), style="red")
        raise typer.Exit(1)


@app.command()
def main(
    input: str = typer.Argument(..., help="Video file or YouTube URL"),
    output: Path = typer.Option("./screenscribe_output", "--output", "-o", help="Output directory"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format (markdown|html)"),
    llm: str = typer.Option("openai", "--llm", help="LLM provider"),
    no_fallback: bool = typer.Option(False, "--no-fallback", help="Disable LLM fallbacks"),
    whisper_model: str = typer.Option("medium", "--whisper-model", help="Whisper model size"),
    whisper_backend: Optional[str] = typer.Option(
        None,
        "--whisper-backend",
        help="Audio backend: mlx (Apple Silicon GPU), faster-whisper (universal), or auto"
    ),
    list_backends: bool = typer.Option(
        False,
        "--list-backends",
        help="List available audio backends and exit"
    ),
    sampling_mode: str = typer.Option("interval", "--sampling-mode", help="Frame sampling mode (interval|scene). Default optimized for educational content"),
    interval: float = typer.Option(45.0, "--interval", help="Interval for interval sampling (seconds). Default optimized for educational content"),
    scene_threshold: float = typer.Option(0.3, "--scene-threshold", help="Scene detection threshold"),
    prompts_dir: Optional[str] = typer.Option(None, "--prompts-dir", help="Custom directory for prompt templates"),
    copy_from_nas: bool = typer.Option(True, "--copy-from-nas/--no-copy-from-nas", help="Copy files from network storage locally for better performance"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Process video/audio to structured notes."""
    
    # Setup logging
    setup_logging(verbose)
    
    # Handle backend listing
    if list_backends:
        from .audio_backends import get_available_backends
        
        console.print("\n🔍 Available Audio Backends:", style="bold")
        for info in get_available_backends(whisper_model):
            status = "✅" if info.available else "❌"
            device_info = f"{info.device}"
            if info.compute_type:
                device_info += f" ({info.compute_type})"
            
            console.print(f"  {status} {info.name}: {device_info}")
            if info.reason and not info.available:
                console.print(f"     {info.reason}", style="dim")
        
        raise typer.Exit(0)
    
    # Validate backend choice
    if whisper_backend and whisper_backend not in ["mlx", "faster-whisper", "whisper-cpp", "auto"]:
        console.print(
            f"❌ Invalid backend '{whisper_backend}'. "
            f"Choose from: mlx, faster-whisper, auto",
            style="red"
        )
        raise typer.Exit(1)
    
    # Validate inputs
    validate_inputs(input, output, format, sampling_mode, whisper_model, llm)
    
    # Create output directory
    output.mkdir(parents=True, exist_ok=True)
    
    # Create processing options
    options = ProcessingOptions(
        output_dir=output,
        output_format=format,
        whisper_model=whisper_model,
        whisper_backend=whisper_backend if whisper_backend != "auto" else None,
        llm_provider=llm,
        no_fallback=no_fallback,
        sampling_mode=sampling_mode,
        interval_seconds=interval,
        scene_threshold=scene_threshold,
        prompts_dir=Path(prompts_dir) if prompts_dir else None,
        copy_from_nas=copy_from_nas,
        verbose=verbose
    )
    
    # Process based on input type
    if input.startswith(("http://", "https://")):
        asyncio.run(process_youtube(input, output, options))
    else:
        asyncio.run(process_local_file(Path(input), output, options))


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()