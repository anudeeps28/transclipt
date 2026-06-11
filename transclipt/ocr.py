"""OCR extraction from video frames with pluggable providers."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class OcrBlock:
    text: str
    confidence: float
    first_seen_at: float


class OcrProvider(Protocol):
    def extract_text(self, frame_path: Path) -> list[tuple[str, float]]:
        """Return list of (text, confidence) pairs from a frame."""
        ...


class AppleVisionProvider:
    """OCR using macOS Apple Vision framework (free, on-device)."""

    def extract_text(self, frame_path: Path) -> list[tuple[str, float]]:
        import Vision
        from Cocoa import NSURL

        image_url = NSURL.fileURLWithPath_(str(frame_path))
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)

        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(
            image_url, {}
        )
        success = handler.performRequests_error_([request], None)
        if not success[0]:
            return []

        results: list[tuple[str, float]] = []
        for observation in request.results():
            candidates = observation.topCandidates_(1)
            if candidates:
                candidate = candidates[0]
                results.append((candidate.string(), candidate.confidence()))

        return results


class NoopProvider:
    """Fallback provider that returns no text (for non-macOS platforms)."""

    def extract_text(self, frame_path: Path) -> list[tuple[str, float]]:
        return []


def get_provider(name: str = "vision") -> OcrProvider:
    if name == "vision":
        try:
            import Vision  # noqa: F401
            return AppleVisionProvider()
        except ImportError:
            return NoopProvider()
    elif name == "noop":
        return NoopProvider()
    else:
        raise ValueError(
            f"Unknown OCR provider '{name}'. "
            f"Available: vision, noop"
        )


def _is_duplicate(new_text: str, seen_texts: list[str], threshold: float = 0.85) -> bool:
    for seen in seen_texts:
        ratio = difflib.SequenceMatcher(None, new_text.lower(), seen.lower()).ratio()
        if ratio >= threshold:
            return True
    return False


def extract_text_from_frames(
    frames_dir: Path,
    provider: OcrProvider | None = None,
    fps: float = 1.0,
) -> tuple[OcrBlock, ...]:
    if provider is None:
        provider = get_provider()

    frame_files = sorted(frames_dir.glob("frame_*.png"))
    if not frame_files:
        return ()

    seen_texts: list[str] = []
    blocks: list[OcrBlock] = []

    for i, frame_path in enumerate(frame_files):
        timestamp = i / fps
        results = provider.extract_text(frame_path)

        for text, confidence in results:
            cleaned = text.strip()
            if not cleaned:
                continue
            if _is_duplicate(cleaned, seen_texts):
                continue

            seen_texts.append(cleaned)
            blocks.append(OcrBlock(
                text=cleaned,
                confidence=confidence,
                first_seen_at=timestamp,
            ))

    return tuple(blocks)
