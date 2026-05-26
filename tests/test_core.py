import zipfile
from pathlib import Path

import pytest

from filecrack.backends import detect_format, get_backend
from filecrack.core import build_candidates, crack_file, load_wordlist


def test_load_wordlist_skips_empty_lines(tmp_path: Path):
    wordlist = tmp_path / "dict.txt"
    wordlist.write_text("123456\n\nsecret\n", encoding="utf-8")

    assert list(load_wordlist(wordlist)) == ["123456", "secret"]


def test_unencrypted_zip_does_not_match_first_password(tmp_path: Path):
    target = tmp_path / "plain.zip"
    wordlist = tmp_path / "dict.txt"
    wordlist.write_text("wrong\nsecret\n", encoding="utf-8")

    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("hello.txt", "hello")

    result = crack_file(target, wordlist=wordlist, workers=2)

    assert result.backend == "zip"
    assert result.found is False


def test_office_extensions_use_office_backend(tmp_path: Path):
    target = tmp_path / "demo.docx"
    target.write_bytes(b"not-a-real-docx")

    assert get_backend(target).name == "office"


def test_detect_format_uses_file_signature_before_extension(tmp_path: Path):
    target = tmp_path / "archive.bin"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("hello.txt", "hello")

    assert detect_format(target) == ".zip"
    assert get_backend(target).name == "zip"


def test_build_candidates_combines_password_weak_and_wordlist_without_duplicates(tmp_path: Path):
    wordlist = tmp_path / "dict.txt"
    wordlist.write_text("123456\ncustom\n", encoding="utf-8")

    candidates = list(build_candidates(single_password="123456", weak_check=True, wordlist=wordlist))

    assert candidates[0] == "123456"
    assert candidates.count("123456") == 1
    assert "password" in candidates
    assert candidates[-1] == "custom"


def test_crack_file_requires_at_least_one_password_source(tmp_path: Path):
    target = tmp_path / "plain.zip"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("hello.txt", "hello")

    with pytest.raises(ValueError):
        crack_file(target)
