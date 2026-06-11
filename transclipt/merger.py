"""Merge OCR text overlays with Whisper audio transcription."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transclipt.ocr import OcrBlock
    from transclipt.transcriber import TranscriptionResult


@dataclass(frozen=True)
class CaptureResult:
    ocr_texts: tuple[OcrBlock, ...]
    transcription: TranscriptionResult | None
    title: str
    source_url: str
    combined_text: str = field(init=False)

    def __post_init__(self) -> None:
        parts: list[str] = []

        if self.ocr_texts:
            ocr_lines = "\n".join(block.text for block in self.ocr_texts)
            parts.append(ocr_lines)

        if self.transcription and self.transcription.full_text.strip():
            parts.append(self.transcription.full_text.strip())

        object.__setattr__(self, "combined_text", "\n\n".join(parts))


def merge_results(
    ocr_texts: tuple[OcrBlock, ...],
    transcription: TranscriptionResult | None,
    title: str,
    source_url: str,
) -> CaptureResult:
    return CaptureResult(
        ocr_texts=ocr_texts,
        transcription=transcription,
        title=title,
        source_url=source_url,
    )
