from pathlib import Path

from tools.file_tools import search_files


def test_search_files_rejects_empty_query(tmp_path):
    (tmp_path / "example.txt").write_text("sample", encoding="utf-8")
    result = search_files("   ", str(tmp_path))
    assert "provide a filename" in result.lower()
    assert "example.txt" not in result


def test_search_files_rejects_non_directory(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("sample", encoding="utf-8")
    result = search_files("file", str(target))
    assert "not a directory" in result.lower()


def test_search_files_finds_matching_file_only(tmp_path):
    (tmp_path / "notes.txt").write_text("ok", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"png")
    result = search_files("notes", str(tmp_path))
    assert "notes.txt" in result
    assert "image.png" not in result
