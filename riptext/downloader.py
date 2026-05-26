"""Download audio from URLs using yt-dlp (and spotdl for Spotify)."""

from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yt_dlp


@dataclass(frozen=True)
class DownloadResult:
    audio_path: Path
    title: str
    source_url: str


_SPOTIFY_PATTERN = re.compile(r"https?://open\.spotify\.com/")


def is_spotify_url(url: str) -> bool:
    return bool(_SPOTIFY_PATTERN.match(url))


def download_audio(url: str, output_dir: Path | None = None) -> DownloadResult:
    if is_spotify_url(url):
        return _download_spotify(url, output_dir)
    return _download_ytdlp(url, output_dir)


def _download_ytdlp(url: str, output_dir: Path | None) -> DownloadResult:
    work_dir = output_dir or Path(tempfile.mkdtemp(prefix="riptext_"))
    output_template = str(work_dir / "%(title)s.%(ext)s")

    ydl_opts = {
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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "untitled")

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
            "Spotify support requires spotdl. Install with: pip install riptext[spotify]"
        )

    work_dir = output_dir or Path(tempfile.mkdtemp(prefix="riptext_spotify_"))

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
