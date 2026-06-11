"""Tests for transclipt.ocr module."""

from __future__ import annotations

from pathlib import Path

import pytest

from transclipt.ocr import (
    OcrBlock,
    NoopProvider,
    AppleVisionProvider,
    get_provider,
    extract_text_from_frames,
    _is_duplicate,
)


class TestOcrBlock:
    def test_frozen(self) -> None:
        block = OcrBlock(text="Hello", confidence=0.95, first_seen_at=1.0)
        with pytest.raises(AttributeError):
            block.text = "changed"  # type: ignore[misc]

    def test_fields(self) -> None:
        block = OcrBlock(text="Test", confidence=0.8, first_seen_at=2.5)
        assert block.text == "Test"
        assert block.confidence == 0.8
        assert block.first_seen_at == 2.5


class TestIsDuplicate:
    def test_exact_match(self) -> None:
        assert _is_duplicate("Hello world", ["Hello world"]) is True

    def test_case_insensitive(self) -> None:
        assert _is_duplicate("HELLO WORLD", ["hello world"]) is True

    def test_fuzzy_match(self) -> None:
        assert _is_duplicate("Hello world!", ["Hello world"]) is True

    def test_no_match(self) -> None:
        assert _is_duplicate("Completely different", ["Hello world"]) is False

    def test_empty_seen(self) -> None:
        assert _is_duplicate("Hello", []) is False

    def test_custom_threshold(self) -> None:
        assert _is_duplicate("Hello", ["Hell"], threshold=0.95) is False
        assert _is_duplicate("Hello", ["Hell"], threshold=0.5) is True


class TestNoopProvider:
    def test_returns_empty(self, tmp_path: Path) -> None:
        provider = NoopProvider()
        result = provider.extract_text(tmp_path / "frame.png")
        assert result == []


class TestGetProvider:
    def test_vision_provider(self) -> None:
        provider = get_provider("vision")
        assert isinstance(provider, (AppleVisionProvider, NoopProvider))

    def test_noop_provider(self) -> None:
        provider = get_provider("noop")
        assert isinstance(provider, NoopProvider)

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown OCR provider"):
            get_provider("unknown")


class TestExtractTextFromFrames:
    def test_empty_directory(self, tmp_path: Path) -> None:
        result = extract_text_from_frames(tmp_path, provider=NoopProvider())
        assert result == ()

    def test_no_matching_files(self, tmp_path: Path) -> None:
        (tmp_path / "other.jpg").write_bytes(b"fake")
        result = extract_text_from_frames(tmp_path, provider=NoopProvider())
        assert result == ()

    def test_deduplicates_across_frames(self, tmp_path: Path) -> None:
        for i in range(3):
            (tmp_path / f"frame_{i:04d}.png").write_bytes(b"fake")

        class RepeatingProvider:
            def extract_text(self, frame_path: Path) -> list[tuple[str, float]]:
                return [("Same text every frame", 0.95)]

        result = extract_text_from_frames(tmp_path, provider=RepeatingProvider())
        assert len(result) == 1
        assert result[0].text == "Same text every frame"
        assert result[0].first_seen_at == 0.0

    def test_captures_new_text(self, tmp_path: Path) -> None:
        for i in range(3):
            (tmp_path / f"frame_{i:04d}.png").write_bytes(b"fake")

        texts = [
            "5 Morning Habits That Changed My Life",
            "How to Build a Second Brain with Notion",
            "The Psychology of Procrastination Explained",
        ]

        class ChangingProvider:
            def __init__(self) -> None:
                self._call_count = 0

            def extract_text(self, frame_path: Path) -> list[tuple[str, float]]:
                idx = self._call_count
                self._call_count += 1
                return [(texts[idx], 0.9)]

        result = extract_text_from_frames(tmp_path, provider=ChangingProvider())
        assert len(result) == 3
        assert result[0].text == texts[0]
        assert result[1].text == texts[1]
        assert result[2].text == texts[2]

    def test_timestamps_from_fps(self, tmp_path: Path) -> None:
        for i in range(3):
            (tmp_path / f"frame_{i:04d}.png").write_bytes(b"fake")

        texts = [
            "Step one: wake up early every day",
            "Step two: exercise for thirty minutes",
            "Step three: read before bed tonight",
        ]

        class UniqueProvider:
            def __init__(self) -> None:
                self._count = 0

            def extract_text(self, frame_path: Path) -> list[tuple[str, float]]:
                idx = self._count
                self._count += 1
                return [(texts[idx], 0.9)]

        result = extract_text_from_frames(tmp_path, provider=UniqueProvider(), fps=2.0)
        assert result[0].first_seen_at == 0.0
        assert result[1].first_seen_at == 0.5
        assert result[2].first_seen_at == 1.0

    def test_skips_empty_text(self, tmp_path: Path) -> None:
        (tmp_path / "frame_0000.png").write_bytes(b"fake")

        class EmptyProvider:
            def extract_text(self, frame_path: Path) -> list[tuple[str, float]]:
                return [("  ", 0.9), ("", 0.8), ("Real text", 0.95)]

        result = extract_text_from_frames(tmp_path, provider=EmptyProvider())
        assert len(result) == 1
        assert result[0].text == "Real text"
