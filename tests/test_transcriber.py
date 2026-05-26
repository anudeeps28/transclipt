"""Tests for transclipt.transcriber module."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from transclipt.transcriber import (
    Segment,
    TranscriptionResult,
    _MODEL_CACHE,
    _get_model,
    transcribe,
)


class TestSegment:
    def test_frozen(self) -> None:
        seg = Segment(start=0.0, end=1.0, text="hello")
        assert seg.start == 0.0
        assert seg.end == 1.0
        assert seg.text == "hello"


class TestTranscriptionResult:
    def test_full_text_joins_segments(self) -> None:
        result = TranscriptionResult(
            segments=(
                Segment(start=0.0, end=1.0, text=" Hello."),
                Segment(start=1.0, end=2.0, text=" World."),
            ),
            language="en",
            language_probability=0.99,
        )
        assert result.full_text == "Hello. World."

    def test_empty_segments(self) -> None:
        result = TranscriptionResult(
            segments=(),
            language="en",
            language_probability=0.95,
        )
        assert result.full_text == ""

    def test_single_segment(self) -> None:
        result = TranscriptionResult(
            segments=(Segment(start=0.0, end=5.0, text=" Just one segment."),),
            language="es",
            language_probability=0.87,
        )
        assert result.full_text == "Just one segment."
        assert result.language == "es"


class TestGetModel:
    @patch("transclipt.transcriber.WhisperModel")
    def test_creates_model_with_int8_for_cpu(self, mock_model_class: MagicMock) -> None:
        _MODEL_CACHE.clear()
        _get_model("base", "cpu")
        mock_model_class.assert_called_once_with("base", device="cpu", compute_type="int8")

    @patch("transclipt.transcriber.WhisperModel")
    def test_creates_model_with_float16_for_cuda(self, mock_model_class: MagicMock) -> None:
        _MODEL_CACHE.clear()
        _get_model("large-v3", "cuda")
        mock_model_class.assert_called_once_with(
            "large-v3", device="cuda", compute_type="float16"
        )

    @patch("transclipt.transcriber.WhisperModel")
    def test_caches_model(self, mock_model_class: MagicMock) -> None:
        _MODEL_CACHE.clear()
        model1 = _get_model("base", "cpu")
        model2 = _get_model("base", "cpu")
        assert model1 is model2
        mock_model_class.assert_called_once()

    @patch("transclipt.transcriber.WhisperModel")
    def test_different_keys_create_different_models(self, mock_model_class: MagicMock) -> None:
        _MODEL_CACHE.clear()
        _get_model("base", "cpu")
        _get_model("small", "cpu")
        assert mock_model_class.call_count == 2


class TestTranscribe:
    @patch("transclipt.transcriber._get_model")
    def test_transcribe_returns_result(self, mock_get_model: MagicMock) -> None:
        fake_segments = [
            SimpleNamespace(start=0.0, end=2.5, text=" Hello world."),
            SimpleNamespace(start=3.0, end=5.5, text=" Goodbye world."),
        ]
        fake_info = SimpleNamespace(language="en", language_probability=0.98)

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter(fake_segments), fake_info)
        mock_get_model.return_value = mock_model

        result = transcribe(Path("/fake/audio.mp3"), model_size="base", device="cpu")

        assert isinstance(result, TranscriptionResult)
        assert len(result.segments) == 2
        assert result.language == "en"
        assert result.language_probability == 0.98
        assert result.full_text == "Hello world. Goodbye world."

    @patch("transclipt.transcriber._get_model")
    def test_transcribe_passes_language(self, mock_get_model: MagicMock) -> None:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (
            iter([]),
            SimpleNamespace(language="hi", language_probability=0.90),
        )
        mock_get_model.return_value = mock_model

        transcribe(Path("/fake/audio.mp3"), language="hi", device="cpu")

        mock_model.transcribe.assert_called_once_with(
            "/fake/audio.mp3",
            language="hi",
            beam_size=5,
            vad_filter=True,
        )

    @patch("transclipt.transcriber._get_model")
    def test_transcribe_empty_audio(self, mock_get_model: MagicMock) -> None:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (
            iter([]),
            SimpleNamespace(language="en", language_probability=0.50),
        )
        mock_get_model.return_value = mock_model

        result = transcribe(Path("/fake/silence.mp3"), device="cpu")
        assert result.segments == ()
        assert result.full_text == ""
