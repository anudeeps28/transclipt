"""Format transcription results into various output formats."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from transclipt.merger import CaptureResult
    from transclipt.transcriber import TranscriptionResult

    FormattableResult = Union[TranscriptionResult, CaptureResult]


def to_text(result: TranscriptionResult) -> str:
    return result.full_text


def to_markdown(result: TranscriptionResult) -> str:
    lines = [
        f"# Transcription",
        f"",
        f"**Language:** {result.language} ({result.language_probability:.0%} confidence)",
        f"",
        "---",
        f"",
        result.full_text,
        "",
    ]
    return "\n".join(lines)


def to_srt(result: TranscriptionResult) -> str:
    entries: list[str] = []
    for i, seg in enumerate(result.segments, start=1):
        start = _format_srt_time(seg.start)
        end = _format_srt_time(seg.end)
        entries.append(f"{i}\n{start} --> {end}\n{seg.text.strip()}\n")
    return "\n".join(entries)


def to_json(result: TranscriptionResult) -> str:
    data = {
        "language": result.language,
        "language_probability": result.language_probability,
        "text": result.full_text,
        "segments": [
            {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
            for seg in result.segments
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def _is_capture_result(result: object) -> bool:
    return hasattr(result, "combined_text") and hasattr(result, "ocr_texts")


def capture_to_text(result: CaptureResult) -> str:
    return result.combined_text


def capture_to_markdown(result: CaptureResult) -> str:
    lines = ["# Transcription (Screen Capture)", ""]

    if result.ocr_texts:
        lines.append("## Text Overlays")
        lines.append("")
        for block in result.ocr_texts:
            lines.append(f"- {block.text}")
        lines.append("")

    if result.transcription and result.transcription.full_text.strip():
        lines.append("## Spoken Audio")
        lines.append("")
        lines.append(
            f"**Language:** {result.transcription.language} "
            f"({result.transcription.language_probability:.0%} confidence)"
        )
        lines.append("")
        lines.append(result.transcription.full_text.strip())
        lines.append("")

    return "\n".join(lines)


def capture_to_json(result: CaptureResult) -> str:
    data: dict = {
        "source": "screen_capture",
        "title": result.title,
        "combined_text": result.combined_text,
        "ocr_texts": [
            {
                "text": block.text,
                "confidence": block.confidence,
                "first_seen_at": block.first_seen_at,
            }
            for block in result.ocr_texts
        ],
    }
    if result.transcription:
        data["transcription"] = {
            "language": result.transcription.language,
            "language_probability": result.transcription.language_probability,
            "text": result.transcription.full_text,
            "segments": [
                {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
                for seg in result.transcription.segments
            ],
        }
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_output(result: FormattableResult, fmt: str) -> str:
    if _is_capture_result(result):
        capture_formatters = {
            "txt": capture_to_text,
            "md": capture_to_markdown,
            "srt": lambda r: capture_to_text(r),
            "json": capture_to_json,
        }
        formatter = capture_formatters.get(fmt)
        if formatter is None:
            raise ValueError(f"Unknown format '{fmt}'. Choose from: {', '.join(capture_formatters)}")
        return formatter(result)  # type: ignore[arg-type]

    formatters = {
        "txt": to_text,
        "md": to_markdown,
        "srt": to_srt,
        "json": to_json,
    }
    formatter = formatters.get(fmt)
    if formatter is None:
        raise ValueError(f"Unknown format '{fmt}'. Choose from: {', '.join(formatters)}")
    return formatter(result)


_FORMAT_EXTENSIONS = {"txt": ".txt", "md": ".md", "srt": ".srt", "json": ".json"}


def get_extension(fmt: str) -> str:
    return _FORMAT_EXTENSIONS.get(fmt, ".txt")


def _format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
