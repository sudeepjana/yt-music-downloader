# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e ".[dev]"   # install package + dev tools (into an activated venv)
ruff check .              # lint
mypy                      # type check (config in pyproject: files = ["src"])
pytest                    # run tests
pytest -q                 # quiet form used in CI
pytest tests/test_downloader.py::test_validate_url_accepts_https   # single test
pytest -k output_template # run tests matching an expression
```

CI (`.github/workflows/ci.yml`) runs exactly `ruff check .`, `mypy`, `pytest -q` on Python 3.13. `requires-python` is `>=3.10` and mypy targets 3.10, so keep syntax 3.10-compatible.

The CLI entry point is `ytmd` (declared in `pyproject.toml` `[project.scripts]` → `ytmd.cli:main`); it only exists after `pip install -e`.

Enable the tracked git hooks once per clone:

```bash
git config core.hooksPath .githooks   # activates .githooks/pre-push
```

`.githooks/pre-push` refuses direct pushes to `main`/`master` — all changes land via a branch + PR (emergency override: `git push --no-verify`).

## Architecture

This is a thin, security-conscious wrapper around **yt-dlp**. The actual downloading, audio extraction, metadata tagging, and thumbnail embedding are all performed by yt-dlp postprocessors driven by ffmpeg — this code mostly just constructs a yt-dlp options dict and runs it. Understanding the port therefore means understanding what each option does in yt-dlp, not custom logic here.

Two source files do everything:

- `src/ytmd/downloader.py` — the library. `download_audio()` validates input, builds options via `build_ydl_opts()`, runs `yt_dlp.YoutubeDL(...).download([url])`, and returns a `DownloadResult(count, output_dir)`.
- `src/ytmd/cli.py` — argparse front end that calls `download_audio()` and maps outcomes to exit codes (see below).

Key design decisions that span files / aren't obvious from one function:

- **ffmpeg is bundled, not system-provided.** `imageio_ffmpeg.get_ffmpeg_exe()` supplies the binary path, passed to yt-dlp as `ffmpeg_location`. Do not assume a system ffmpeg.
- **Tagging/cover art is done by yt-dlp**, via the `FFmpegExtractAudio` / `FFmpegMetadata` / `EmbedThumbnail` postprocessors — not by hand, so there is no tagging code in this repo to find.
- **`mutagen` is a required runtime dependency even though nothing here imports it.** yt-dlp's `EmbedThumbnail` postprocessor embeds cover art into `opus`/`flac` **only** via mutagen and raises `EmbedThumbnailPPError` without it (it is also the preferred path for `m4a`; `mp3` uses ffmpeg). yt-dlp treats mutagen as optional and won't install it, so `pyproject.toml` must declare it. Do not remove it — doing so re-breaks opus/flac thumbnail embedding.
- **URL validation is a security boundary, ordered before any network work.** `validate_url()` rejects non-`http(s)` schemes to close the `file://`/local-scheme surface that yt-dlp would otherwise accept, and `download_audio()` calls it before touching the network. `tests/test_downloader.py::test_download_audio_rejects_bad_url_before_network` enforces that ordering — preserve it.
- **The output template avoids string-splicing untrusted titles.** `build_output_template()` uses yt-dlp's own conditional field `%(playlist_title&{}/|)s` so yt-dlp sanitizes/escapes the playlist folder name (a title with `%`, a path separator, or `..` can't escape `output_dir` or be reinterpreted as a template field). Tests assert this exact field is used and that filenames stay `%(title)s.%(ext)s` (no unique id — same-title tracks intentionally overwrite).
- **Playlists skip bad entries** (`ignoreerrors: True`) rather than aborting on the first private/geo-blocked item.
- **Success is measured by a progress hook.** A `finished`-status hook appends filenames; `DownloadResult.count` is that length. The CLI treats `count == 0` as a failure (exit 1) even though yt-dlp itself didn't raise.

### CLI exit-code contract

`cli.main()` deliberately maps exception types to exit codes — keep this stable: `ValueError` → 2 (bad format/URL), `DownloadError` → 1, `OSError` → 1 (write failure), `KeyboardInterrupt` → 130, any other exception → 1 with a friendly message, and a successful run that downloaded nothing → 1.

## Constraints

- **Supported formats** are fixed in `SUPPORTED_FORMATS = ("mp3", "opus", "m4a", "flac")`; `LOSSLESS_FORMATS = ("flac",)` (quality is ignored, with a printed note, for lossless).
- `yt-dlp` is intentionally pinned with a **lower bound only** — it ships frequent releases tracking YouTube changes and must stay current. Don't add an upper cap.
- Downloads commonly fail with 403/PO-Token errors; the supported remedies are updating yt-dlp and `--cookies-from-browser`. See the README Troubleshooting section before debugging download failures as code bugs.
