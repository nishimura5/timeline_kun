from __future__ import annotations

import os

import pytest

from timeline_kun.file_loader import FileLoader

# test_file_loader.pyと同じディレクトリにあるfixturesフォルダを探す
ROOT = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR_CANDIDATES = [
    os.path.join(ROOT, "fixtures"),
]


def _fixture_path(filename: str) -> str:
    for d in FIXTURE_DIR_CANDIDATES:
        candidate = os.path.join(d, filename)
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(f"Fixture file not found: {filename}")


INVALID_CASES = [
    # filename, expected_warn_msg, expected_err_msg
    (
        "blank.csv",
        "",
        "Header missing required field: title, member, duration, start, fixed, instruction",
    ),
    ("invalid_fixed_code.csv", "", "[line 1] Invalid fixed code: none"),
    (
        "non_decreasing_start.csv",
        "[line 2] Start time is earlier than the previous line",
        None,
    ),
    (
        "no_start.csv",
        "",
        "[line 2] Start must be set in fixed==start",
    ),
    (
        "no_duration.csv",
        "",
        "[line 1] Duration must be set in fixed==duration",
    ),
    ("no_duration_last_row.csv", "", "[line 2] No next line"),
    ("conflict_rows.csv", "[line 2] Task2 conflict with the previous line", None),
]

VALID_CASES = [
    # filename
    ("only_header.csv"),
    ("with_end.csv"),
    ("mmss_format.csv"),
    # CSVs used in manual test
    ("recording_1.csv"),
    ("recording_2.csv"),
    ("recording_3hour.csv"),
    # CSVs used in SSRN
    ("ssrn_exp1.csv"),
    ("ssrn_exp2.csv"),
    ("ssrn_exp3.csv"),
]

TEXT_ENCODING_CASES = [
    # filename, expected_encoding, expected_warn_msg, expected_err_msg
    ("ja_utf8.csv", "utf-8", "", None),
    ("ja_sjis.csv", "shift-jis", "", None),
    ("ja_euc.csv", "utf-8", "", "File encoding not supported (not UTF-8 or Shift-JIS)"),
]


@pytest.mark.parametrize("filename, expected_warn_msg, expected_err_msg", INVALID_CASES)
def test_load_invalid_file_for_preview(
    filename,
    expected_warn_msg,
    expected_err_msg,
):
    file_path = _fixture_path(filename)
    fl = FileLoader()
    if expected_err_msg is not None:
        with pytest.raises(ValueError) as e:
            _ = fl.load_file_for_preview(file_path)
        assert expected_err_msg in str(e.value)
    elif expected_warn_msg != "":
        warn_msg, time_table = fl.load_file_for_preview(file_path)
        assert warn_msg == expected_warn_msg
        assert time_table is not None


@pytest.mark.parametrize("filename", VALID_CASES)
def test_load_valid_file_for_preview(
    filename,
):
    file_path = _fixture_path(filename)
    fl = FileLoader()
    warn_msg, time_table = fl.load_file_for_preview(file_path)
    assert warn_msg == ""
    assert time_table is not None


@pytest.mark.parametrize(
    "filename, expected_encoding, expected_warn_msg, expected_err_msg",
    TEXT_ENCODING_CASES,
)
def test_load_file_for_encoding_detection(
    filename,
    expected_encoding,
    expected_warn_msg,
    expected_err_msg,
):
    file_path = _fixture_path(filename)
    fl = FileLoader()
    if expected_err_msg is not None:
        with pytest.raises(ValueError) as e:
            _ = fl.load_file_for_preview(file_path)
        assert expected_err_msg in str(e.value)
    else:
        warn_msg, time_table = fl.load_file_for_preview(file_path)
        assert fl.get_encoding() == expected_encoding
        assert warn_msg == expected_warn_msg
        assert time_table is not None
