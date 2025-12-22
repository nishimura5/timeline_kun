# Tests

This directory contains automated tests for Timeline-kun.

## Running the test suite

From the repository root (the directory that contains `pyproject.toml`):

```bash
uv sync --group dev
uv run pytest
```


## Test files

- `test_smoke.py`
	- Import-level smoke tests to ensure core modules are importable.

- `test_app_timer.py`
	- CLI/argument parsing tests for the timer app.
	- Designed to avoid launching the GUI.

- `test_file_loader.py`
	- CSV loading and validation tests using fixture files under `tests/fixtures/`.

## Fixtures

The fixtures cover cases such as:

- Invalid or missing headers (missing required columns)
- Invalid `fixed` codes (only `start` or `duration` are accepted)
- Missing values in required fields
- Temporal inconsistencies (e.g., start times that go backwards, or overlaps)
- Last-row edge cases where an end time cannot be inferred
- Text encoding detection:
	- Accepts UTF-8 and Shift-JIS
	- Rejects unsupported encodings

Fixture CSVs live in `tests/fixtures/`. They are used mainly by `test_file_loader.py`.

### Naming convention

Fixtures are named to make intent obvious from the filename:

- Prefix: `valid__`, `invalid__`, or `warn__`
- Components: `__`-separated `lower_snake_case`

### Mapping (filename -> what it covers)

- `invalid__header__missing_required_columns.csv`: invalid/missing headers (missing required columns)
- `invalid__fixed__unsupported_code.csv`: invalid fixed codes (only `start` or `duration` are accepted)
- `invalid__required__missing_start_when_fixed_start.csv`: missing required fields (missing `start` when `fixed=start`)
- `invalid__required__missing_duration_when_fixed_duration.csv`: missing required fields (missing `duration` when `fixed=duration`)
- `invalid__last_row__cannot_infer_end_time.csv`: last-row edge case where the end time cannot be inferred
- `warn__time__start_earlier_than_previous.csv`: temporal inconsistency (start time goes backwards)
- `warn__time__overlap_with_previous.csv`: temporal inconsistency (overlap/conflict with previous row)
- `valid__encoding__utf8.csv`: supported encoding (UTF-8)
- `valid__encoding__shift_jis.csv`: supported encoding (Shift-JIS)
- `invalid__encoding__unsupported.csv`: unsupported encoding is rejected
- `valid__header_only.csv`: minimal valid CSV (header only)
- `valid__with_end_column.csv`: valid CSV with `end` column
- `valid__time_format__mmss.csv`: supported time format variant (MM:SS)
