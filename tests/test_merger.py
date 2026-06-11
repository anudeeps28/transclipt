"""Tests for transclipt.merger module."""

from __future__ import annotations

import pytest

from transclipt.merger import CaptureResult, merge_results
from transclipt.ocr import OcrBlock
from transclipt.transcriber import Segment, TranscriptionResult


def _make_transcription(text: str = "Hello world.") -> TranscriptionResult:
    return TranscriptionResult(
        segments=(Segment(start=0.0, end=2.0, text=f" {text}"),),
        language="en",
        language_probability=0.99,
    )


class TestCaptureResult:
    def test_frozen(self) -> None:
        result = CaptureResult(
            ocr_texts=(),
            transcription=None,
            title="Test",
            source_url="https://example.com",
        )
        with pytest.raises(AttributeError):
            result.title = "changed"  # type: ignore[misc]

    def test_combined_text_ocr_only(self) -> None:
        blocks = (
            OcrBlock(text="5 Morning Habits", confidence=0.95, first_seen_at=0.0),
            OcrBlock(text="Wake up at 5am", confidence=0.9, first_seen_at=2.0),
        )
        result = CaptureResult(
            ocr_texts=blocks,
            transcription=None,
            title="Test",
            source_url="https://example.com",
        )
        assert result.combined_text == "5 Morning Habits\nWake up at 5am"

    def test_combined_text_audio_only(self) -> None:
        result = CaptureResult(
            ocr_texts=(),
            transcription=_make_transcription("This is spoken audio."),
            title="Test",
            source_url="https://example.com",
        )
        assert result.combined_text == "This is spoken audio."

    def test_combined_text_both(self) -> None:
        blocks = (
            OcrBlock(text="Title on screen", confidence=0.95, first_seen_at=0.0),
        )
        result = CaptureResult(
            ocr_texts=blocks,
            transcription=_make_transcription("And here is what was said."),
            title="Test",
            source_url="https://example.com",
        )
        assert "Title on screen" in result.combined_text
        assert "And here is what was said." in result.combined_text

    def test_combined_text_empty(self) -> None:
        result = CaptureResult(
            ocr_texts=(),
            transcription=None,
            title="Test",
            source_url="https://example.com",
        )
        assert result.combined_text == ""


class TestMergeResults:
    def test_returns_capture_result(self) -> None:
        blocks = (
            OcrBlock(text="Some text", confidence=0.9, first_seen_at=0.0),
        )
        tx = _make_transcription()
        result = merge_results(
            ocr_texts=blocks,
            transcription=tx,
            title="My Reel",
            source_url="https://instagram.com/reel/abc",
        )
        assert isinstance(result, CaptureResult)
        assert result.title == "My Reel"
        assert result.source_url == "https://instagram.com/reel/abc"
        assert len(result.ocr_texts) == 1
        assert result.transcription is not None
