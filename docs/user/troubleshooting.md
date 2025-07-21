# Troubleshooting Guide

This guide covers common issues and their solutions when using screenscribe.

> 📖 **For comprehensive guidance**, see the **[User Manual](../USER_MANUAL.md)** which includes complete usage, optimization, prompt customization, and troubleshooting guidance.

## Backend and Performance Issues

### MLX Backend Not Available (Apple Silicon)

**Problem**: `screenscribe --list-backends` shows MLX as unavailable on M1/M2/M3 Mac

**Solutions**:

1. **Install Apple Silicon dependencies (CRITICAL)**:
   ```bash
   # For development installation - ALWAYS use [apple] for GPU acceleration
   uv tool install --editable './[apple]' --force
   
   # For package installation (when released)
   uv tool install "screenscribe[apple]" --force
   ```

2. **Verify platform detection**:
   ```bash
   python3 -c "import platform; print(f'{platform.system()} {platform.machine()}')"
   # Should show: Darwin arm64
   ```

3. **Test MLX manually**:
   ```bash
   python3 -c "import mlx_whisper; print('✅ MLX working')"
   ```

### Slow Transcription Performance

**Problem**: Transcription taking much longer than expected

**Diagnosis**:
```bash
# Check which backend is being used
screenscribe --list-backends

# Look for:
# ✅ mlx: gpu (float16)         ← Should be available on Apple Silicon
# ✅ faster-whisper: cpu (int8)  ← CPU fallback
```

**Solutions**:

1. **For Apple Silicon users - ensure GPU acceleration**:
   ```bash
   # Force MLX backend
   screenscribe video.mp4 --whisper-backend mlx
   
   # Expected performance: 49min video in ~103 seconds (1.7 minutes)
   
   # If MLX backend shows as unavailable, reinstall with Apple dependencies:
   cd /path/to/screenscribe/
   uv tool install --editable './[apple]' --force
   ```

2. **Choose appropriate model size**:
   ```bash
   # Faster but less accurate
   screenscribe video.mp4 --whisper-model tiny
   
   # Slower but more accurate
   screenscribe video.mp4 --whisper-model large
   ```

3. **For network storage (NAS/SMB)**:
   - screenscribe automatically copies files locally for better performance
   - Ensure sufficient disk space in /tmp

### Backend Selection Issues

**Problem**: Wrong backend being selected automatically

**Solutions**:

1. **Force specific backend**:
   ```bash
   # Force Apple Silicon GPU
   screenscribe video.mp4 --whisper-backend mlx
   
   # Force CPU backend
   screenscribe video.mp4 --whisper-backend faster-whisper
   ```

2. **Check backend availability**:
   ```bash
   screenscribe --list-backends test.mp4
   ```

## Installation Issues

### Command Not Found: screenscribe

**Problem**: Terminal reports `screenscribe: command not found`

**Solutions**:

1. **Check if uv tools are in PATH**:
   ```bash
   echo $PATH | grep -q "$HOME/.local/bin" || echo "Need to add to PATH"
   ```

2. **Add uv tools to PATH**:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   # Add to your shell profile:
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   ```

3. **Reinstall screenscribe**:
   ```bash
   uv tool uninstall screenscribe
   uv tool install screenscribe
   ```

4. **Verify installation location**:
   ```bash
   uv tool list | grep screenscribe
   ```

### FFmpeg Installation Issues

**Problem**: `FFmpeg not found` error

**Solutions**:

1. **Verify FFmpeg installation**:
   ```bash
   ffmpeg -version
   ```

2. **Install FFmpeg**:
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # Fedora
   sudo dnf install ffmpeg
   
   # Arch Linux
   sudo pacman -S ffmpeg
   ```

3. **Check PATH**:
   ```bash
   which ffmpeg
   ```

### Python Version Issues

**Problem**: Compatibility errors with Python versions

**Solutions**:

1. **Check Python version**:
   ```bash
   python3 --version
   ```

2. **Install compatible Python version**:
   - screenscribe requires Python 3.9 or higher
   - Use pyenv or your system package manager

3. **Force specific Python version**:
   ```bash
   uv python install 3.11
   uv tool install --python 3.11 screenscribe
   ```

## Runtime Errors

### API Key Issues

**Problem**: `No API keys found` or authentication errors

**Solutions**:

1. **Set API keys**:
   ```bash
   export OPENAI_API_KEY="sk-your-key-here"
   # Or for Anthropic:
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```

2. **Verify API key format**:
   - OpenAI keys start with `sk-`
   - Anthropic keys start with `sk-ant-`

3. **Check API key validity**:
   ```bash
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        "https://api.openai.com/v1/models" | head -20
   ```

4. **Add to shell profile**:
   ```bash
   echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Memory Issues

**Problem**: Out of memory errors or system freezing

**Solutions**:

1. **Use smaller Whisper model**:
   ```bash
   screenscribe video.mp4 --whisper-model tiny
   ```

2. **Reduce frame sampling**:
   ```bash
   screenscribe video.mp4 --sampling-mode interval --interval 30
   ```

3. **Process shorter segments**:
   ```bash
   # Use FFmpeg to split large videos
   ffmpeg -i large-video.mp4 -t 600 -c copy segment1.mp4
   ```

4. **Close other applications**:
   - Free up RAM before processing large videos
   - Monitor system resources with `top` or Activity Monitor

### GPU Issues

**Problem**: CUDA errors or GPU out of memory

**Solutions**:

1. **Force CPU usage**:
   ```bash
   export CUDA_VISIBLE_DEVICES=""
   screenscribe video.mp4
   ```

2. **Use smaller models**:
   ```bash
   screenscribe video.mp4 --whisper-model base
   ```

3. **Check GPU memory**:
   ```bash
   nvidia-smi  # Check GPU memory usage
   ```

## Processing Issues

### Video Format Problems

**Problem**: `Unsupported video format` or codec errors

**Solutions**:

1. **Convert video format**:
   ```bash
   ffmpeg -i input-video.mkv -c:v libx264 -c:a aac output.mp4
   ```

2. **Check video properties**:
   ```bash
   ffprobe -v quiet -print_format json -show_format input.mp4
   ```

3. **Use compatible formats**:
   - MP4 (recommended)
   - MKV, MOV, AVI, WebM

### Audio Issues

**Problem**: `No audio stream found` error

**Solutions**:

1. **Check if video has audio**:
   ```bash
   ffprobe -v error -select_streams a:0 -show_entries stream=codec_type -of csv=p=0 video.mp4
   ```

2. **Add audio track**:
   ```bash
   # Add silent audio track
   ffmpeg -i video-no-audio.mp4 -f lavfi -i anullsrc=c=mono:r=48000 -c:v copy -c:a aac -shortest output.mp4
   ```

3. **Extract audio separately**:
   ```bash
   ffmpeg -i video.mp4 -vn -c:a wav audio.wav
   screenscribe audio.wav  # Process audio-only
   ```

### Transcription Quality Issues

**Problem**: Poor transcription accuracy

**Solutions**:

1. **Use larger Whisper model**:
   ```bash
   screenscribe video.mp4 --whisper-model large
   ```

2. **Check audio quality**:
   - Ensure clear speech in source video
   - Remove background noise if possible

3. **Verify language settings**:
   ```bash
   # For non-English content, consider preprocessing
   # Whisper auto-detects language but may need hints
   ```

### Scene Detection Issues

**Problem**: Too many or too few frames extracted

**Solutions**:

1. **Adjust scene threshold**:
   ```bash
   # More sensitive (more frames)
   screenscribe video.mp4 --scene-threshold 0.1
   
   # Less sensitive (fewer frames)  
   screenscribe video.mp4 --scene-threshold 0.5
   ```

2. **Use interval mode**:
   ```bash
   screenscribe video.mp4 --sampling-mode interval --interval 10
   ```

3. **Check video content**:
   - Static content may need lower thresholds
   - Dynamic content may need higher thresholds

## LLM and Synthesis Issues

### Rate Limiting

**Problem**: `Rate limit exceeded` errors

**Solutions**:

1. **Reduce concurrency**:
   - Edit synthesis.py to lower `max_concurrent` (default: 5)

2. **Wait and retry**:
   ```bash
   # Rate limits reset after time
   sleep 60 && screenscribe video.mp4
   ```

3. **Use fallback provider**:
   ```bash
   # Set both API keys for automatic fallback
   export OPENAI_API_KEY="sk-..."
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

### Poor Analysis Quality

**Problem**: Generic or inaccurate frame analysis

**Solutions**:

1. **Customize prompts**:
   - See [Prompt Customization Guide](prompt-customization.md)
   - Create content-specific prompts

2. **Use better models**:
   ```bash
   screenscribe video.mp4 --llm openai  # Use GPT-4 Vision
   ```

3. **Improve input quality**:
   - Ensure good video resolution
   - Check that thumbnails are clear

### JSON Parsing Errors

**Problem**: `Failed to parse LLM response` errors

**Solutions**:

1. **Check prompt format**:
   - Ensure JSON schema is clear in prompts
   - Verify template variables are correct

2. **Use fallback mode**:
   ```bash
   screenscribe video.mp4 --no-fallback false
   ```

3. **Debug LLM responses**:
   ```bash
   screenscribe video.mp4 --verbose
   ```

## Network and Connectivity Issues

### Download Failures

**Problem**: YouTube download errors

**Solutions**:

1. **Update yt-dlp**:
   ```bash
   pip install --upgrade yt-dlp
   ```

2. **Check video availability**:
   - Ensure video is public
   - Check for geographic restrictions

3. **Use cookies for restricted content**:
   ```bash
   # Export cookies from browser and use with yt-dlp
   yt-dlp --cookies cookies.txt "https://youtube.com/..."
   ```

### API Connectivity Issues

**Problem**: Network timeouts or connection errors

**Solutions**:

1. **Check internet connection**:
   ```bash
   ping api.openai.com
   ```

2. **Configure proxy if needed**:
   ```bash
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

3. **Increase timeouts**:
   - Edit synthesis.py to increase timeout values

## Performance Issues

### Slow Processing

**Problem**: Very slow processing speeds

**Solutions**:

1. **Use faster models**:
   ```bash
   screenscribe video.mp4 --whisper-model tiny
   ```

2. **Reduce frame count**:
   ```bash
   screenscribe video.mp4 --sampling-mode interval --interval 60
   ```

3. **Check system resources**:
   ```bash
   htop  # Monitor CPU and memory usage
   ```

4. **Use GPU acceleration**:
   ```bash
   # Ensure CUDA is available for Whisper
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### High Memory Usage

**Problem**: Excessive memory consumption

**Solutions**:

1. **Process in segments**:
   ```bash
   # Split video into smaller parts
   ffmpeg -i large.mp4 -t 300 -c copy part1.mp4
   ```

2. **Clear cache**:
   ```bash
   # Clear Whisper model cache if needed
   rm -rf ~/.cache/whisper/*
   ```

## Getting Help

### Enable Verbose Mode

For detailed debugging information:

```bash
screenscribe video.mp4 --verbose
```

### Check Logs

Monitor system logs for additional error information:

```bash
# macOS
tail -f /var/log/system.log | grep screenscribe

# Linux
journalctl -f | grep screenscribe
```

### Create Minimal Test Case

For reporting issues:

1. Test with a short video (30 seconds)
2. Use default settings
3. Save error output
4. Note your system configuration

### System Information

Gather system info for troubleshooting:

```bash
# System information
uname -a
python3 --version
uv --version
ffmpeg -version | head -1

# screenscribe information
uv tool list | grep screenscribe
screenscribe --help | head -10
```

### Report Issues

When reporting problems:

1. Include system information
2. Provide exact error messages
3. Share minimal reproduction steps  
4. Include video characteristics (length, format, size)

### Common Error Patterns

**Import Errors**: Usually missing dependencies
**Permission Errors**: File access or executable permissions
**Memory Errors**: Video too large or insufficient RAM
**Network Errors**: API connectivity or rate limiting
**Format Errors**: Video codec or container issues

## Preventive Measures

### Regular Maintenance

1. **Keep tools updated**:
   ```bash
   uv tool upgrade screenscribe
   ```

2. **Clean temporary files**:
   ```bash
   # Clean up processing outputs periodically
   find /tmp -name "*screenscribe*" -delete
   ```

3. **Monitor disk space**:
   ```bash
   df -h  # Ensure sufficient space for processing
   ```

### Best Practices

- Test with short videos first
- Monitor system resources during processing
- Keep API keys secure and rotated
- Backup important configurations
- Use version control for custom prompts

## Still Having Issues?

If problems persist:

1. Check the [GitHub Issues](https://github.com/screenscribe/screenscribe/issues)
2. Search for similar problems
3. Create a new issue with detailed information
4. Consider joining community discussions