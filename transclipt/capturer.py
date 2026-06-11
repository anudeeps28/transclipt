"""Capture Instagram Reels via Patchright browser automation."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from patchright.sync_api import sync_playwright, Page, BrowserContext


_SESSION_DIR = Path.home() / ".transclipt" / "browser"

_INSTAGRAM_DOMAINS = frozenset({
    "instagram.com",
    "www.instagram.com",
})


@dataclass(frozen=True)
class CaptureFrameResult:
    frames_dir: Path
    frame_count: int
    audio_path: Path | None
    title: str
    source_url: str


def _ensure_session_dir() -> Path:
    _SESSION_DIR.mkdir(parents=True, exist_ok=True)
    _SESSION_DIR.chmod(0o700)
    return _SESSION_DIR


def _wait_for_video(page: Page, timeout_ms: int = 15000) -> None:
    page.wait_for_selector("video", timeout=timeout_ms)


def _get_video_duration(page: Page) -> float:
    return page.evaluate("""() => {
        const video = document.querySelector('video');
        if (!video || isNaN(video.duration)) return 0;
        return video.duration;
    }""")


def _play_video(page: Page) -> None:
    page.evaluate("""() => {
        const video = document.querySelector('video');
        if (video) {
            video.muted = false;
            video.play();
        }
    }""")


def _get_video_current_time(page: Page) -> float:
    return page.evaluate("""() => {
        const video = document.querySelector('video');
        if (!video) return 0;
        return video.currentTime;
    }""")


def _extract_title(page: Page, url: str) -> str:
    title = page.evaluate("""() => {
        const meta = document.querySelector('meta[property="og:title"]');
        if (meta) return meta.getAttribute('content');
        return document.title;
    }""")
    if title and title.strip() and title.strip() != "Instagram":
        return title.strip()
    return url.split("/")[-1] or "instagram_reel"


def _is_login_wall(page: Page) -> bool:
    return page.evaluate("""() => {
        const text = document.body?.innerText || '';
        return text.includes('Log in') && text.includes('Sign up') && !document.querySelector('video');
    }""")


def _capture_frames(page: Page, frames_dir: Path, duration: float, fps: float = 1.0) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    interval = 1.0 / fps
    frame_count = 0
    start_time = time.monotonic()

    while True:
        current_time = _get_video_current_time(page)
        if current_time >= duration - 0.5:
            break
        if time.monotonic() - start_time > duration + 10:
            break

        frame_path = frames_dir / f"frame_{frame_count:04d}.png"
        page.screenshot(path=str(frame_path))
        frame_count += 1

        time.sleep(interval)

    if frame_count == 0:
        frame_path = frames_dir / "frame_0000.png"
        page.screenshot(path=str(frame_path))
        frame_count = 1

    return frame_count


def _get_browser_pid(context: BrowserContext) -> int | None:
    try:
        browser = context.browser
        if browser:
            return browser.process.pid  # type: ignore[union-attr]
    except Exception:
        pass
    return None


def _start_audio_capture(output_dir: Path, duration: float, pid: int | None) -> Path | None:
    try:
        from transclipt.audio_capture import capture_audio, is_available
    except ImportError:
        return None

    if not is_available():
        return None

    audio_path = output_dir / "audio.wav"
    success = capture_audio(audio_path, duration, pid)
    return audio_path if success else None


def capture_reel(
    url: str,
    output_dir: Path,
    fps: float = 1.0,
    headed: bool = False,
    capture_audio: bool = True,
) -> CaptureFrameResult:
    session_dir = _ensure_session_dir()
    frames_dir = output_dir / "frames"

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=not headed,
            channel="chrome",
            viewport={"width": 430, "height": 932},
            args=["--disable-blink-features=AutomationControlled"],
        )

        try:
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            if _is_login_wall(page):
                context.close()
                raise LoginRequiredError(
                    "Instagram login required. Run: transclipt --login"
                )

            _wait_for_video(page)
            title = _extract_title(page, url)

            duration = _get_video_duration(page)
            if duration <= 0:
                time.sleep(2)
                duration = _get_video_duration(page)
            if duration <= 0:
                duration = 30.0

            _play_video(page)
            time.sleep(0.5)

            audio_path = None
            if capture_audio:
                browser_pid = _get_browser_pid(context)
                import threading
                audio_result: list[Path | None] = [None]

                def _audio_thread() -> None:
                    audio_result[0] = _start_audio_capture(output_dir, duration + 1, browser_pid)

                audio_thread = threading.Thread(target=_audio_thread)
                audio_thread.start()

            frame_count = _capture_frames(page, frames_dir, duration, fps)

            if capture_audio:
                audio_thread.join(timeout=duration + 35)  # type: ignore[possibly-undefined]
                audio_path = audio_result[0]  # type: ignore[possibly-undefined]

            return CaptureFrameResult(
                frames_dir=frames_dir,
                frame_count=frame_count,
                audio_path=audio_path,
                title=title,
                source_url=url,
            )
        finally:
            context.close()


def login_interactive() -> None:
    session_dir = _ensure_session_dir()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            channel="chrome",
            viewport={"width": 430, "height": 932},
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = context.new_page()
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")

        print("Log into Instagram in the browser window.")
        print("Press Enter here when done...")
        input()

        context.close()


class LoginRequiredError(Exception):
    pass
