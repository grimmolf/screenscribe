#!/usr/bin/env python3
"""
Predownload MLX Whisper models for offline use
Ensures all models are cached locally for reliable Apple Silicon performance
"""

import sys
import os
from pathlib import Path

def predownload_mlx_models():
    """Predownload all MLX Whisper models to local cache"""
    try:
        import mlx_whisper
        print("🍎 MLX Whisper detected - predownloading models for Apple Silicon...")
    except ImportError:
        print("❌ MLX Whisper not available. Install with: pip install mlx-whisper")
        return False
    
    # MLX model repository mapping
    mlx_models = {
        "tiny": "mlx-community/whisper-tiny",
        "base": "mlx-community/whisper-base",
        "small": "mlx-community/whisper-small",
        "medium": "mlx-community/whisper-medium",
        "large-v2": "mlx-community/whisper-large-v2",
        "large-v3": "mlx-community/whisper-large-v3"
    }
    
    print("📥 Predownloading MLX Whisper models...")
    print("This may take several minutes for larger models...")
    
    # Create a single test audio file for all models
    import tempfile
    import subprocess
    
    # Create 1-second silent audio file for testing
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_audio = f.name
        
    try:
        # Generate silent audio with ffmpeg
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=16000:d=1",
            "-y", temp_audio
        ], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to create test audio file. Is ffmpeg installed?")
        return False
    
    success_count = 0
    for model_name, model_repo in mlx_models.items():
        try:
            print(f"  📦 Downloading {model_name} ({model_repo})...")
            
            # This will download and cache the model
            _ = mlx_whisper.transcribe(temp_audio, path_or_hf_repo=model_repo, verbose=False)
            
            print(f"  ✅ {model_name} downloaded successfully")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to download {model_name}: {e}")
            continue
    
    # Clean up test file
    try:
        os.unlink(temp_audio)
    except OSError:
        pass
    
    print(f"\n🎉 Predownload complete: {success_count}/{len(mlx_models)} models cached")
    print("💾 Models are now cached locally for offline use")
    
    if success_count > 0:
        print("\n🚀 MLX Whisper is ready for 20-30x speed improvement on Apple Silicon!")
        return True
    else:
        print("\n⚠️  No models were successfully downloaded")
        return False

def check_mlx_models():
    """Check which MLX models are already cached"""
    try:
        import mlx_whisper
        print("🔍 Checking MLX model cache...")
        
        # MLX models are typically cached in ~/.cache/huggingface/
        cache_dir = Path.home() / ".cache" / "huggingface"
        if cache_dir.exists():
            print(f"📁 Cache directory: {cache_dir}")
            
            # List cached whisper models
            whisper_dirs = list(cache_dir.glob("**/models--openai--whisper*"))
            if whisper_dirs:
                print("✅ Cached MLX Whisper models found:")
                for dir_path in whisper_dirs:
                    model_name = dir_path.name.replace("models--openai--whisper-", "")
                    print(f"  • {model_name}")
            else:
                print("📭 No cached MLX Whisper models found")
                return False
        else:
            print("📭 No HuggingFace cache directory found")
            return False
            
        return True
        
    except ImportError:
        print("❌ MLX Whisper not available")
        return False

if __name__ == "__main__":
    print("🎬 MLX Whisper Model Predownloader for screenscribe")
    print("=" * 50)
    
    # Check current status
    check_mlx_models()
    print()
    
    # Ask user if they want to predownload
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        proceed = True
    else:
        response = input("📥 Predownload all MLX models now? [y/N]: ").lower().strip()
        proceed = response in ['y', 'yes']
    
    if proceed:
        success = predownload_mlx_models()
        if success:
            print("\n🎯 Next steps:")
            print("  • Run: scribe analyze video.mp4 --whisper-backend auto")
            print("  • MLX will be used automatically for 20-30x speedup")
        sys.exit(0 if success else 1)
    else:
        print("⏭️  Skipping predownload. Run with --auto flag to download without prompting.")
        sys.exit(0)