# CONTEXT.md

Domain glossary, module map, and codebase conventions.
Read by Claude Code agents before grilling, architecture proposals, or refactor sessions — so they anchor suggestions in the team's shared vocabulary.

**How to maintain:** Update as understanding evolves. Add terms when they stabilize. ADRs record *why* decisions were made; this file records *what* is true now.

---

## Domain glossary

| Term | Definition |
|---|---|
| riptext | CLI tool and Python package that transcribes video/audio URLs to text |
| segment | A contiguous block of transcribed speech with start/end timestamps |
| yt-dlp | External tool that downloads audio from 1000+ video platforms |
| faster-whisper | CTranslate2-accelerated Whisper model for speech-to-text transcription |
| spotdl | Optional external tool for downloading Spotify tracks (installed via extras) |
| VAD | Voice Activity Detection — filters silence before transcription to improve accuracy |

---

## Module map

One line per module or service. What it owns and what it explicitly does not.

| Module / Service | Owns | Does NOT own |
|---|---|---|
| riptext.cli | CLI argument parsing, orchestration of download-transcribe-format pipeline, progress display | Audio download logic, transcription logic, output formatting |
| riptext.downloader | Downloading audio from URLs via yt-dlp and spotdl, producing mp3 files | Transcription, formatting, temp directory lifecycle (caller manages) |
| riptext.transcriber | Loading Whisper models, transcribing audio files, returning segments with timestamps | Downloading, formatting, file I/O for final output |
| riptext.formatter | Converting TranscriptionResult to txt/md/srt/json string formats | File I/O (caller writes to disk) |

---

## Codebase conventions

Patterns that apply here but might surprise a reader from another project. The "why" for each lives in `docs/adr/` if it was a hard decision.

- Frozen dataclasses for all data transfer objects (DownloadResult, Segment, TranscriptionResult)
- Typer for CLI with Rich for terminal output
- Temp directories created by caller, cleaned up in finally blocks
- Model caching in module-level dict to avoid reloading Whisper models

---

## See also

- `docs/adr/` — Architectural Decision Records (why decisions were made)
- `docs/adr/README.md` — When to write an ADR vs. update this file
