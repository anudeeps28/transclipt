"""Tests for transclipt.cli module."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from transclipt.cli import app
from transclipt.downloader import DownloadResult
from transclipt.transcriber import Segment, TranscriptionResult

runner = CliRunner()


def _fake_download(url: str, output_dir: Path | None = None) -> DownloadResult:
    audio_path = (output_dir or Path("/tmp")) / "test.mp3"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_text("fake")
    return DownloadResult(audio_path=audio_path, title="Test Video", source_url=url)


def _fake_transcribe(**kwargs) -> TranscriptionResult:
    return TranscriptionResult(
        segments=(
            Segment(start=0.0, end=2.0, text=" Hello world."),
            Segment(start=2.5, end=4.0, text=" Goodbye."),
        ),
        language="en",
        language_probability=0.99,
    )


class TestCli:
    @patch("transclipt.cli.transcribe", side_effect=lambda **kw: _fake_transcribe(**kw))
    @patch("transclipt.cli.download_audio", side_effect=_fake_download)
    def test_single_url_txt(self, mock_dl: MagicMock, mock_tx: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "out.txt"
        result = runner.invoke(app, [
            "https://www.youtube.com/watch?v=abc",
            "--output", str(output_file),
        ])
        assert result.exit_code == 0
        assert "Done:" in result.output
        assert output_file.exists()
        content = output_file.read_text()
        assert "Hello world." in content

    @patch("transclipt.cli.transcribe", side_effect=lambda **kw: _fake_transcribe(**kw))
    @patch("transclipt.cli.download_audio", side_effect=_fake_download)
    def test_single_url_json(self, mock_dl: MagicMock, mock_tx: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "out.json"
        result = runner.invoke(app, [
            "https://www.youtube.com/watch?v=abc",
            "--format", "json",
            "--output", str(output_file),
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        import json
        data = json.loads(output_file.read_text())
        assert data["language"] == "en"
        assert len(data["segments"]) == 2

    @patch("transclipt.cli.transcribe", side_effect=lambda **kw: _fake_transcribe(**kw))
    @patch("transclipt.cli.download_audio", side_effect=_fake_download)
    def test_single_url_srt(self, mock_dl: MagicMock, mock_tx: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "out.srt"
        result = runner.invoke(app, [
            "https://www.youtube.com/watch?v=abc",
            "--format", "srt",
            "--output", str(output_file),
        ])
        assert result.exit_code == 0
        content = output_file.read_text()
        assert "00:00:00,000 --> 00:00:02,000" in content

    @patch("transclipt.cli.transcribe", side_effect=lambda **kw: _fake_transcribe(**kw))
    @patch("transclipt.cli.download_audio", side_effect=_fake_download)
    def test_single_url_md(self, mock_dl: MagicMock, mock_tx: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "out.md"
        result = runner.invoke(app, [
            "https://www.youtube.com/watch?v=abc",
            "--format", "md",
            "--output", str(output_file),
        ])
        assert result.exit_code == 0
        content = output_file.read_text()
        assert "# Transcription" in content

    def test_output_with_multiple_urls_errors(self) -> None:
        result = runner.invoke(app, [
            "https://url1.com",
            "https://url2.com",
            "--output", "/tmp/out.txt",
        ])
        assert result.exit_code == 1
        assert "--output can only be used with a single URL" in result.output

    def test_no_args_shows_help(self) -> None:
        result = runner.invoke(app, [])
        assert result.exit_code == 2
        assert "Usage:" in result.output

    @patch("transclipt.cli.transcribe", side_effect=lambda **kw: _fake_transcribe(**kw))
    @patch("transclipt.cli.download_audio", side_effect=_fake_download)
    def test_model_option(self, mock_dl: MagicMock, mock_tx: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "out.txt"
        result = runner.invoke(app, [
            "https://www.youtube.com/watch?v=abc",
            "--model", "small",
            "--output", str(output_file),
        ])
        assert result.exit_code == 0
        mock_tx.assert_called_once()
        call_kwargs = mock_tx.call_args
        assert call_kwargs.kwargs.get("model_size") == "small" or "small" in str(call_kwargs)

    @patch("transclipt.cli.transcribe", side_effect=lambda **kw: _fake_transcribe(**kw))
    @patch("transclipt.cli.download_audio", side_effect=_fake_download)
    def test_language_option(self, mock_dl: MagicMock, mock_tx: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "out.txt"
        result = runner.invoke(app, [
            "https://www.youtube.com/watch?v=abc",
            "--language", "hi",
            "--output", str(output_file),
        ])
        assert result.exit_code == 0

    @patch("transclipt.cli.download_audio", side_effect=RuntimeError("Network error"))
    def test_download_error_exits_with_code_1(self, mock_dl: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "out.txt"
        result = runner.invoke(app, [
            "https://www.youtube.com/watch?v=abc",
            "--output", str(output_file),
        ])
        assert result.exit_code == 1
        assert "Error processing" in result.output
