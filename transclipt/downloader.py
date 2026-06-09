"""Download audio from URLs using yt-dlp (and spotdl for Spotify)."""

from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp


@dataclass(frozen=True)
class DownloadResult:
    audio_path: Path
    title: str
    source_url: str


_SPOTIFY_PATTERN = re.compile(r"https?://open\.spotify\.com/")

_AUTH_REQUIRED_DOMAINS = frozenset({
    "instagram.com",
    "www.instagram.com",
    "tiktok.com",
    "www.tiktok.com",
    "x.com",
    "twitter.com",
    "www.twitter.com",
})

_AUTH_ERROR_PATTERNS = (
    "login required",
    "sign in to confirm",
    "sent an empty media response",
    "cookies",
)

_BROWSERS_TO_TRY = ("chrome", "firefox", "brave", "edge", "safari", "opera", "chromium")


def is_spotify_url(url: str) -> bool:
    return bool(_SPOTIFY_PATTERN.match(url))


def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.hostname or ""


def _needs_auth(url: str) -> bool:
    return _extract_domain(url) in _AUTH_REQUIRED_DOMAINS


def _is_auth_error(error_message: str) -> bool:
    lower = error_message.lower()
    return any(pattern in lower for pattern in _AUTH_ERROR_PATTERNS)


def _find_working_browser(url: str, ydl_opts: dict) -> str | None:
    for browser in _BROWSERS_TO_TRY:
        try:
            opts = {**ydl_opts, "cookiesfrombrowser": (browser,), "skip_download": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=False)
            return browser
        except Exception:
            continue
    return None


def download_audio(
    url: str,
    output_dir: Path | None = None,
    cookies_file: Path | None = None,
) -> DownloadResult:
    if is_spotify_url(url):
        return _download_spotify(url, output_dir)
    return _download_ytdlp(url, output_dir, cookies_file)


def _download_ytdlp(
    url: str,
    output_dir: Path | None,
    cookies_file: Path | None = None,
) -> DownloadResult:
    work_dir = output_dir or Path(tempfile.mkdtemp(prefix="transclipt_"))
    output_template = str(work_dir / "%(title)s.%(ext)s")

    ydl_opts: dict = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }

    if cookies_file:
        ydl_opts["cookiefile"] = str(cookies_file)

    needs_auth = _needs_auth(url)

    if needs_auth and not cookies_file:
        browser = _find_working_browser(url, ydl_opts)
        if browser:
            ydl_opts["cookiesfrombrowser"] = (browser,)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "untitled")
    except Exception as err:
        if not cookies_file and _is_auth_error(str(err)):
            browser = _find_working_browser(url, ydl_opts)
            if browser:
                ydl_opts["cookiesfrombrowser"] = (browser,)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get("title", "untitled")
            else:
                domain = _extract_domain(url)
                raise RuntimeError(
                    f"This URL requires login to access. "
                    f"Couldn't find an active {domain} session in your browsers. "
                    f"Please log into {domain} in Chrome or Firefox and try again. "
                    f"Alternatively, use --cookies <file> with an exported cookies.txt file."
                ) from err
        else:
            raise

    audio_files = list(work_dir.glob("*.mp3"))
    if not audio_files:
        raise RuntimeError(f"No audio file produced for {url}")

    return DownloadResult(
        audio_path=audio_files[0],
        title=title,
        source_url=url,
    )


def _download_spotify(url: str, output_dir: Path | None) -> DownloadResult:
    try:
        import spotdl  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "Spotify support requires spotdl. Install with: pip install transclipt[spotify]"
        )

    work_dir = output_dir or Path(tempfile.mkdtemp(prefix="transclipt_spotify_"))

    result = subprocess.run(
        ["spotdl", "download", url, "--output", str(work_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"spotdl failed: {result.stderr}")

    audio_files = list(work_dir.glob("*.mp3")) + list(work_dir.glob("*.m4a"))
    if not audio_files:
        raise RuntimeError(f"No audio file produced for {url}")

    title = audio_files[0].stem
    return DownloadResult(
        audio_path=audio_files[0],
        title=title,
        source_url=url,
    )
