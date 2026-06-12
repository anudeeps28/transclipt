"""Tests for transclipt.audio_capture module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from transclipt.audio_capture import is_available, capture_audio, _BINARY_PATH


class TestIsAvailable:
    @patch("transclipt.audio_capture.sys")
    def test_not_available_on_linux(self, mock_sys: MagicMock) -> None:
        mock_sys.platform = "linux"
        assert is_available() is False

    @patch("transclipt.audio_capture.sys")
    def test_not_available_on_windows(self, mock_sys: MagicMock) -> None:
        mock_sys.platform = "win32"
        assert is_available() is False

    @patch("transclipt.audio_capture._BINARY_PATH")
    @patch("transclipt.audio_capture.sys")
    def test_available_when_binary_exists(self, mock_sys: MagicMock, mock_path: MagicMock) -> None:
        mock_sys.platform = "darwin"
        mock_path.exists.return_value = True
        assert is_available() is True

    @patch("transclipt.audio_capture._try_build")
    @patch("transclipt.audio_capture._BINARY_PATH")
    @patch("transclipt.audio_capture.sys")
    def test_tries_build_when_binary_missing(
        self, mock_sys: MagicMock, mock_path: MagicMock, mock_build: MagicMock
    ) -> None:
        mock_sys.platform = "darwin"
        mock_path.exists.return_value = False
        mock_build.return_value = True
        assert is_available() is True
        mock_build.assert_called_once()


class TestCaptureAudio:
    @patch("transclipt.audio_capture.is_available", return_value=False)
    def test_returns_false_when_unavailable(self, mock_avail: MagicMock, tmp_path: Path) -> None:
        result = capture_audio(tmp_path / "audio.wav", 5.0)
        assert result is False

    @patch("transclipt.audio_capture.subprocess")
    @patch("transclipt.audio_capture.is_available", return_value=True)
    def test_calls_binary_with_correct_args(
        self, mock_avail: MagicMock, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"fake wav")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.run.return_value = mock_result

        result = capture_audio(audio_path, 10.0, pid=12345)

        mock_subprocess.run.assert_called_once()
        call_args = mock_subprocess.run.call_args
        cmd = call_args[0][0]
        assert str(audio_path) in cmd
        assert "10.0" in cmd
        assert "12345" in cmd

    @patch("transclipt.audio_capture.subprocess")
    @patch("transclipt.audio_capture.is_available", return_value=True)
    def test_returns_false_on_failure(
        self, mock_avail: MagicMock, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.run.return_value = mock_result

        result = capture_audio(tmp_path / "audio.wav", 5.0)
        assert result is False
