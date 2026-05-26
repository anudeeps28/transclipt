"""Format transcription results into various output formats."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transclipt.transcriber import TranscriptionResult


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


def format_output(result: TranscriptionResult, fmt: str) -> str:
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
