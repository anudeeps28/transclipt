"""CLI entry point using Typer."""

from __future__ import annotations

import shutil
import tempfile
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from transclipt.downloader import download_audio
from transclipt.formatter import format_output, get_extension
from transclipt.transcriber import transcribe

_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".mp4", ".mp3", ".wav", ".m4a", ".webm"})

app = typer.Typer(
    name="transclipt",
    help="Transcribe any video URL to text. Supports YouTube, Instagram, TikTok, Twitter, Spotify, and 1000+ more.",
    no_args_is_help=True,
)

console = Console()


class OutputFormat(str, Enum):
    txt = "txt"
    md = "md"
    srt = "srt"
    json = "json"


class ModelSize(str, Enum):
    tiny = "tiny"
    base = "base"
    small = "small"
    medium = "medium"
    large = "large-v3"


@app.command()
def main(
    urls: Annotated[list[str], typer.Argument(help="One or more video/audio URLs to transcribe")],
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.txt,
    model: Annotated[ModelSize, typer.Option("--model", "-m", help="Whisper model size")] = ModelSize.base,
    language: Annotated[Optional[str], typer.Option("--language", "-l", help="Force language (e.g. en, hi, es)")] = None,
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output file path (default: auto-named)")] = None,
    device: Annotated[str, typer.Option("--device", "-d", help="Device: auto, cpu, or cuda")] = "auto",
    cookies: Annotated[Optional[Path], typer.Option("--cookies", help="Path to cookies.txt file for authenticated downloads")] = None,
) -> None:
    """Transcribe video/audio URLs to text."""
    if output and len(urls) > 1:
        console.print("[red]Error:[/red] --output can only be used with a single URL.")
        raise typer.Exit(code=1)

    if cookies and not cookies.is_file():
        console.print(f"[red]Error:[/red] Cookies file not found: {cookies}")
        raise typer.Exit(code=1)

    for url in urls:
        if _is_local_file(url):
            _process_local_file(
                file_path_str=url,
                fmt=format.value,
                model_size=model.value,
                language=language,
                output_path=output,
                device=device,
            )
        else:
            _process_url(
                url=url,
                fmt=format.value,
                model_size=model.value,
                language=language,
                output_path=output,
                device=device,
                cookies_file=cookies,
            )


def _is_local_file(input_str: str) -> bool:
    path = Path(input_str)
    return path.exists() and path.suffix != ""


def _process_local_file(
    file_path_str: str,
    fmt: str,
    model_size: str,
    language: str | None,
    output_path: Path | None,
    device: str,
) -> None:
    file_path = Path(file_path_str).resolve()

    if not file_path.is_file():
        console.print(f"[red]Error:[/red] File not found: {file_path_str}")
        raise typer.Exit(code=1)

    if file_path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        console.print(
            f"[red]Error:[/red] Unsupported file format: {file_path.suffix}. "
            f"Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}"
        )
        raise typer.Exit(code=1)

    title = file_path.stem

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Transcribing {file_path.name} with {model_size} model...", total=None
            )
            tx_result = transcribe(
                audio_path=file_path,
                model_size=model_size,
                language=language,
                device=device,
            )

            progress.update(task, description="Formatting output...")
            formatted = format_output(tx_result, fmt)

        if output_path:
            dest = output_path
        else:
            output_dir = Path(__file__).resolve().parent.parent / "output"
            output_dir.mkdir(exist_ok=True)
            safe_title = "".join(
                c if c.isalnum() or c in " -_" else "_" for c in title
            )
            dest = output_dir / f"{safe_title}{get_extension(fmt)}"

        dest.write_text(formatted, encoding="utf-8")
        console.print(f"[green]Done:[/green] {dest}")
        console.print(f"  Language: {tx_result.language} ({tx_result.language_probability:.0%})")
        console.print(f"  Segments: {len(tx_result.segments)}")

    except typer.Exit:
        raise
    except Exception as err:
        console.print(f"[red]Error processing {file_path_str}:[/red] {err}")
        raise typer.Exit(code=1)


def _process_url(
    url: str,
    fmt: str,
    model_size: str,
    language: str | None,
    output_path: Path | None,
    device: str,
    cookies_file: Path | None = None,
) -> None:
    tmp_dir = Path(tempfile.mkdtemp(prefix="transclipt_"))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading audio...", total=None)
            dl_result = download_audio(url, output_dir=tmp_dir, cookies_file=cookies_file)

            progress.update(task, description=f"Transcribing with {model_size} model...")
            tx_result = transcribe(
                audio_path=dl_result.audio_path,
                model_size=model_size,
                language=language,
                device=device,
            )

            progress.update(task, description="Formatting output...")
            formatted = format_output(tx_result, fmt)

        if output_path:
            dest = output_path
        else:
            output_dir = Path(__file__).resolve().parent.parent / "output"
            output_dir.mkdir(exist_ok=True)
            safe_title = "".join(
                c if c.isalnum() or c in " -_" else "_" for c in dl_result.title
            )
            dest = output_dir / f"{safe_title}{get_extension(fmt)}"

        dest.write_text(formatted, encoding="utf-8")
        console.print(f"[green]Done:[/green] {dest}")
        console.print(f"  Language: {tx_result.language} ({tx_result.language_probability:.0%})")
        console.print(f"  Segments: {len(tx_result.segments)}")

    except Exception as err:
        console.print(f"[red]Error processing {url}:[/red] {err}")
        raise typer.Exit(code=1)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    app()
