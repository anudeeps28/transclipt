# transclipt

Transcribe any video URL to text. Supports YouTube, Instagram, TikTok, Twitter/X, Spotify, and 1000+ more sites.

## Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) (required by yt-dlp for audio extraction)

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

## Install

```bash
git clone https://github.com/anudeeps28/transclipt.git
cd transclipt
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

For Spotify support (requires a free Spotify account):

```bash
pip install -e ".[spotify]"
```

## Usage

```bash
# Basic — outputs a .txt file auto-named after the video title
transclipt https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Instagram reel → SRT subtitle file
transclipt https://www.instagram.com/reel/... --format srt

# Markdown output with better model
transclipt <url> --format md --model medium

# Multiple URLs at once
transclipt <url1> <url2> <url3>

# Force language (useful for non-English content)
transclipt <url> --language hi --model small

# Specific output file
transclipt <url> --format json --output result.json
```

### Options

| Flag | Short | Description | Default |
|---|---|---|---|
| `--format` | `-f` | Output format: `txt`, `md`, `srt`, `json` | `txt` |
| `--model` | `-m` | Whisper model: `tiny`, `base`, `small`, `medium`, `large-v3` | `base` |
| `--language` | `-l` | Force language (e.g. `en`, `hi`, `es`) | auto-detect |
| `--output` | `-o` | Output file path | auto-named from video title |
| `--device` | `-d` | Device: `auto`, `cpu`, `cuda` | `auto` |
| `--cookies` | | Path to a cookies.txt file (see [Advanced](#advanced)) | — |

### Model tradeoff

| Model | Speed | Quality | Download size |
|---|---|---|---|
| `tiny` | Fastest | OK for clear speech | ~39 MB |
| `base` | Fast | Good for most content | ~74 MB |
| `small` | Moderate | Noticeably better | ~244 MB |
| `medium` | Slow | Great accuracy | ~769 MB |
| `large-v3` | Slowest | Best accuracy | ~1.5 GB |

First run of each model downloads the weights. Cached after that.

## Sites that require login

Some sites (Instagram, TikTok, Twitter/X) require you to be logged in to access content. transclipt handles this automatically — it reads cookies from your browser so you don't need to do anything extra. Just make sure you're logged into the site in Chrome, Firefox, or another browser on your machine.

On macOS, you may see a system prompt asking to allow access to your browser's cookie storage. Click "Allow" — this is a one-time permission that lets transclipt use your existing login session.

If automatic browser cookies don't work, see the [Advanced](#advanced) section below.

## Supported sites

- YouTube
- Instagram Reels
- TikTok
- Twitter/X
- Spotify (requires `pip install -e ".[spotify]"`)
- Facebook, Reddit, Vimeo, and [1000+ more](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## Supported platforms

- macOS (Intel and Apple Silicon)
- Linux

Windows is untested but should work — ffmpeg and all Python dependencies have Windows builds.

## Advanced

If automatic browser cookie detection doesn't work (e.g. in a Docker container, CI, or headless server), you can provide a cookies file manually:

```bash
transclipt https://www.instagram.com/reel/... --cookies ~/cookies.txt
```

To export a cookies file: install a browser extension like "Get cookies.txt LOCALLY" for Chrome, navigate to the site you need, and export. The file follows the Netscape cookie format that yt-dlp expects.

## License

MIT
