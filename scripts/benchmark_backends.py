#!/usr/bin/env python3
"""Benchmark script for audio transcription backends."""

import time
import statistics
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
import logging

# Import after path setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from screenscribe.audio_backends import get_available_backends, MLXWhisperBackend, FasterWhisperBackend

console = Console()
app = typer.Typer(help="Benchmark audio transcription backends")

# Setup logging to suppress backend noise during benchmarking
logging.getLogger().setLevel(logging.WARNING)


def format_time(seconds: float) -> str:
    """Format time in a human readable way."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}m {seconds:.1f}s"


def get_audio_duration(audio_path: Path) -> float:
    """Get audio file duration using ffprobe."""
    import subprocess
    import json
    
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        console.print(f"⚠️  Could not determine audio duration: {e}", style="yellow")
        return 0.0


@app.command()
def benchmark(
    audio_file: Path = typer.Argument(..., help="Path to audio file for benchmarking"),
    model: str = typer.Option("base", "--model", help="Whisper model to test"),
    runs: int = typer.Option(3, "--runs", help="Number of benchmark runs per backend"),
    backends: str = typer.Option("all", "--backends", help="Backends to test (all, mlx, faster-whisper)"),
    output: Path = typer.Option(None, "--output", help="Save results to JSON file")
):
    """Benchmark all available backends."""
    
    if not audio_file.exists():
        console.print(f"❌ Audio file not found: {audio_file}", style="red")
        raise typer.Exit(1)
    
    console.print(f"🎯 Benchmarking audio transcription backends", style="bold")
    console.print(f"📁 Audio file: {audio_file}")
    console.print(f"🎭 Model: {model}")
    console.print(f"🔄 Runs per backend: {runs}")
    
    # Get audio duration for performance calculations
    audio_duration = get_audio_duration(audio_file)
    if audio_duration > 0:
        console.print(f"⏱️  Audio duration: {format_time(audio_duration)}")
    
    # Get available backends
    available_backends = get_available_backends(model)
    
    # Filter backends based on selection
    if backends != "all":
        backend_names = [b.strip() for b in backends.split(",")]
        available_backends = [b for b in available_backends if b.name in backend_names]
    
    # Filter out unavailable backends
    available_backends = [b for b in available_backends if b.available]
    
    if not available_backends:
        console.print("❌ No available backends found", style="red")
        raise typer.Exit(1)
    
    console.print(f"\n🔍 Testing {len(available_backends)} backend(s):")
    for info in available_backends:
        device_info = f"{info.device}"
        if info.compute_type:
            device_info += f" ({info.compute_type})"
        console.print(f"  ✅ {info.name}: {device_info}")
    
    # Results storage
    benchmark_results = {
        "audio_file": str(audio_file),
        "audio_duration": audio_duration,
        "model": model,
        "runs": runs,
        "results": {}
    }
    
    # Create results table
    table = Table(title="Benchmark Results")
    table.add_column("Backend", style="cyan")
    table.add_column("Device", style="blue")
    table.add_column("Avg Time", style="green")
    table.add_column("Min Time", style="green")
    table.add_column("Max Time", style="green")
    table.add_column("Std Dev", style="yellow")
    if audio_duration > 0:
        table.add_column("RT Factor", style="magenta")
    table.add_column("Words/Min", style="white")
    
    console.print()
    
    # Benchmark each backend
    for info in available_backends:
        console.print(f"📊 Benchmarking {info.name} ({info.device})...")
        
        # Create backend instance
        if info.name == "mlx":
            backend = MLXWhisperBackend(model)
        else:
            backend = FasterWhisperBackend(model)
        
        if not backend.is_available():
            console.print(f"⏭️  Skipping {info.name} (not available)", style="yellow")
            continue
        
        # Run benchmarks
        times = []
        word_counts = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task(f"Running {runs} benchmark runs...", total=runs)
            
            for run in range(runs):
                try:
                    start_time = time.time()
                    result = backend.transcribe(audio_file)
                    elapsed = time.time() - start_time
                    
                    times.append(elapsed)
                    word_count = len(result.text.split())
                    word_counts.append(word_count)
                    
                    progress.update(task, advance=1)
                    console.print(f"  Run {run + 1}: {format_time(elapsed)} ({word_count} words)")
                    
                except Exception as e:
                    console.print(f"❌ Error in run {run + 1}: {e}", style="red")
                    continue
        
        if not times:
            console.print(f"❌ All runs failed for {info.name}", style="red")
            continue
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        avg_words = statistics.mean(word_counts) if word_counts else 0
        
        # Calculate real-time factor (processing_time / audio_duration)
        rt_factor = avg_time / audio_duration if audio_duration > 0 else 0
        
        # Calculate words per minute
        words_per_min = (avg_words / avg_time * 60) if avg_time > 0 else 0
        
        # Add to results
        benchmark_results["results"][info.name] = {
            "device": info.device,
            "compute_type": info.compute_type,
            "times": times,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "std_dev": std_dev,
            "rt_factor": rt_factor,
            "avg_words": avg_words,
            "words_per_min": words_per_min
        }
        
        # Add to table
        row = [
            info.name,
            f"{info.device} ({info.compute_type})" if info.compute_type else info.device,
            format_time(avg_time),
            format_time(min_time),
            format_time(max_time),
            f"{std_dev:.1f}s"
        ]
        
        if audio_duration > 0:
            row.append(f"{rt_factor:.2f}x")
        
        row.append(f"{words_per_min:.0f}")
        
        table.add_row(*row)
    
    console.print()
    console.print(table)
    
    # Performance analysis
    console.print("\n📈 Performance Analysis:", style="bold")
    
    if len(benchmark_results["results"]) > 1:
        # Find fastest backend
        fastest = min(benchmark_results["results"].items(), key=lambda x: x[1]["avg_time"])
        console.print(f"🥇 Fastest: {fastest[0]} ({format_time(fastest[1]['avg_time'])})")
        
        # Compare backends
        for name, result in benchmark_results["results"].items():
            if name != fastest[0]:
                speedup = result["avg_time"] / fastest[1]["avg_time"]
                console.print(f"   {name} is {speedup:.1f}x slower than {fastest[0]}")
    
    if audio_duration > 0:
        console.print(f"\n⏱️  Real-time Performance:")
        for name, result in benchmark_results["results"].items():
            rt_factor = result["rt_factor"]
            if rt_factor < 1.0:
                console.print(f"   {name}: {rt_factor:.2f}x (faster than real-time) ✨")
            else:
                console.print(f"   {name}: {rt_factor:.2f}x (slower than real-time)")
    
    # Memory and efficiency notes
    console.print(f"\n💡 Notes:", style="bold")
    console.print("• RT Factor < 1.0 means faster than real-time processing")
    console.print("• Lower RT Factor = better performance")
    console.print("• GPU backends typically use more memory but are faster")
    console.print("• CPU backends are more memory efficient but slower")
    
    # Save results to file if requested
    if output:
        import json
        with open(output, 'w') as f:
            json.dump(benchmark_results, f, indent=2)
        console.print(f"\n💾 Results saved to: {output}")


@app.command()
def compare(
    audio_file: Path = typer.Argument(..., help="Path to audio file for comparison"),
    model: str = typer.Option("base", "--model", help="Whisper model to test"),
):
    """Quick comparison of available backends."""
    
    if not audio_file.exists():
        console.print(f"❌ Audio file not found: {audio_file}", style="red")
        raise typer.Exit(1)
    
    console.print(f"🆚 Quick Backend Comparison", style="bold")
    console.print(f"📁 Audio file: {audio_file}")
    console.print(f"🎭 Model: {model}")
    
    # Get available backends
    available_backends = get_available_backends(model)
    available_backends = [b for b in available_backends if b.available]
    
    if not available_backends:
        console.print("❌ No available backends found", style="red")
        raise typer.Exit(1)
    
    console.print(f"\n🏃 Running single test on each backend...")
    
    results = []
    
    for info in available_backends:
        console.print(f"\n📊 Testing {info.name}...")
        
        # Create backend instance
        if info.name == "mlx":
            backend = MLXWhisperBackend(model)
        else:
            backend = FasterWhisperBackend(model)
        
        try:
            start_time = time.time()
            result = backend.transcribe(audio_file)
            elapsed = time.time() - start_time
            
            word_count = len(result.text.split())
            
            results.append({
                "name": info.name,
                "device": info.device,
                "time": elapsed,
                "words": word_count,
                "text": result.text[:100] + "..." if len(result.text) > 100 else result.text
            })
            
            console.print(f"✅ {info.name}: {format_time(elapsed)} ({word_count} words)")
            
        except Exception as e:
            console.print(f"❌ {info.name} failed: {e}", style="red")
    
    if len(results) > 1:
        # Quick comparison
        fastest = min(results, key=lambda x: x["time"])
        console.print(f"\n🏆 Winner: {fastest['name']} ({format_time(fastest['time'])})")
    
    # Show text comparison
    console.print(f"\n📝 Transcription Preview:")
    for result in results:
        console.print(f"\n{result['name']}: \"{result['text']}\"", style="dim")


if __name__ == "__main__":
    app()