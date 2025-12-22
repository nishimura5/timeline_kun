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


CASES = [
    # filename, expected_encoding, expected_warn_msg, expected_err_msg
    ("ja_utf8.csv", "utf-8", "", None),
    ("ja_sjis.csv", "shift-jis", "", None),
    ("ja_euc.csv", "utf-8", "", "File encoding not supported (not UTF-8 or Shift-JIS)"),
    (
        "blank.csv",
        "utf-8",
        "",
        "Header missing required field: title, member, duration, start, fixed, instruction",
    ),
    ("invalid_fixed_code.csv", "utf-8", "", "[line 1] Invalid fixed code: none"),
    ("only_header.csv", "utf-8", "", None),
    ("with_end.csv", "utf-8", "", None),
    (
        "non_decreasing_start.csv",
        "utf-8",
        "[line 2] Start time is earlier than the previous line",
        None,
    ),
    (
        "no_start.csv",
        "utf-8",
        "",
        "[line 2] Start must be set in fixed==start",
    ),
    (
        "no_duration.csv",
        "utf-8",
        "",
        "[line 1] Duration must be set in fixed==duration",
    ),
    ("no_duration_last_row.csv", "utf-8", "", "[line 2] No next line"),
    ("conflict_rows.csv", "utf-8", "[line 2] Task2 conflict with the previous line", None),
    # CSVs used in manual test
    ("recording_1.csv", "utf-8", "", None),
    ("recording_2.csv", "utf-8", "", None),
    ("recording_3hour.csv", "utf-8", "", None),
    # CSVs used in SSRN
    ("ssrn_exp1.csv", "shift-jis", "", None),
    ("ssrn_exp2.csv", "utf-8", "", None),
    ("ssrn_exp3.csv", "utf-8", "", None),
]


@pytest.mark.parametrize(
    "filename, expected_encoding, expected_warn_msg, expected_err_msg", CASES
)
def test_load_file_for_preview(
    filename,
    expected_encoding,
    expected_warn_msg,
    expected_err_msg,
):
    try:
        file_path = _fixture_path(filename)
    except FileNotFoundError:
        assert False, f"Fixture file not found: {filename}, (ROOT={ROOT})"
    fl = FileLoader()
    if expected_err_msg is not None:
        with pytest.raises(ValueError) as e:
            _ = fl.load_file_for_preview(file_path)
        assert expected_err_msg in str(e.value)
    elif expected_warn_msg != "":
        warn_msg, time_table = fl.load_file_for_preview(file_path)
        assert fl.get_encoding() == expected_encoding
        assert warn_msg == expected_warn_msg
        assert time_table is not None
    else:
        warn_msg, time_table = fl.load_file_for_preview(file_path)
        assert fl.get_encoding() == expected_encoding
        assert warn_msg == expected_warn_msg
        assert time_table is not None
