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
        "invalid__header__missing_required_columns.csv",
        "",
        "Header missing required field: title, member, duration, start, fixed, instruction",
    ),
    ("invalid__fixed__unsupported_code.csv", "", "[line 1] Invalid fixed code: none"),
    (
        "warn__time__start_earlier_than_previous.csv",
        "[line 2] Start time is earlier than the previous line",
        None,
    ),
    (
        "invalid__required__missing_start_when_fixed_start.csv",
        "",
        "[line 2] Start must be set in fixed==start",
    ),
    (
        "invalid__required__missing_duration_when_fixed_duration.csv",
        "",
        "[line 1] Duration must be set in fixed==duration",
    ),
    ("invalid__last_row__cannot_infer_end_time.csv", "", "[line 2] No next line"),
    (
        "warn__time__overlap_with_previous.csv",
        "[line 2] Task2 conflict with the previous line",
        None,
    ),
    (
        "warn__previous__missing_duration_or_end.csv",
        "[line 2] No duration (or end) in the previous line",
        None,
    ),
]

VALID_CASES = [
    # filename
    ("valid__header_only.csv"),
    ("valid__with_end_column.csv"),
    ("valid__time_format__mmss.csv"),
    ("valid__crlf.csv"),
    ("valid__empty_lines__ignored.csv"),
    ("valid__quoted_fields.csv"),
    # CSVs used in manual test
    ("valid__recording__example_1.csv"),
    ("valid__recording__example_2.csv"),
    ("valid__recording__example_3hour.csv"),
    # CSVs used in SSRN
    ("valid__ssrn__exp1.csv"),
    ("valid__ssrn__exp2.csv"),
    ("valid__ssrn__exp3.csv"),
]

TEXT_ENCODING_CASES = [
    # filename, expected_encoding, expected_warn_msg, expected_err_msg
    ("valid__encoding__utf8.csv", "utf-8", "", None),
    ("valid__encoding__utf8_bom.csv", "utf-8", "", None),
    ("valid__encoding__shift_jis.csv", "cp932", "", None),
    ("valid__encoding__euc_jp.csv", "euc_jp", "", None),
    (
        "invalid__encoding__unsupported.csv",
        "utf-8",
        "",
        "File encoding not supported",
    ),
]


@pytest.mark.parametrize("filename, expected_warn_msg, expected_err_msg", INVALID_CASES)
def test_load_invalid_file_for_preview(
    filename,
    expected_warn_msg,
    expected_err_msg,
):
    file_path = _fixture_path(filename)
    fl = FileLoader(fallback_encoding="shift-jis")
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
    fl = FileLoader(fallback_encoding=expected_encoding)
    if expected_err_msg is not None:
        with pytest.raises(ValueError) as e:
            _ = fl.load_file_for_preview(file_path)
        assert expected_err_msg in str(e.value)
    else:
        warn_msg, time_table = fl.load_file_for_preview(file_path)
        assert fl.get_encoding() == expected_encoding
        assert warn_msg == expected_warn_msg
        assert time_table is not None
