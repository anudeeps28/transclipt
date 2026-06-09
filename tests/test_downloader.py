"""Tests for transclipt.downloader module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from transclipt.downloader import (
    DownloadResult,
    _extract_domain,
    _is_auth_error,
    _needs_auth,
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


class TestExtractDomain:
    def test_instagram(self) -> None:
        assert _extract_domain("https://www.instagram.com/reel/abc") == "www.instagram.com"

    def test_youtube(self) -> None:
        assert _extract_domain("https://www.youtube.com/watch?v=abc") == "www.youtube.com"

    def test_tiktok(self) -> None:
        assert _extract_domain("https://www.tiktok.com/@user/video/123") == "www.tiktok.com"

    def test_empty_string(self) -> None:
        assert _extract_domain("") == ""

    def test_bare_domain(self) -> None:
        assert _extract_domain("https://x.com/status/123") == "x.com"


class TestNeedsAuth:
    def test_instagram_needs_auth(self) -> None:
        assert _needs_auth("https://www.instagram.com/reel/abc") is True

    def test_instagram_without_www(self) -> None:
        assert _needs_auth("https://instagram.com/reel/abc") is True

    def test_tiktok_needs_auth(self) -> None:
        assert _needs_auth("https://www.tiktok.com/@user/video/123") is True

    def test_twitter_needs_auth(self) -> None:
        assert _needs_auth("https://twitter.com/user/status/123") is True

    def test_x_needs_auth(self) -> None:
        assert _needs_auth("https://x.com/user/status/123") is True

    def test_youtube_no_auth(self) -> None:
        assert _needs_auth("https://www.youtube.com/watch?v=abc") is False

    def test_vimeo_no_auth(self) -> None:
        assert _needs_auth("https://vimeo.com/123") is False


class TestIsAuthError:
    def test_instagram_empty_response(self) -> None:
        assert _is_auth_error("Instagram sent an empty media response") is True

    def test_login_required(self) -> None:
        assert _is_auth_error("ERROR: Login required") is True

    def test_sign_in_prompt(self) -> None:
        assert _is_auth_error("Sign in to confirm you're not a bot") is True

    def test_cookies_mention(self) -> None:
        assert _is_auth_error("use --cookies for authentication") is True

    def test_network_error_not_auth(self) -> None:
        assert _is_auth_error("Network connection refused") is False

    def test_not_found_not_auth(self) -> None:
        assert _is_auth_error("Video not found") is False

    def test_case_insensitive(self) -> None:
        assert _is_auth_error("LOGIN REQUIRED") is True


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

    @patch("transclipt.downloader.yt_dlp.YoutubeDL")
    def test_cookies_file_passed_to_ydl_opts(self, mock_ydl_class: MagicMock, tmp_path: Path) -> None:
        audio_file = tmp_path / "Test.mp3"
        audio_file.write_text("fake audio")
        cookies_file = tmp_path / "cookies.txt"
        cookies_file.write_text("fake cookies")

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Test"}
        mock_ydl_class.return_value = mock_ydl

        download_audio(
            "https://www.youtube.com/watch?v=abc",
            output_dir=tmp_path,
            cookies_file=cookies_file,
        )

        opts_used = mock_ydl_class.call_args[0][0]
        assert opts_used["cookiefile"] == str(cookies_file)

    @patch("transclipt.downloader._find_working_browser", return_value="chrome")
    @patch("transclipt.downloader.yt_dlp.YoutubeDL")
    def test_instagram_url_tries_browser_cookies(
        self, mock_ydl_class: MagicMock, mock_find_browser: MagicMock, tmp_path: Path
    ) -> None:
        audio_file = tmp_path / "Reel.mp3"
        audio_file.write_text("fake audio")

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Reel"}
        mock_ydl_class.return_value = mock_ydl

        result = download_audio(
            "https://www.instagram.com/reel/abc123",
            output_dir=tmp_path,
        )

        assert result.title == "Reel"
        mock_find_browser.assert_called_once()
        opts_used = mock_ydl_class.call_args[0][0]
        assert opts_used["cookiesfrombrowser"] == ("chrome",)

    @patch("transclipt.downloader._find_working_browser", return_value=None)
    @patch("transclipt.downloader.yt_dlp.YoutubeDL")
    def test_instagram_no_browser_auth_error_raises_helpful_message(
        self, mock_ydl_class: MagicMock, mock_find_browser: MagicMock, tmp_path: Path
    ) -> None:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = Exception("Instagram sent an empty media response")
        mock_ydl_class.return_value = mock_ydl

        with pytest.raises(RuntimeError, match="requires login to access"):
            download_audio(
                "https://www.instagram.com/reel/abc123",
                output_dir=tmp_path,
            )

    @patch("transclipt.downloader._find_working_browser", return_value="firefox")
    @patch("transclipt.downloader.yt_dlp.YoutubeDL")
    def test_auth_error_fallback_retries_with_browser(
        self, mock_ydl_class: MagicMock, mock_find_browser: MagicMock, tmp_path: Path
    ) -> None:
        """Non-auth-listed domain gets auth error, fallback finds browser and retries."""
        audio_file = tmp_path / "Video.mp3"
        audio_file.write_text("fake audio")

        mock_ydl_fail = MagicMock()
        mock_ydl_fail.__enter__ = MagicMock(return_value=mock_ydl_fail)
        mock_ydl_fail.__exit__ = MagicMock(return_value=False)
        mock_ydl_fail.extract_info.side_effect = Exception("Login required")

        mock_ydl_success = MagicMock()
        mock_ydl_success.__enter__ = MagicMock(return_value=mock_ydl_success)
        mock_ydl_success.__exit__ = MagicMock(return_value=False)
        mock_ydl_success.extract_info.return_value = {"title": "Video"}

        mock_ydl_class.side_effect = [mock_ydl_fail, mock_ydl_success]

        result = download_audio(
            "https://some-new-site.com/video/123",
            output_dir=tmp_path,
        )

        assert result.title == "Video"
        mock_find_browser.assert_called_once()

    @patch("transclipt.downloader.yt_dlp.YoutubeDL")
    def test_non_auth_error_not_caught(self, mock_ydl_class: MagicMock, tmp_path: Path) -> None:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = Exception("Network connection refused")
        mock_ydl_class.return_value = mock_ydl

        with pytest.raises(Exception, match="Network connection refused"):
            download_audio("https://www.youtube.com/watch?v=abc", output_dir=tmp_path)


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
