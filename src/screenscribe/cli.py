"""CLI interface for screenscribe."""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from .models import ProcessingOptions, VideoMetadata
from .utils import setup_logging, check_dependencies, get_video_metadata, sanitize_filename
from .config import config
from .config_enhanced import enhanced_config
from .updater import check_for_updates, update_screenscribe

console = Console()
app = typer.Typer(help="Process videos and screen recordings to structured notes")
config_app = typer.Typer(help="Configuration management")
update_app = typer.Typer(help="Update management")

# Add sub-commands
app.add_typer(config_app, name="config")
app.add_typer(update_app, name="update")


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
    """Process YouTube video with enhanced transcript support."""
    from .youtube_enhanced import YouTubeProcessor
    import tempfile
    
    console.print(f"📺 Processing YouTube video: {url}")
    
    # Initialize YouTube processor
    yt_processor = YouTubeProcessor(
        prefer_youtube_transcripts=getattr(options, 'use_youtube_transcripts', enhanced_config.config.prefer_youtube_transcripts)
    )
    
    # Extract video ID for transcript processing
    video_id = yt_processor.extract_video_id(url)
    
    # Try to get YouTube transcript first if enabled
    transcript_result = None
    transcript_source = None
    
    if getattr(options, 'use_youtube_transcripts', enhanced_config.config.prefer_youtube_transcripts) and video_id:
        console.print("🎯 Checking for YouTube transcripts...")
        try:
            transcript_data = await yt_processor.get_youtube_transcript(video_id)
            if transcript_data:
                transcript_result, transcript_source = transcript_data
                console.print(f"✅ Found {transcript_source.source} transcript: {transcript_source.segment_count} segments", style="green")
        except Exception as e:
            console.print(f"⚠️ YouTube transcript extraction failed: {e}", style="yellow")
    
    # Create temporary directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        console.print("📥 Downloading video file...")
        try:
            # Download video using enhanced processor
            video_path, video_info = await yt_processor.download_video(
                url, temp_path, enhanced_config.config.yt_dlp_format
            )
            
            title = sanitize_filename(video_info.get('title', 'video'))
            
            # Update options with YouTube metadata
            options.youtube_url = url
            
            # Process the downloaded video (with potential transcript override)
            await process_local_file(
                video_path, output_dir, options, 
                youtube_title=title, 
                youtube_url=url,
                youtube_transcript=transcript_result,
                transcript_source=transcript_source
            )
                
        except Exception as e:
            console.print(f"❌ Error processing YouTube video: {e}", style="red")
            if options.verbose:
                import traceback
                console.print(traceback.format_exc(), style="red")
            raise typer.Exit(1)


async def process_local_file(
    video_path: Path, 
    output_dir: Path, 
    options: ProcessingOptions,
    youtube_title: Optional[str] = None,
    youtube_url: Optional[str] = None,
    youtube_transcript = None,
    transcript_source = None
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
        
        # Step 2: Handle transcription (YouTube transcript or Whisper)
        if youtube_transcript and transcript_source:
            console.print(f"📝 Using {transcript_source.source} transcript ({transcript_source.segment_count} segments)", style="blue")
            
            # Convert to expected format for compatibility
            transcript_data = {
                "text": youtube_transcript.text,
                "segments": [segment.model_dump() for segment in youtube_transcript.segments],
                "source": transcript_source.source,
                "confidence": transcript_source.confidence
            }
            
            segments = youtube_transcript.segments
            
        else:
            # Fallback to Whisper transcription
            console.print("🎵 Extracting audio...")
            audio_path = await audio_processor.extract_audio(video_path, copy_from_nas=options.copy_from_nas)
            
            console.print("🎤 Transcribing audio with Whisper...")
            transcript_data = audio_processor.transcribe(audio_path, language=None)
            
            # Parse segments
            from .models import TranscriptSegment
            segments = [TranscriptSegment(**seg) for seg in transcript_data["segments"]]
            
            # Clean up temp audio
            if audio_path.exists():
                audio_path.unlink()
        
        # Save transcript
        transcript_file = output_dir / "transcript.json"
        transcript_file.write_text(json.dumps(transcript_data, indent=2))
        
        console.print(f"📝 Using transcript with {len(segments)} segments")
        
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
        
        # Note: Audio cleanup now handled in transcription section
        
        # Success message
        console.print(f"✅ Processing complete! Output saved to: {output_file}", style="green")
        console.print(f"⏱️  Processing time: {result.processing_time:.1f}s", style="blue")
        
    except Exception as e:
        console.print(f"❌ Error during processing: {e}", style="red")
        if options.verbose:
            import traceback
            console.print(traceback.format_exc(), style="red")
        raise typer.Exit(1)


@app.command(name="process")
def process_command(
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
    prompts_dir: Optional[str] = typer.Option(None, "--prompts-dir", help="Custom directory for prompt templates (defaults to ~/.config/screenscribe/prompts/)"),
    use_youtube_transcripts: bool = typer.Option(True, "--use-youtube-transcripts/--no-youtube-transcripts", help="Use YouTube's built-in transcripts when available"),
    transcript_file: Optional[str] = typer.Option(None, "--transcript-file", help="External transcript file (JSON, SRT, VTT, or plain text)"),
    llm_endpoint: Optional[str] = typer.Option(None, "--llm-endpoint", help="LLM endpoint name from config (overrides --llm)"),
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
    
    # Use enhanced config for better defaults
    if not prompts_dir:
        prompts_dir = enhanced_config.config.global_prompts_dir
        
    if llm_endpoint:
        # Override LLM provider with endpoint from config
        endpoint = enhanced_config.get_llm_endpoint(llm_endpoint)
        if endpoint:
            llm = endpoint.provider
        else:
            console.print(f"❌ LLM endpoint '{llm_endpoint}' not found in config", style="red")
            raise typer.Exit(1)
    
    # Validate inputs
    validate_inputs(input, output, format, sampling_mode, whisper_model, llm)
    
    # Validate enhanced config
    config_errors = enhanced_config.validate()
    if config_errors:
        console.print("❌ Configuration errors:", style="red")
        for error in config_errors:
            console.print(f"  - {error}", style="red")
        raise typer.Exit(1)
    
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
    
    # Add enhanced processing options attributes
    options.use_youtube_transcripts = use_youtube_transcripts
    options.transcript_file = transcript_file
    options.llm_endpoint = llm_endpoint
    
    # Process based on input type
    if input.startswith(("http://", "https://")):
        asyncio.run(process_youtube(input, output, options))
    else:
        asyncio.run(process_local_file(Path(input), output, options))


@config_app.command("show")
def show_config():
    """Show current configuration."""
    config_data = enhanced_config.config
    
    console.print("\n🔧 Screenscribe Configuration", style="bold")
    
    # LLM Endpoints
    console.print("\n📡 LLM Endpoints:", style="bold blue")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Status")
    
    for endpoint in config_data.llm_endpoints:
        status = "✅ Enabled" if endpoint.enabled else "❌ Disabled"
        if not endpoint.api_key:
            status = "⚠️ No API Key"
        table.add_row(
            endpoint.name,
            endpoint.provider,
            endpoint.model or "default",
            status
        )
    console.print(table)
    
    # Directories
    console.print("\n📁 Directories:", style="bold blue")
    console.print(f"  Prompts: {config_data.global_prompts_dir}")
    console.print(f"  Output: {config_data.output_base_dir}")
    console.print(f"  Whisper Cache: {config_data.whisper_cache_dir}")
    
    # Processing Defaults
    console.print("\n⚙️ Processing Defaults:", style="bold blue")
    console.print(f"  Sampling Mode: {config_data.default_sampling_mode}")
    console.print(f"  Interval: {config_data.default_interval_seconds}s")
    console.print(f"  Scene Threshold: {config_data.default_scene_threshold}")
    console.print(f"  Whisper Model: {config_data.default_whisper_model}")
    console.print(f"  Whisper Backend: {config_data.default_whisper_backend}")
    
    # YouTube Settings
    console.print("\n📺 YouTube Settings:", style="bold blue")
    console.print(f"  Prefer YouTube Transcripts: {config_data.prefer_youtube_transcripts}")
    console.print(f"  Download Format: {config_data.yt_dlp_format}")
    
    # Update Settings
    console.print("\n🔄 Update Settings:", style="bold blue")
    console.print(f"  Auto Check Updates: {config_data.auto_check_updates}")
    console.print(f"  GitHub Repo: {config_data.github_repo}")


@config_app.command("init")
def init_config():
    """Initialize default configuration."""
    from .config_enhanced import setup_global_directories
    
    console.print("🔧 Initializing screenscribe configuration...")
    
    # Setup directories and save config
    setup_global_directories(enhanced_config.config)
    enhanced_config.save()
    
    console.print("✅ Configuration initialized!", style="green")
    console.print(f"📁 Config file: {enhanced_config.config.global_prompts_dir}/../config.json")
    console.print(f"📁 Prompts directory: {enhanced_config.config.global_prompts_dir}")
    console.print(f"📁 Output directory: {enhanced_config.config.output_base_dir}")
    
    console.print("\n💡 Next steps:")
    console.print("  - Edit config.json to add your API keys")
    console.print("  - Customize prompts in the prompts/ directory")
    console.print("  - Run 'screenscribe config show' to view current settings")


@config_app.command("validate")
def validate_config():
    """Validate current configuration."""
    console.print("🔍 Validating configuration...")
    
    errors = enhanced_config.validate()
    
    if not errors:
        console.print("✅ Configuration is valid!", style="green")
    else:
        console.print("❌ Configuration errors found:", style="red")
        for error in errors:
            console.print(f"  - {error}", style="red")
        raise typer.Exit(1)


@update_app.command("check")
def check_update():
    """Check for available updates."""
    console.print("🔍 Checking for updates...")
    
    try:
        info = check_for_updates(enhanced_config.config.github_repo)
        
        console.print(f"\n📦 Current Version: {info['current_version'] or 'Unknown'}")
        console.print(f"📦 Latest Version: {info['latest_version'] or 'Unknown'}")
        
        if info['has_update']:
            console.print("🆕 Update available!", style="green bold")
            if info.get('release_date'):
                console.print(f"📅 Released: {info['release_date']}")
            if info.get('release_notes'):
                console.print(f"📝 Release Notes: {info['release_url']}")
        else:
            console.print("✅ You're up to date!", style="blue")
        
        # Show latest commit info
        if info.get('latest_commit'):
            commit = info['latest_commit']
            console.print(f"\n🔄 Latest Commit: {commit['sha']}")
            console.print(f"💬 {commit['message']}")
            console.print(f"📅 {commit['date']}")
            
    except Exception as e:
        console.print(f"❌ Error checking for updates: {e}", style="red")
        raise typer.Exit(1)


@update_app.command("install")
def install_update(
    dev: bool = typer.Option(False, "--dev", help="Install latest development version instead of release")
):
    """Install the latest update."""
    repo = enhanced_config.config.github_repo
    
    if dev:
        console.print(f"🔄 Installing latest development version from {repo}...")
        success = update_screenscribe(repo, to_latest=False)
    else:
        console.print(f"🔄 Installing latest release from {repo}...")
        success = update_screenscribe(repo, to_latest=True)
    
    if success:
        console.print("✅ Update installed successfully!", style="green")
        console.print("🔄 You may need to restart your terminal session.")
    else:
        console.print("❌ Update failed. Check logs for details.", style="red")
        raise typer.Exit(1)


# Make the process command the default
@app.callback(invoke_without_command=True)
def default_command(
    ctx: typer.Context,
    input: Optional[str] = typer.Argument(None, help="Video file or YouTube URL"),
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
    prompts_dir: Optional[str] = typer.Option(None, "--prompts-dir", help="Custom directory for prompt templates (defaults to ~/.config/screenscribe/prompts/)"),
    use_youtube_transcripts: bool = typer.Option(True, "--use-youtube-transcripts/--no-youtube-transcripts", help="Use YouTube's built-in transcripts when available"),
    transcript_file: Optional[str] = typer.Option(None, "--transcript-file", help="External transcript file (JSON, SRT, VTT, or plain text)"),
    llm_endpoint: Optional[str] = typer.Option(None, "--llm-endpoint", help="LLM endpoint name from config (overrides --llm)"),
    copy_from_nas: bool = typer.Option(True, "--copy-from-nas/--no-copy-from-nas", help="Copy files from network storage locally for better performance"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Process video/audio to structured notes (default command)."""
    
    # If no subcommand and no input provided, show help
    if ctx.invoked_subcommand is None:
        if input is None:
            console.print(ctx.get_help())
            return
        
        # Call the processing function with all parameters
        # Handle external transcript file if provided
        if transcript_file:
            transcript_path = Path(transcript_file)
            if not transcript_path.exists():
                console.print(f"❌ Transcript file not found: {transcript_file}", style="red")
                raise typer.Exit(1)
            
            console.print(f"📄 Loading external transcript: {transcript_file}")
            # Process with external transcript (implementation needed in process_with_external_transcript)
            process_with_external_transcript(
                input=input,
                output=output,
                transcript_path=transcript_path,
                format=format,
                llm=llm,
                no_fallback=no_fallback,
                whisper_model=whisper_model,
                whisper_backend=whisper_backend,
                sampling_mode=sampling_mode,
                interval=interval,
                scene_threshold=scene_threshold,
                prompts_dir=prompts_dir,
                llm_endpoint=llm_endpoint,
                copy_from_nas=copy_from_nas,
                verbose=verbose
            )
            return
        
        # Regular processing
        process_command(
            input=input,
            output=output,
            format=format,
            llm=llm,
            no_fallback=no_fallback,
            whisper_model=whisper_model,
            whisper_backend=whisper_backend,
            list_backends=list_backends,
            sampling_mode=sampling_mode,
            interval=interval,
            scene_threshold=scene_threshold,
            prompts_dir=prompts_dir,
            use_youtube_transcripts=use_youtube_transcripts,
            transcript_file=transcript_file,
            llm_endpoint=llm_endpoint,
            copy_from_nas=copy_from_nas,
            verbose=verbose
        )


def process_with_external_transcript(
    input: str,
    output: Path,
    transcript_path: Path,
    format: str,
    llm: str,
    no_fallback: bool,
    whisper_model: str,
    whisper_backend: Optional[str],
    sampling_mode: str,
    interval: float,
    scene_threshold: float,
    prompts_dir: Optional[str],
    llm_endpoint: Optional[str],
    copy_from_nas: bool,
    verbose: bool
):
    """Process video with external transcript file."""
    from .youtube_enhanced import YouTubeProcessor
    
    console.print(f"📄 Processing with external transcript: {transcript_path}")
    
    # Load external transcript
    yt_processor = YouTubeProcessor()
    transcript_result = None
    transcript_source = None
    
    try:
        transcript_data = asyncio.run(yt_processor.load_external_transcript(transcript_path))
        if transcript_data:
            transcript_result, transcript_source = transcript_data
            console.print(f"✅ Loaded external transcript: {transcript_source.segment_count} segments", style="green")
    except Exception as e:
        console.print(f"❌ Error loading external transcript: {e}", style="red")
        raise typer.Exit(1)
    
    # Use enhanced config for better defaults
    if not prompts_dir:
        prompts_dir = enhanced_config.config.global_prompts_dir
        
    if llm_endpoint:
        # Override LLM provider with endpoint from config
        endpoint = enhanced_config.get_llm_endpoint(llm_endpoint)
        if endpoint:
            llm = endpoint.provider
        else:
            console.print(f"❌ LLM endpoint '{llm_endpoint}' not found in config", style="red")
            raise typer.Exit(1)
    
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
        # YouTube URL with external transcript
        asyncio.run(process_youtube_with_transcript(input, output, options, transcript_result, transcript_source))
    else:
        # Local file with external transcript
        video_path = Path(input)
        if not video_path.exists():
            console.print(f"❌ Video file not found: {video_path}", style="red")
            raise typer.Exit(1)
            
        asyncio.run(process_local_file(
            video_path, output, options,
            youtube_transcript=transcript_result,
            transcript_source=transcript_source
        ))


async def process_youtube_with_transcript(url: str, output_dir: Path, options: ProcessingOptions, transcript_result, transcript_source) -> None:
    """Process YouTube video with pre-loaded external transcript."""
    from .youtube_enhanced import YouTubeProcessor
    import tempfile
    
    console.print(f"📺 Processing YouTube video with external transcript: {url}")
    
    # Initialize YouTube processor (transcripts disabled since we have external)
    yt_processor = YouTubeProcessor(prefer_youtube_transcripts=False)
    
    # Create temporary directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        console.print("📥 Downloading video file...")
        try:
            # Download video using enhanced processor
            video_path, video_info = await yt_processor.download_video(
                url, temp_path, enhanced_config.config.yt_dlp_format
            )
            
            title = sanitize_filename(video_info.get('title', 'video'))
            
            # Update options with YouTube metadata
            options.youtube_url = url
            
            # Process the downloaded video with external transcript
            await process_local_file(
                video_path, output_dir, options, 
                youtube_title=title, 
                youtube_url=url,
                youtube_transcript=transcript_result,
                transcript_source=transcript_source
            )
                
        except Exception as e:
            console.print(f"❌ Error processing YouTube video: {e}", style="red")
            if options.verbose:
                import traceback
                console.print(traceback.format_exc(), style="red")
            raise typer.Exit(1)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()