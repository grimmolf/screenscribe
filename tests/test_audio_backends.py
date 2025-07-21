"""Unit tests for audio backend detection and compatibility."""

import platform
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from screenscribe.audio_backends import (
    FasterWhisperBackend,
    MLXWhisperBackend,
    get_available_backends,
    get_best_backend,
)
from screenscribe.models import BackendInfo, TranscriptionResult, TranscriptionSegment


class TestBackendDetection:
    """Test backend detection and availability."""

    def test_mlx_only_on_apple_silicon(self):
        """Test MLX backend is only available on Apple Silicon."""
        backend = MLXWhisperBackend()
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            # May or may not be available depending on installation
            assert isinstance(backend.is_available(), bool)
        else:
            assert not backend.is_available()

    def test_faster_whisper_always_available(self):
        """Test faster-whisper backend is always available as fallback."""
        backend = FasterWhisperBackend()
        assert backend.is_available()

    def test_auto_selection(self):
        """Test automatic backend selection returns available backend."""
        backend = get_best_backend()
        assert backend is not None
        assert backend.is_available()

    def test_get_available_backends(self):
        """Test getting list of available backends."""
        backends = get_available_backends()
        assert isinstance(backends, list)
        assert len(backends) >= 1  # At least faster-whisper should be available

        # Check that all returned info objects are properly formatted
        for info in backends:
            assert isinstance(info, BackendInfo)
            assert isinstance(info.available, bool)
            assert isinstance(info.name, str)
            assert isinstance(info.device, str)

    def test_preferred_backend_selection(self):
        """Test explicit backend selection."""
        # Test selecting faster-whisper (should always work)
        backend = get_best_backend(preferred="faster-whisper")
        assert isinstance(backend, FasterWhisperBackend)
        assert backend.is_available()

        # Test selecting MLX (may not work on all platforms)
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            try:
                backend = get_best_backend(preferred="mlx")
                if backend.is_available():
                    assert isinstance(backend, MLXWhisperBackend)
            except Exception:
                # MLX not installed, should fall back
                pass


class TestBackendInfo:
    """Test backend information objects."""

    def test_faster_whisper_info(self):
        """Test faster-whisper backend info."""
        backend = FasterWhisperBackend()
        info = backend.get_info()

        assert info.name == "faster-whisper"
        assert info.available is True
        assert isinstance(info.device, str)
        assert info.device in ["cpu", "cuda"]
        assert info.compute_type in ["int8", "float16"]

    def test_mlx_info_structure(self):
        """Test MLX backend info structure (regardless of availability)."""
        backend = MLXWhisperBackend()
        info = backend.get_info()

        assert info.name == "mlx"
        assert isinstance(info.available, bool)
        assert isinstance(info.device, str)

        if not info.available:
            assert isinstance(info.reason, str)
            assert len(info.reason) > 0


class TestBackendCompatibility:
    """Test backend output compatibility."""

    @pytest.fixture
    def mock_transcription_result(self):
        """Mock transcription result for testing."""
        segments = [
            TranscriptionSegment(
                id=0,
                seek=0,
                start=0.0,
                end=2.5,
                text="Hello world",
                tokens=[123, 456],
                temperature=0.0,
                avg_logprob=-0.5,
                compression_ratio=1.2,
                no_speech_prob=0.1,
            ),
        ]

        return TranscriptionResult(
            text="Hello world",
            segments=segments,
            language="en",
            duration=2.5,
        )

    def test_transcription_result_structure(self, mock_transcription_result):
        """Test transcription result has required structure."""
        result = mock_transcription_result

        # Test top-level structure
        assert isinstance(result.text, str)
        assert isinstance(result.segments, list)
        assert isinstance(result.language, str)
        assert isinstance(result.duration, (float, type(None)))

        # Test segment structure
        if result.segments:
            seg = result.segments[0]
            assert isinstance(seg.id, int)
            assert isinstance(seg.start, float)
            assert isinstance(seg.end, float)
            assert isinstance(seg.text, str)
            assert isinstance(seg.tokens, list)

    @patch("screenscribe.audio_backends.Path.exists")
    def test_backend_output_normalization(self, mock_exists):
        """Test that different backends produce compatible output format."""
        mock_exists.return_value = True

        # Test faster-whisper backend normalization
        backend = FasterWhisperBackend(model_name="tiny")

        # Mock the transcribe method to avoid actual model loading
        mock_segments = [
            Mock(
                id=0, seek=0, start=0.0, end=2.5, text="Hello world",
                tokens=[123, 456], temperature=0.0, avg_logprob=-0.5,
                compression_ratio=1.2, no_speech_prob=0.1, words=[],
            ),
        ]
        mock_info = Mock(language="en", duration=2.5)

        with patch.object(backend, "model") as mock_model:
            mock_model.transcribe.return_value = (mock_segments, mock_info)
            backend.model = mock_model

            result = backend.transcribe(Path("dummy.wav"))

            # Verify normalized output structure
            assert isinstance(result, TranscriptionResult)
            assert result.text == "Hello world"
            assert len(result.segments) == 1
            assert result.language == "en"
            assert result.duration == 2.5


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_backend_preference(self):
        """Test handling of invalid backend preference."""
        # Should fall back to available backend
        backend = get_best_backend(preferred="nonexistent-backend")
        assert backend is not None
        assert backend.is_available()

    def test_model_name_propagation(self):
        """Test that model name is properly propagated to backends."""
        model_name = "large"
        backend = get_best_backend(model_name=model_name)
        assert backend.model_name == model_name

    def test_backend_unavailable_fallback(self):
        """Test that unavailable backends don't crash the system."""
        # This should always return a working backend (faster-whisper)
        backend = get_best_backend()
        assert backend is not None
        assert backend.is_available()

        # Should be able to get info without crashing
        info = backend.get_info()
        assert isinstance(info, BackendInfo)
        assert info.available is True


class TestPerformanceConsiderations:
    """Test performance-related backend features."""

    def test_cpu_optimization_detection(self):
        """Test CPU optimization is detected correctly."""
        backend = FasterWhisperBackend()
        info = backend.get_info()

        # Should use appropriate compute type based on platform
        if info.device == "cpu":
            assert info.compute_type == "int8"  # CPU uses int8 for performance
        elif info.device == "cuda":
            assert info.compute_type == "float16"  # GPU uses float16

    @pytest.mark.skipif(
        platform.system() != "Darwin" or platform.machine() != "arm64",
        reason="Apple Silicon specific test",
    )
    def test_apple_silicon_detection(self):
        """Test Apple Silicon platform detection (only on Apple Silicon)."""
        backend = MLXWhisperBackend()

        # On Apple Silicon, should at least attempt to be available
        # (may fail if mlx-whisper not installed, but should detect platform)
        info = backend.get_info()

        if not info.available:
            # If not available, should have a reason
            assert info.reason is not None
            assert "MLX" in info.reason or "Apple Silicon" in info.reason
        else:
            # If available, should use GPU
            assert info.device == "gpu"
            assert info.compute_type == "float16"
