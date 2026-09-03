# yt-music-downloader

Download audio from a YouTube video or playlist as mp3/opus/m4a/flac, with
title/artist metadata and cover art embedded.

Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) + ffmpeg (bundled via
[imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)) + [mutagen](https://github.com/quodlibet/mutagen)
for tagging — no separate Homebrew/system install needed.

## Setup

```bash
git clone <your-repo-url> yt-music-downloader
cd yt-music-downloader
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

On the first run, imageio-ffmpeg makes sure a bundled ffmpeg binary is
available; no separate install is required on the common platforms (macOS,
Windows, Linux x86_64).

**Recommended: a JavaScript runtime.** yt-dlp now runs YouTube's player
JavaScript in an external JS runtime to unlock all formats; without one it
prints a warning and may fetch lower-quality streams or fail. Installing
[Deno](https://deno.com) (the runtime yt-dlp auto-detects) is the simplest fix —
see [Troubleshooting](#troubleshooting) below.

## Usage

```bash
ytmd "https://www.youtube.com/watch?v=..."                    # -> downloads/<title>.mp3
ytmd "https://www.youtube.com/watch?v=..." --format opus
ytmd "https://www.youtube.com/playlist?list=..." -o ~/Music   # -> ~/Music/<playlist>/<title>.mp3
ytmd "https://youtu.be/AAA" "https://youtu.be/BBB"            # several URLs in one run
ytmd -a urls.txt                                              # read URLs from a file
```

Pass several URLs at once, and/or read them from a file with `-a/--batch-file`
(one URL per line; blank lines and `#` comments are ignored). URLs on the
command line and in the batch file are combined into a single run:

```
# urls.txt
https://www.youtube.com/watch?v=AAA
# this line is ignored
https://www.youtube.com/playlist?list=BBB
```

On success the tool prints how many files were saved and the absolute output
directory.

### Options

| Flag | Description |
| --- | --- |
| `-a, --batch-file FILE` | Read URLs from `FILE`, one per line (blank lines and `#` comments ignored); combined with any URLs on the command line. |
| `-f, --format {mp3,opus,m4a,flac}` | Output format (default `mp3`). |
| `-o, --output-dir DIR` | Where to save audio (default `./downloads`). |
| `-q, --quality 0-9` | Quality for **lossy** formats: `0` = best (default), `9` = worst. Ignored for `flac` (lossless — always full quality). |
| `--cookies-from-browser BROWSER` | Load cookies from `firefox`/`chrome`/`safari`/etc. to reach age-restricted or token-gated videos. |
| `--version` | Print the version and exit. |

Files are named `<title>.<ext>`. Playlist entries are grouped into a subfolder
named after the playlist. Note that two tracks with the same title (or
re-downloading one) will overwrite each other.

The URL must be an `http(s)` link. yt-dlp supports many sites beyond YouTube,
so **any** http(s) host you pass will be fetched — only pass URLs you trust.

## Troubleshooting

- **Warning: "No supported JavaScript runtime could be found"** — YouTube
  extraction now relies on running its player JavaScript in an external JS
  runtime (yt-dlp's EJS feature). Without one, yt-dlp falls back to a degraded
  path and some formats may be missing. Install **Deno**, which yt-dlp
  auto-detects (no flags needed):

  ```bash
  curl -fsSL https://deno.land/install.sh | sh
  ```

  Open a new terminal so `deno` is on your `PATH` (verify with `deno --version`),
  then re-run `ytmd`. On macOS, prefer this official installer over
  `brew install deno` — the Homebrew formula builds from source and needs a full
  Xcode install. Deno is recommended because it sandboxes the untrusted player
  JS; other runtimes (e.g. Node) work only if pointed to explicitly. See the
  [yt-dlp EJS guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS) for details.

- **Downloads failing with token/403 errors** — YouTube increasingly requires a
  PO Token to serve audio streams. First update yt-dlp:

  ```bash
  pip install -U yt-dlp
  ```

  If that doesn't help, pass your browser's cookies:

  ```bash
  ytmd "<url>" --cookies-from-browser firefox
  ```

  For the full picture (including the `bgutil-ytdlp-pot-provider` plugin) see the
  [yt-dlp PO Token guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide).

## Disclaimer

This tool is intended for personal use with content you own or are otherwise
permitted to download. Downloading videos may violate
[YouTube's Terms of Service](https://www.youtube.com/t/terms), and downloading
copyrighted material without permission may be unlawful in your jurisdiction.
You are solely responsible for how you use it.

## Development

```bash
pip install -e ".[dev]"
ruff check .
mypy
pytest
```
