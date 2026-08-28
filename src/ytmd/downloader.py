import os
from dataclasses import dataclass
from urllib.parse import urlparse

import imageio_ffmpeg
import yt_dlp

SUPPORTED_FORMATS = ("mp3", "opus", "m4a", "flac")
LOSSLESS_FORMATS = ("flac",)


@dataclass
class DownloadResult:
    count: int
    output_dir: str


def validate_url(url: str) -> None:
    """Reject anything that isn't an http(s) URL.

    The URL is handed straight to yt-dlp, which will happily fetch non-http
    schemes (e.g. ``file://``) and arbitrary hosts. Restricting to http(s)
    closes the local-scheme surface; note that yt-dlp can still reach any
    http(s) host, which is documented in the README.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid URL '{url}': expected an http:// or https:// link.")


def build_output_template(output_dir: str) -> str:
    """Return the yt-dlp output template.

    Playlist entries go into a subfolder named after the playlist; single
    videos land directly in ``output_dir``. The folder name comes from
    yt-dlp's own conditional field ``%(playlist_title&...)s`` rather than
    string-splicing the title ourselves, so yt-dlp sanitizes and escapes it —
    a title containing ``%``, a path separator, or ``..`` can neither be
    reinterpreted as a template field nor escape ``output_dir``.

    Note: filenames are ``<title>.<ext>`` with no unique component, so two
    tracks that share a title (or re-downloading the same title) will
    overwrite each other — an accepted trade-off for clean library filenames.
    """
    return os.path.join(
        output_dir,
        "%(playlist_title&{}/|)s%(title)s.%(ext)s",
    )


def build_ydl_opts(
    fmt: str,
    output_dir: str,
    quality: int | None,
    cookies_from_browser: str | None,
    progress_hooks: list,
) -> dict:
    extract_audio: dict = {"key": "FFmpegExtractAudio", "preferredcodec": fmt}
    if quality is not None:
        extract_audio["preferredquality"] = str(quality)

    opts: dict = {
        "format": "bestaudio/best",
        "outtmpl": build_output_template(output_dir),
        "writethumbnail": True,
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
        # Skip unavailable/private/geo-blocked entries instead of aborting the
        # whole playlist on the first bad one.
        "ignoreerrors": True,
        "progress_hooks": progress_hooks,
        "postprocessors": [
            extract_audio,
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
    }
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser,)
    return opts


def download_audio(
    url: str,
    fmt: str = "mp3",
    output_dir: str = "downloads",
    quality: int | None = None,
    cookies_from_browser: str | None = None,
) -> DownloadResult:
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{fmt}'. Choose from {', '.join(SUPPORTED_FORMATS)}."
        )
    validate_url(url)

    if quality is not None and fmt in LOSSLESS_FORMATS:
        print(f"Note: --quality is ignored for lossless format '{fmt}'.")

    output_dir = os.path.abspath(output_dir)

    # Count successfully downloaded streams so the CLI can confirm what landed
    # (a 'finished' hook fires once per completed download, before postprocessing).
    finished: list = []

    def _hook(status: dict) -> None:
        if status.get("status") == "finished":
            finished.append(status.get("filename"))

    opts = build_ydl_opts(fmt, output_dir, quality, cookies_from_browser, [_hook])
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    return DownloadResult(count=len(finished), output_dir=output_dir)
