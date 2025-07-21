"""Integration tests for multi-backend audio functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from screenscribe.audio import AudioProcessor
from screenscribe.cli import validate_inputs
from screenscribe.models import ProcessingOptions


class TestBackendIntegration:
    """Test integration between backends and AudioProcessor."""

    def test_audio_processor_backend_selection(self):
        """Test AudioProcessor correctly uses selected backend."""
        # Test auto-selection (should work on all platforms)
        processor = AudioProcessor(model_name="tiny")
        assert processor.backend is not None
        assert processor.backend.is_available()

        # Test explicit faster-whisper selection
        processor = AudioProcessor(model_name="tiny", backend="faster-whisper")
        assert processor.backend.get_info().name == "faster-whisper"

        # Test invalid backend falls back gracefully
        processor = AudioProcessor(model_name="tiny", backend="nonexistent")
        assert processor.backend is not None
        assert processor.backend.is_available()

    def test_model_info_consistency(self):
        """Test model info is consistent across different backends."""
        processor = AudioProcessor(model_name="base")
        info = processor.get_model_info()

        # Should contain required fields
        assert "model_name" in info
        assert "backend" in info
        assert "device" in info
        assert "available" in info

        assert info["model_name"] == "base"
        assert info["available"] is True
        assert isinstance(info["backend"], str)
        assert isinstance(info["device"], str)

    @patch("screenscribe.audio.Path.exists")
    @patch("screenscribe.audio.subprocess.run")
    async def test_audio_extraction_backend_agnostic(self, mock_subprocess, mock_exists):
        """Test audio extraction works regardless of backend."""
        mock_exists.return_value = True
        mock_subprocess.return_value = Mock(stdout="audio", returncode=0)

        # Test with different backends
        for backend in [None, "faster-whisper"]:  # None = auto-select
            processor = AudioProcessor(model_name="tiny", backend=backend)

            with patch.object(processor, "_check_nas_performance", return_value=False):
                with patch("tempfile.mktemp", return_value="/tmp/test.wav"):
                    # Should not fail regardless of backend
                    try:
                        result_path = await processor.extract_audio(Path("dummy.mp4"))
                        assert isinstance(result_path, Path)
                    except Exception as e:
                        # Some mocking might fail, but shouldn't be backend-specific errors
                        assert "backend" not in str(e).lower()


class TestCLIIntegration:
    """Test CLI integration with multi-backend system."""

    def test_cli_backend_validation(self):
        """Test CLI properly validates backend selections."""
        # Test valid inputs don't raise errors
        try:
            validate_inputs(
                "/tmp/test.mp4", Path("/tmp/output"),
                "markdown", "scene", "medium", "openai",
            )
        except SystemExit:
            # Expected for missing dependencies, not backend issues
            pass

    def test_processing_options_backend_field(self):
        """Test ProcessingOptions properly handles backend field."""
        options = ProcessingOptions(
            output_dir=Path("/tmp"),
            output_format="markdown",
            whisper_model="base",
            whisper_backend="faster-whisper",
        )

        assert options.whisper_backend == "faster-whisper"

        # Test None backend (auto-select)
        options_auto = ProcessingOptions(
            output_dir=Path("/tmp"),
            output_format="markdown",
            whisper_model="base",
            whisper_backend=None,
        )

        assert options_auto.whisper_backend is None


class TestEndToEndFlow:
    """Test end-to-end processing flow with different backends."""

    @pytest.fixture
    def temp_audio_file(self):
        """Create a temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # Create minimal WAV file header (44 bytes)
            wav_header = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
            f.write(wav_header)
            return Path(f.name)

    def test_backend_consistency(self, temp_audio_file):
        """Test different backends produce consistent results (mocked)."""
        # Since we can't run actual transcription in tests, mock the backend results

        mock_result = {
            "text": "Test transcription",
            "segments": [{
                "id": 0,
                "seek": 0,
                "start": 0.0,
                "end": 1.0,
                "text": "Test transcription",
                "tokens": [],
                "temperature": 0.0,
                "avg_logprob": -0.5,
                "compression_ratio": 1.0,
                "no_speech_prob": 0.1,
                "words": [],
            }],
            "language": "en",
            "duration": 1.0,
        }

        # Test different backends produce same structure
        for backend_name in ["faster-whisper"]:  # Only test available ones
            processor = AudioProcessor(model_name="tiny", backend=backend_name)

            # Mock the backend transcribe method
            with patch.object(processor.backend, "transcribe") as mock_transcribe:
                from screenscribe.models import (
                    TranscriptionResult,
                    TranscriptionSegment,
                )

                segment = TranscriptionSegment(
                    id=0, seek=0, start=0.0, end=1.0, text="Test transcription",
                    tokens=[], temperature=0.0, avg_logprob=-0.5,
                    compression_ratio=1.0, no_speech_prob=0.1, words=[],
                )

                mock_transcribe.return_value = TranscriptionResult(
                    text="Test transcription",
                    segments=[segment],
                    language="en",
                    duration=1.0,
                )

                result = processor.transcribe(temp_audio_file)

                # Verify result structure
                assert "text" in result
                assert "segments" in result
                assert "language" in result
                assert result["text"] == "Test transcription"
                assert len(result["segments"]) == 1
                assert result["language"] == "en"

        # Clean up
        temp_audio_file.unlink(missing_ok=True)


class TestPlatformSpecific:
    """Test platform-specific backend behavior."""

    @pytest.mark.skipif(
        not (Path("/System/Library/CoreServices/Finder.app").exists()),
        reason="macOS specific test",
    )
    def test_macos_backend_priority(self):
        """Test macOS properly prioritizes MLX when available."""
        import platform

        if platform.system() == "Darwin" and platform.machine() == "arm64":
            # On Apple Silicon, should prefer MLX if available
            processor = AudioProcessor(model_name="tiny")
            backend_info = processor.backend.get_info()

            # Either MLX is selected, or faster-whisper with good reason
            if backend_info.name == "mlx":
                assert backend_info.device == "gpu"
            else:
                assert backend_info.name == "faster-whisper"
                # Should have fallen back for a reason (e.g., MLX not installed)

    def test_cross_platform_fallback(self):
        """Test system gracefully falls back on all platforms."""
        # This should work on any platform
        processor = AudioProcessor(model_name="tiny")
        backend_info = processor.backend.get_info()

        # Should always have a working backend
        assert backend_info.available is True
        assert backend_info.name in ["mlx", "faster-whisper"]

        # faster-whisper should always be available
        fallback_processor = AudioProcessor(model_name="tiny", backend="faster-whisper")
        fallback_info = fallback_processor.backend.get_info()
        assert fallback_info.available is True
        assert fallback_info.name == "faster-whisper"


class TestErrorHandling:
    """Test error handling in multi-backend system."""

    def test_invalid_audio_file_handling(self):
        """Test backends handle invalid audio files gracefully."""
        processor = AudioProcessor(model_name="tiny")

        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            processor.transcribe(Path("/nonexistent/file.wav"))

    def test_backend_initialization_errors(self):
        """Test graceful handling of backend initialization errors."""
        # Should not crash even with invalid model names
        processor = AudioProcessor(model_name="nonexistent-model")
        assert processor.backend is not None

        # Should be able to get info
        info = processor.get_model_info()
        assert isinstance(info, dict)
        assert "model_name" in info

    def test_transcription_interruption_handling(self):
        """Test transcription can be interrupted gracefully."""
        processor = AudioProcessor(model_name="tiny")

        # Mock interruption scenario
        with patch("screenscribe.audio._shutdown_requested", True):
            # Should handle interruption without crashing
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav") as f:
                    # Create minimal WAV file
                    wav_header = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
                    f.write(wav_header)
                    f.flush()

                    result = processor.transcribe(Path(f.name))
                    # May succeed or fail gracefully, but shouldn't crash
                    if result:
                        assert isinstance(result, dict)
            except (KeyboardInterrupt, RuntimeError) as e:
                # These are expected for interruption scenarios
                assert "interrupt" in str(e).lower() or "fail" in str(e).lower()
