import pytest

from ytmd.cli import read_batch_file


def test_read_batch_file_one_url_per_line(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text("https://a.com/1\nhttps://b.com/2\n")
    assert read_batch_file(str(f)) == ["https://a.com/1", "https://b.com/2"]


def test_read_batch_file_skips_blanks_and_comments(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text(
        "# a comment\n"
        "\n"
        "  https://a.com/1  \n"  # surrounding whitespace is stripped
        "   \n"
        "# another comment\n"
        "https://b.com/2\n"
    )
    assert read_batch_file(str(f)) == ["https://a.com/1", "https://b.com/2"]


def test_read_batch_file_empty_returns_empty_list(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text("\n# nothing but comments\n\n")
    assert read_batch_file(str(f)) == []


def test_read_batch_file_missing_raises_oserror(tmp_path):
    with pytest.raises(OSError):
        read_batch_file(str(tmp_path / "does-not-exist.txt"))
