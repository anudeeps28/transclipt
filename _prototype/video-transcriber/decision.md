# Prototype: Video Transcription CLI Tool

**Chosen:** Candidate B — "Modular package with Typer CLI"
**Date:** 2026-05-25
**Question:** What's the best architecture for an open-source CLI tool that transcribes videos from any platform?
**Candidates:** 3 proposed, 1 built (user chose B directly)

## Why Candidate B

The user skipped the A-vs-B comparison and went straight to B. Rationale:

- **Open-source readiness** — modular layout is expected by contributors; single-file scripts don't attract PRs
- **Testability** — each module (downloader, transcriber, formatter) can be unit tested independently
- **Swappability** — transcription engine can be changed (e.g., whisper.cpp, cloud API) by editing one file
- **Professional CLI** — Typer auto-generates `--help`, validates arguments, and supports shell completion

## Architecture

```
riptext/
  __init__.py       — version
  cli.py            — Typer entry point, progress UI (rich)
  downloader.py     — yt-dlp wrapper + spotdl for Spotify
  transcriber.py    — faster-whisper wrapper, model caching
  formatter.py      — txt / md / srt / json output
```

Pipeline: URL -> downloader -> audio file -> transcriber -> segments -> formatter -> output file

## Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Transcription engine | faster-whisper (not openai-whisper) | 4x faster on CPU, lower memory, same models |
| CLI framework | Typer | Auto-help, type validation, rich integration |
| Spotify support | Optional dependency (`pip install riptext[spotify]`) | Avoids forcing spotdl install on users who don't need it |
| Output formats | txt, md, srt, json | Covers plain text, documentation, subtitles, and structured data |
| Temp file cleanup | Always, via finally block | No leftover audio files |
| Data classes | Frozen dataclasses | Immutable results, safe to pass around |

## How to Promote the Winner

1. Move `_prototype/video-transcriber/candidate-b/` contents to the repo root
2. Fill in `tasks/notes.md` with the actual build/test/lint commands
3. Update `CONTEXT.md` with the module map and domain terms
4. Run `/implement` or `/story` to add tests, README, and CI
5. `pip install -e .` to install locally, then test with real URLs
