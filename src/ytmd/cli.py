import argparse
import sys

from yt_dlp.utils import DownloadError

from . import __version__
from .downloader import SUPPORTED_FORMATS, download_audio


def read_batch_file(path: str) -> list[str]:
    """Read URLs from a batch file: one per line, ignoring blank lines and
    lines beginning with ``#`` (comments), matching yt-dlp's ``-a`` convention.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    return [s for line in lines if (s := line.strip()) and not s.startswith("#")]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ytmd", description="Download audio from a YouTube video or playlist."
    )
    parser.add_argument(
        "url", nargs="*", metavar="URL",
        help="One or more video/playlist URLs (YouTube or any yt-dlp-supported site)",
    )
    parser.add_argument(
        "-a", "--batch-file", metavar="FILE",
        help="Read URLs from FILE, one per line (blank lines and #-comments are "
             "ignored); combined with any URLs given on the command line.",
    )
    parser.add_argument(
        "-f", "--format", choices=SUPPORTED_FORMATS, default="mp3",
        help="Output audio format (default: mp3)",
    )
    parser.add_argument(
        "-o", "--output-dir", default="downloads",
        help="Directory to save downloaded audio (default: ./downloads)",
    )
    parser.add_argument(
        "-q", "--quality", type=int, choices=range(0, 10), metavar="0-9", default=None,
        help="Quality for lossy formats: 0 = best (default), 9 = worst. Ignored for flac.",
    )
    parser.add_argument(
        "--cookies-from-browser", metavar="BROWSER",
        help="Load cookies from this browser (e.g. firefox, chrome, safari) to reach "
             "age-restricted or token-gated videos. See README troubleshooting.",
    )
    parser.add_argument("--version", action="version", version=f"ytmd {__version__}")
    args = parser.parse_args()

    urls = list(args.url)
    if args.batch_file:
        try:
            urls += read_batch_file(args.batch_file)
        except OSError as e:
            parser.error(f"could not read batch file '{args.batch_file}': {e}")
    if not urls:
        parser.error("no URLs given: pass at least one URL or --batch-file FILE")

    try:
        result = download_audio(
            urls,
            fmt=args.format,
            output_dir=args.output_dir,
            quality=args.quality,
            cookies_from_browser=args.cookies_from_browser,
        )
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except DownloadError as e:
        print(f"Error: download failed: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: could not write to '{args.output_dir}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # last-resort: a friendly message beats a raw traceback
        print(f"Error: unexpected failure: {e}", file=sys.stderr)
        sys.exit(1)

    if result.count == 0:
        print(
            "No audio was downloaded — the URL may be unavailable, private, "
            "or an empty playlist.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Done — {result.count} file(s) saved to {result.output_dir}")


if __name__ == "__main__":
    main()
