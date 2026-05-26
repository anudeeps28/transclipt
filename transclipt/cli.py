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
) -> None:
    """Transcribe video/audio URLs to text."""
    if output and len(urls) > 1:
        console.print("[red]Error:[/red] --output can only be used with a single URL.")
        raise typer.Exit(code=1)

    for url in urls:
        _process_url(
            url=url,
            fmt=format.value,
            model_size=model.value,
            language=language,
            output_path=output,
            device=device,
        )


def _process_url(
    url: str,
    fmt: str,
    model_size: str,
    language: str | None,
    output_path: Path | None,
    device: str,
) -> None:
    tmp_dir = Path(tempfile.mkdtemp(prefix="transclipt_"))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading audio...", total=None)
            dl_result = download_audio(url, output_dir=tmp_dir)

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
            safe_title = "".join(
                c if c.isalnum() or c in " -_" else "_" for c in dl_result.title
            )
            dest = Path(f"{safe_title}{get_extension(fmt)}")

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
