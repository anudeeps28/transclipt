"""Transcribe audio files using faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from faster_whisper import WhisperModel


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptionResult:
    segments: tuple[Segment, ...]
    language: str
    language_probability: float
    full_text: str = field(init=False)

    def __post_init__(self) -> None:
        joined = " ".join(seg.text.strip() for seg in self.segments)
        object.__setattr__(self, "full_text", joined)


_MODEL_CACHE: dict[str, WhisperModel] = {}


def _get_model(model_size: str, device: str) -> WhisperModel:
    key = f"{model_size}:{device}"
    if key not in _MODEL_CACHE:
        compute_type = "float16" if device == "cuda" else "int8"
        _MODEL_CACHE[key] = WhisperModel(
            model_size, device=device, compute_type=compute_type
        )
    return _MODEL_CACHE[key]


def transcribe(
    audio_path: Path,
    model_size: str = "base",
    language: str | None = None,
    device: str = "auto",
) -> TranscriptionResult:
    model = _get_model(model_size, device)

    segments_gen, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=True,
    )

    segments = tuple(
        Segment(start=seg.start, end=seg.end, text=seg.text)
        for seg in segments_gen
    )

    return TranscriptionResult(
        segments=segments,
        language=info.language,
        language_probability=info.language_probability,
    )
