import os

import pytest

from ytmd.downloader import (
    build_output_template,
    download_audio,
    validate_url,
)


def test_validate_url_accepts_https():
    validate_url("https://www.youtube.com/watch?v=abc")  # should not raise


def test_validate_url_accepts_http():
    validate_url("http://example.com/video")  # should not raise


@pytest.mark.parametrize(
    "bad_url",
    [
        "file:///etc/passwd",
        "ftp://example.com/x",
        "not-a-url",
        "www.youtube.com/watch?v=abc",  # no scheme
        "https://",  # no host
    ],
)
def test_validate_url_rejects_non_http(bad_url):
    with pytest.raises(ValueError):
        validate_url(bad_url)


def test_download_audio_rejects_unknown_format():
    with pytest.raises(ValueError, match="Unsupported format"):
        download_audio("https://youtube.com/watch?v=abc", fmt="wav")


def test_download_audio_rejects_bad_url_before_network():
    # A bad URL must raise before any network/ffmpeg work happens.
    with pytest.raises(ValueError, match="Invalid URL"):
        download_audio("file:///etc/passwd", fmt="mp3")


def test_output_template_is_under_output_dir():
    tmpl = build_output_template("/tmp/music")
    assert tmpl.startswith(os.path.abspath("/tmp/music") + os.sep) or tmpl.startswith("/tmp/music/")


def test_output_template_uses_conditional_playlist_field():
    # Playlist subfolder comes from yt-dlp's escaped field, not spliced text.
    tmpl = build_output_template("/tmp/music")
    assert "%(playlist_title&{}/|)s" in tmpl


def test_output_template_uses_plain_title_filename():
    # Filenames are <title>.<ext> with no id — clean names, collisions accepted.
    tmpl = build_output_template("/tmp/music")
    assert tmpl.endswith("%(title)s.%(ext)s")
    assert "%(id)s" not in tmpl
