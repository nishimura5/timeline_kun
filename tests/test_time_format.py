import pytest

from timeline_kun import time_format


@pytest.mark.parametrize(
    "src, expected",
    [
        ("0:1:2", "0:01:02"),
        ("1:2", "0:01:02"),
        ("0:70:00", "1:10:00"),
        ("3600", "1:00:00"),
        ("0:00:3600", "1:00:00"),
    ],
)
def test_str_to_time_str(src: str, expected: str):
    assert time_format.str_to_time_str(src) == expected


@pytest.mark.parametrize(
    "src, expected",
    [
        ("0:1:2", 62),
        ("1:2", 62),
        ("0:70:00", 4200),
        ("3600", 3600),
        ("0:00:3600", 3600),
    ],
)
def test_str_to_seconds(src: str, expected: int):
    assert time_format.str_to_seconds(src) == expected
