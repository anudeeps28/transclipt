"""Tests for transclipt.capturer module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from transclipt.capturer import (
    CaptureFrameResult,
    LoginRequiredError,
    _ensure_session_dir,
    _extract_title,
    _is_login_wall,
)


class TestCaptureFrameResult:
    def test_frozen(self, tmp_path: Path) -> None:
        result = CaptureFrameResult(
            frames_dir=tmp_path,
            frame_count=10,
            audio_path=None,
            title="Test Reel",
            source_url="https://www.instagram.com/reel/abc",
        )
        with pytest.raises(AttributeError):
            result.title = "changed"  # type: ignore[misc]

    def test_fields(self, tmp_path: Path) -> None:
        audio_file = tmp_path / "audio.wav"
        result = CaptureFrameResult(
            frames_dir=tmp_path,
            frame_count=5,
            audio_path=audio_file,
            title="My Reel",
            source_url="https://www.instagram.com/reel/xyz",
        )
        assert result.frames_dir == tmp_path
        assert result.frame_count == 5
        assert result.audio_path == audio_file
        assert result.title == "My Reel"
        assert result.source_url == "https://www.instagram.com/reel/xyz"


class TestEnsureSessionDir:
    def test_creates_directory(self, tmp_path: Path) -> None:
        test_dir = tmp_path / ".transclipt" / "browser"
        with patch("transclipt.capturer._SESSION_DIR", test_dir):
            from transclipt.capturer import _ensure_session_dir
            result = _ensure_session_dir()
            assert result.exists()
            assert result.is_dir()


class TestExtractTitle:
    def test_returns_og_title(self) -> None:
        page = MagicMock()
        page.evaluate.return_value = "5 Morning Habits That Changed My Life"
        title = _extract_title(page, "https://www.instagram.com/reel/abc")
        assert title == "5 Morning Habits That Changed My Life"

    def test_falls_back_to_url_slug(self) -> None:
        page = MagicMock()
        page.evaluate.return_value = "Instagram"
        title = _extract_title(page, "https://www.instagram.com/reel/abc123")
        assert title == "abc123"

    def test_handles_empty_title(self) -> None:
        page = MagicMock()
        page.evaluate.return_value = ""
        title = _extract_title(page, "https://www.instagram.com/reel/def456")
        assert title == "def456"

    def test_handles_none_title(self) -> None:
        page = MagicMock()
        page.evaluate.return_value = None
        title = _extract_title(page, "https://www.instagram.com/reel/ghi789")
        assert title == "ghi789"


class TestIsLoginWall:
    def test_detects_login_wall(self) -> None:
        page = MagicMock()
        page.evaluate.return_value = True
        assert _is_login_wall(page) is True

    def test_no_login_wall(self) -> None:
        page = MagicMock()
        page.evaluate.return_value = False
        assert _is_login_wall(page) is False


class TestLoginRequiredError:
    def test_is_exception(self) -> None:
        err = LoginRequiredError("test message")
        assert isinstance(err, Exception)
        assert str(err) == "test message"


class TestCaptureReel:
    @patch("patchright.sync_api.sync_playwright")
    def test_login_wall_raises_error(self, mock_pw: MagicMock, tmp_path: Path) -> None:
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = MagicMock()
        mock_browser.chromium.launch_persistent_context.return_value = mock_context

        mock_pw.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_pw.return_value.__exit__ = MagicMock(return_value=False)

        mock_page.evaluate.side_effect = lambda js: True if "Log in" in js else None

        from transclipt.capturer import capture_reel

        with pytest.raises(LoginRequiredError, match="Instagram login required"):
            capture_reel(
                url="https://www.instagram.com/reel/abc",
                output_dir=tmp_path,
            )

    @patch("transclipt.capturer.time")
    @patch("patchright.sync_api.sync_playwright")
    def test_captures_frames_successfully(self, mock_pw: MagicMock, mock_time: MagicMock, tmp_path: Path) -> None:
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = MagicMock()
        mock_browser.chromium.launch_persistent_context.return_value = mock_context

        mock_pw.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_pw.return_value.__exit__ = MagicMock(return_value=False)

        call_count = 0

        def mock_evaluate(js: str):
            nonlocal call_count
            if "Log in" in js:
                return False
            if "og:title" in js:
                return "Test Reel Title"
            if "duration" in js:
                return 3.0
            if "currentTime" in js:
                call_count += 1
                return 3.0 if call_count > 1 else 1.0
            if "play" in js:
                return None
            return None

        mock_page.evaluate.side_effect = mock_evaluate
        mock_page.wait_for_selector.return_value = None
        mock_page.screenshot.return_value = None

        mock_time.monotonic.side_effect = [0.0, 1.0, 15.0]
        mock_time.sleep.return_value = None

        from transclipt.capturer import capture_reel

        result = capture_reel(
            url="https://www.instagram.com/reel/abc",
            output_dir=tmp_path,
        )

        assert result.title == "Test Reel Title"
        assert result.source_url == "https://www.instagram.com/reel/abc"
        assert result.frames_dir == tmp_path / "frames"
        assert mock_page.screenshot.called
