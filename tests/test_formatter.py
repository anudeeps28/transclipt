"""Tests for transclipt.formatter module."""

from __future__ import annotations

import json

import pytest

from transclipt.formatter import (
    _format_srt_time,
    format_output,
    get_extension,
    to_json,
    to_markdown,
    to_srt,
    to_text,
)
from transclipt.transcriber import Segment, TranscriptionResult


@pytest.fixture
def result() -> TranscriptionResult:
    return TranscriptionResult(
        segments=(
            Segment(start=0.0, end=2.5, text=" Hello world."),
            Segment(start=3.0, end=5.5, text=" Goodbye world."),
        ),
        language="en",
        language_probability=0.95,
    )


@pytest.fixture
def empty_result() -> TranscriptionResult:
    return TranscriptionResult(
        segments=(),
        language="en",
        language_probability=0.99,
    )


def test_to_text(result: TranscriptionResult) -> None:
    assert to_text(result) == "Hello world. Goodbye world."


def test_to_markdown(result: TranscriptionResult) -> None:
    output = to_markdown(result)
    assert output.startswith("# Transcription")
    assert "**Language:** en (95% confidence)" in output
    assert "Hello world. Goodbye world." in output


def test_to_srt(result: TranscriptionResult) -> None:
    output = to_srt(result)
    assert "1\n00:00:00,000 --> 00:00:02,500\nHello world." in output
    assert "2\n00:00:03,000 --> 00:00:05,500\nGoodbye world." in output


def test_to_json(result: TranscriptionResult) -> None:
    output = to_json(result)
    data = json.loads(output)
    assert data["language"] == "en"
    assert data["language_probability"] == 0.95
    assert data["text"] == "Hello world. Goodbye world."
    assert len(data["segments"]) == 2
    assert data["segments"][0]["start"] == 0.0
    assert data["segments"][0]["end"] == 2.5
    assert data["segments"][0]["text"] == "Hello world."


def test_format_output_dispatches_correctly(result: TranscriptionResult) -> None:
    assert format_output(result, "txt") == to_text(result)
    assert format_output(result, "md") == to_markdown(result)
    assert format_output(result, "srt") == to_srt(result)
    assert format_output(result, "json") == to_json(result)


def test_format_output_unknown_format(result: TranscriptionResult) -> None:
    with pytest.raises(ValueError, match="Unknown format 'xml'"):
        format_output(result, "xml")


def test_get_extension() -> None:
    assert get_extension("txt") == ".txt"
    assert get_extension("md") == ".md"
    assert get_extension("srt") == ".srt"
    assert get_extension("json") == ".json"
    assert get_extension("unknown") == ".txt"


def test_format_srt_time() -> None:
    assert _format_srt_time(3661.5) == "01:01:01,500"
    assert _format_srt_time(0.0) == "00:00:00,000"


def test_empty_segments(empty_result: TranscriptionResult) -> None:
    assert to_text(empty_result) == ""
    data = json.loads(to_json(empty_result))
    assert data["segments"] == []
    assert data["text"] == ""
