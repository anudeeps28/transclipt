"""Tests for transclipt.downloader module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from transclipt.downloader import (
    DownloadResult,
    download_audio,
    is_spotify_url,
)


class TestIsSpotifyUrl:
    def test_spotify_track(self) -> None:
        assert is_spotify_url("https://open.spotify.com/track/abc123") is True

    def test_spotify_episode(self) -> None:
        assert is_spotify_url("https://open.spotify.com/episode/xyz") is True

    def test_http_spotify(self) -> None:
        assert is_spotify_url("http://open.spotify.com/track/abc") is True

    def test_youtube_url(self) -> None:
        assert is_spotify_url("https://www.youtube.com/watch?v=abc") is False

    def test_instagram_url(self) -> None:
        assert is_spotify_url("https://www.instagram.com/reel/abc") is False

    def test_empty_string(self) -> None:
        assert is_spotify_url("") is False


class TestDownloadYtdlp:
    @patch("transclipt.downloader.yt_dlp.YoutubeDL")
    def test_successful_download(self, mock_ydl_class: MagicMock, tmp_path: Path) -> None:
        audio_file = tmp_path / "Test Video.mp3"
        audio_file.write_text("fake audio")

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Test Video"}
        mock_ydl_class.return_value = mock_ydl

        result = download_audio("https://www.youtube.com/watch?v=abc", output_dir=tmp_path)

        assert isinstance(result, DownloadResult)
        assert result.title == "Test Video"
        assert result.source_url == "https://www.youtube.com/watch?v=abc"
        assert result.audio_path == audio_file

    @patch("transclipt.downloader.yt_dlp.YoutubeDL")
    def test_no_audio_produced_raises(self, mock_ydl_class: MagicMock, tmp_path: Path) -> None:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Test"}
        mock_ydl_class.return_value = mock_ydl

        with pytest.raises(RuntimeError, match="No audio file produced"):
            download_audio("https://www.youtube.com/watch?v=abc", output_dir=tmp_path)

    @patch("transclipt.downloader.yt_dlp.YoutubeDL")
    def test_untitled_video(self, mock_ydl_class: MagicMock, tmp_path: Path) -> None:
        audio_file = tmp_path / "something.mp3"
        audio_file.write_text("fake audio")

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {}
        mock_ydl_class.return_value = mock_ydl

        result = download_audio("https://www.youtube.com/watch?v=abc", output_dir=tmp_path)
        assert result.title == "untitled"


class TestDownloadSpotify:
    @patch("transclipt.downloader.subprocess.run")
    def test_successful_spotify_download(self, mock_run: MagicMock, tmp_path: Path) -> None:
        audio_file = tmp_path / "Song Title.mp3"
        audio_file.write_text("fake audio")

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with patch.dict("sys.modules", {"spotdl": MagicMock()}):
            result = download_audio(
                "https://open.spotify.com/track/abc123", output_dir=tmp_path
            )

        assert isinstance(result, DownloadResult)
        assert result.title == "Song Title"
        assert result.audio_path == audio_file

    @patch("transclipt.downloader.subprocess.run")
    def test_spotdl_failure_raises(self, mock_run: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="auth failed")

        with patch.dict("sys.modules", {"spotdl": MagicMock()}):
            with pytest.raises(RuntimeError, match="spotdl failed"):
                download_audio(
                    "https://open.spotify.com/track/abc123", output_dir=tmp_path
                )

    def test_spotdl_not_installed_raises(self, tmp_path: Path) -> None:
        with patch.dict("sys.modules", {"spotdl": None}):
            with pytest.raises(RuntimeError, match="Spotify support requires spotdl"):
                download_audio(
                    "https://open.spotify.com/track/abc123", output_dir=tmp_path
                )
