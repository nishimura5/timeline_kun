from __future__ import annotations

import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures"

mmodule = importlib.import_module("timeline_kun.file_loader")
file_loader = getattr(mmodule, "FileLoader")

if file_loader.get_encoding is None:
    raise ImportError(
        "Could not import 'get_encoding' from 'timeline_kun.file_loader.FileLoader'"
    )

PARAMS = [("ja_utf8.csv", "utf-8"), ("ja_sjis.csv", "shift-jis")]


@pytest.mark.parametrize("filename, expected_encoding", PARAMS)
def test_get_encoding(filename, expected_encoding):
    file_path = FIXTURE_DIR / filename
    fl = file_loader()
    _ = fl._read_file(str(file_path))  # Load the file to set the encoding
    encoding = fl.get_encoding()
    assert encoding == expected_encoding
