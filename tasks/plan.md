# Work Plan

**Last updated:** 2026-06-10

## Feature: Instagram Reel Screen-Capture Transcription Pipeline

**Goal:** Build a screen-capture-based transcription pipeline as the primary method for Instagram Reels. Captures both text overlays (OCR) and spoken words (Whisper). yt-dlp remains primary for YouTube and other platforms.

**Use case:** Capture useful information from Reels for second brain / content reuse.

## In Progress
<!-- Nothing yet — awaiting /architect before implementation -->

## Up Next

| Priority | Task | Size | Notes |
|---|---|---|---|
| 1 | Local file support | Small (2 files) | `transclipt ./video.mp4` skips download → straight to Whisper. No blockers. |
| 2 | Patchright browser capture engine | Medium (new module) | Opens Instagram URL in Patchright, plays Reel, captures frames at 1-2fps. Persistent session for login. |
| 3 | Apple Vision OCR for text overlays | Medium (new module) | Extracts text from captured frames via pyobjc-framework-Vision. Deduplicates across frames. |
| 4 | Audio capture via ScreenCaptureKit | Medium-Large (Swift CLI + Python wrapper) | Small Swift helper captures browser-window audio → WAV. Python calls it during Reel playback. |
| 5 | Combined transcript pipeline | Small (1 file) | Merges OCR text + Whisper audio transcript into unified output. |
| 6 | Platform routing in CLI | Small (2 files) | Instagram → Patchright (primary), yt-dlp (fallback). YouTube/others → yt-dlp (primary). |
| 7 | Tests for new pipeline | Medium | Unit + integration tests for each new module. 80%+ coverage. TDD throughout. |

## Dependency Chain
- Task 1 is independent — can ship immediately
- Tasks 2→3→4→5 build sequentially
- Task 6 wires everything together
- Task 7 runs alongside each task (TDD)

## Architecture
- Platform routing: Instagram → screen capture (primary), yt-dlp (fallback)
- YouTube/TikTok/X/others → yt-dlp (primary)
- Screen capture: Patchright (Playwright fork) + persistent browser session
- OCR: Apple Vision framework via pyobjc
- Audio capture: ScreenCaptureKit via Swift CLI helper
- Transcription: faster-whisper (existing)

## Backlog
<!-- Future enhancements -->
- [ ] iOS Shortcut for share-sheet → AirDrop → auto-transcribe workflow
- [ ] Watch-folder mode (auto-transcribe files dropped into a directory)
- [ ] Apple SpeechAnalyzer integration (macOS 26+, faster than Whisper)

## Done (this cycle)
- [x] Prototype — Modular Typer CLI (merged)
- [x] CI setup (merged PR #3)
- [x] Unit tests (merged PR #2)
- [x] Landing page (merged PR #4)
- [x] Output folder (merged PR #10)
- [x] Auto browser cookies (merged PR #11)
