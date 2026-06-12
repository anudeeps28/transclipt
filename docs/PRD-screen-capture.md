# PRD: Screen-Capture Instagram Reel Transcription

**Status:** Draft
**Date:** 2026-06-10
**Author:** Anudeep Sharma

## Problem Statement

The current yt-dlp-based approach for Instagram Reels has two issues:
1. **Reliability** — yt-dlp's Instagram extractor frequently breaks (empty responses, rate limits) as Instagram changes their API
2. **Incomplete capture** — yt-dlp only downloads audio, missing text overlays that many info-Reels rely on (tips, lists, key points displayed on screen)

The user's goal is to capture useful information from Instagram Reels to add to their second brain and reuse in their content. Many valuable Reels are text-overlay style where the key information is displayed visually, not spoken.

## Solution

Build a screen-capture-based transcription pipeline that:
1. Opens the Reel in a real browser (like a normal user)
2. Captures video frames for OCR of text overlays
3. Captures audio for speech-to-text transcription
4. Combines both into a unified transcript

This is the primary path for Instagram. yt-dlp remains primary for YouTube and other platforms.

## User Stories

### US-1: Transcribe Instagram Reel via screen capture
**As a** content creator, **I want to** paste an Instagram Reel URL and get a transcript that includes both spoken words and text overlays, **so that** I can save useful information to my second brain.

**Acceptance criteria:**
- `transclipt https://www.instagram.com/reel/xyz` uses screen capture for Instagram URLs
- Browser opens (headless by default), plays the Reel, captures content
- Output includes text overlays (OCR) and spoken words (Whisper)
- Persistent browser session — login once, reuse across runs
- Falls back to yt-dlp if screen capture fails

### US-2: Transcribe a local video/audio file
**As a** user, **I want to** pass a local file path instead of a URL, **so that** I can transcribe screen recordings or downloaded videos without needing yt-dlp.

**Acceptance criteria:**
- `transclipt ./my_reel.mp4` detects the input is a file path
- Skips the download step entirely
- Transcribes audio via Whisper
- Supports common formats: mp4, mp3, wav, m4a, webm

### US-3: First-time Instagram login
**As a** user, **I want to** log into Instagram once in the capture browser, **so that** subsequent runs don't require re-authentication.

**Acceptance criteria:**
- First run: browser opens in headed mode for manual login
- Session persisted to disk (Patchright persistent context)
- Subsequent runs: headless, reuses saved session
- If session expires: prompts user to re-login

### US-4: Platform-aware routing
**As a** user, **I want** the tool to automatically choose the best capture method per platform, **so that** I don't have to think about which method to use.

**Acceptance criteria:**
- Instagram URLs → screen capture pipeline (primary), yt-dlp (fallback)
- YouTube URLs → yt-dlp (primary)
- TikTok, X, other URLs → yt-dlp (primary)
- `--method capture|ytdlp` flag to override auto-routing

## Non-Functional Requirements

### NFR-1: Performance
- Screen capture takes approximately real-time (Reel duration + 5-10s setup/teardown)
- OCR processing: < 2 seconds per frame
- Total pipeline for a 60-second Reel: < 90 seconds

### NFR-2: Platform support
- Screen capture features: macOS only (Apple Vision, ScreenCaptureKit)
- yt-dlp path: cross-platform (existing behavior unchanged)
- Graceful degradation: on non-macOS, screen capture unavailable, yt-dlp used for everything

### NFR-3: Resource usage
- Browser instance: ~200-400MB RAM during capture, released after
- No persistent background processes
- Swift audio helper: minimal, started/stopped per capture session

### NFR-4: Reliability
- If headless is blocked by Instagram, auto-retry in headed mode
- If screen capture fails entirely, fall back to yt-dlp
- Clear error messages when dependencies are missing (Patchright, Swift toolchain)

## Technical Constraints

- Python 3.10+
- macOS 14+ for ScreenCaptureKit audio capture
- macOS 12+ for Apple Vision OCR
- Patchright (Playwright fork) for browser automation
- Swift CLI helper for ScreenCaptureKit audio capture (compiled binary)
- pyobjc-framework-Vision for OCR
- faster-whisper for audio transcription (existing dependency)

## Out of Scope

- iOS Shortcut integration
- Watch-folder auto-transcribe mode
- Non-Instagram screen capture (YouTube, TikTok via screen capture)
- Real-time streaming transcription
- Multi-Reel batch capture in parallel
