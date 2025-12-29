# Timeline CSV format

This document describes the CSV specification for timeline definitions that are loaded by Timeline-kun’s **Timer / Previewer**.

This CSV behavior follows the implementation in `src/timeline_kun/csv_to_timetable.py`.


## 1. File assumptions

### Text encoding (read behavior)
Timeline-kun reads CSV files using the following decoding order:

1. Try **UTF-8**
2. If it fails, try the encoding specified by `read_extra_encoding` in `config.toml`
3. If it still fails, fall back to **cp932**

If a UTF-8 **BOM (`\ufeff`)** exists at the beginning of the decoded text, it is automatically removed before parsing
(including the case where multiple BOMs are repeated at the start).

### Text encoding (write / export behavior)
- When you edit and save a CSV **inside Timeline-kun**, it is saved as **UTF-8**.
- When you press the **Send to Excel** button, Timeline-kun converts and saves the file as **UTF-8 with BOM** (`utf-8-sig`)
  and then opens it in Excel.

### Newlines and empty lines
- Both **LF (`\n`)** and **CRLF (`\r\n`)** are accepted.
- Parsing is performed using Python’s standard CSV reader (there is no manual `split("\n")` of the file content).
- Completely empty rows (rows where all cells are empty/whitespace) are ignored.

### CSV parsing (delimiter / quoting)
- Fields are separated by commas (`,`).
- Standard double-quote quoting is supported. Use quotes when a field contains a comma, e.g.:
  - `title,member,start,duration,fixed,instruction`
  - `"Task, with comma",Alice,0:00:00,0:01:00,start,`
- Inside a quoted field, a literal double quote should be written as `""` (CSV-style escaping).
- Leading and trailing whitespace in each cell is stripped after parsing.

## 2. Header (required / optional)

### Required columns
The following columns are **required**. The order does not matter.

Header matching is:
- **case-insensitive**, and
- ignores **leading/trailing whitespace** around header names.

Required columns:
- `title`
- `member`
- `duration`
- `start`
- `fixed`
- `instruction`

### Optional columns
- `end` (optional)
  - If the header does not include `end`, each row’s `end` is treated as an empty string.

### Missing / extra cells in data rows
- If a data row has fewer cells than the header, missing cells are treated as empty strings.
- Extra cells beyond the header are ignored.

## 3. Column meanings

### `title` (string)
Task name (used for display in Timer).

### `member` (string)
Assignee name, etc. (used for display in Timer).

### `instruction` (string)
Displayed as “instruction” in Timer. If empty, Timer displays `start - end` instead.

It is also used as the keyword source for BLE recording triggers (see below).

### `fixed` (enum)
Only `start` or `duration` is valid (anything else is an error).

### `start` / `end` / `duration` (time string)
These values represent times in seconds or colon-separated time.

Supported formats (parser behavior):
- `SS` (e.g., `90`)
- `M:SS` (e.g., `1:30`)
- `H:MM:SS` (e.g., `0:01:30`)

An empty string is treated as 0 seconds (`"" -> 0`).

### Time format: parse → normalize

Use **h:mm:ss** as the canonical format (e.g., `1:02:03`).  
To mitigate ambiguous user input, Timeline-kun applies a two-step process: **parse → normalize**.

#### 1) Parsing (determined by the number of `:`)
- **Two colons**: parse as `h:mm:ss`
- **One colon**: parse as `mm:ss` (treat as `h=0`)
- **No colons**: parse as seconds `s` (treat as `h=0, m=0`)

#### 2) Normalization (normalize to `h:mm:ss` when non-empty)
After parsing, the value is normalized to `h:mm:ss`:
- minutes and seconds are zero-padded to 2 digits
- carry/rollover is applied (e.g., `70` seconds becomes `1:10`)

Examples:
- Zero-padding:
  - `01:2:3` → `1:02:03`
  - `1:2` (= `mm:ss`) → `0:01:02`
  - `10` (= `s`) → `0:00:10`
- Carry/rollover:
  - `1:70:00` → `2:10:00`
  - `0:00:3600` → `1:00:00`
  - `70:00` (= `mm:ss`) → `1:10:00`

Note:
- `h:mm:ss` is the official format. Fewer colons and carry/rollover handling exist only as a best-effort fallback.
- Empty strings remain empty (but are treated as 0 seconds where numeric time is required).

## 4. How times are determined (implementation behavior)

The parser processes rows top-to-bottom and maintains an internal `current_time` (the previous row’s end time in seconds).
For each row, it determines `start` / `end` and updates `current_time`.

### 4.1 When `fixed == "start"`
- Principle: **start is fixed**, and end is determined accordingly.
- Exception: only the first data row may have `start=0`. For all other rows, `start=0` is an error.

How `end` is determined (priority order):
1) If `duration > 0` is provided, then `end = start + duration`
2) Otherwise, if `end > 0` is provided, then `end = end`
3) If neither `duration` nor `end` is provided, it uses the next row’s `start` to determine `end`
   - If the next row’s `start` is `"0"`, that becomes an error
   - If this is the last row (no next row), it is also an error

Warning behavior:
- If `start < current_time` (earlier than the previous row’s end), it is treated as a conflict with the previous row.
  The row is marked with `has_error`.

### 4.2 When `fixed == "duration"`
- Principle: **duration is fixed**, and start/end are determined accordingly.
- `duration == 0` is an error (required).

How `start/end` are determined:
1) If `start==0` and `end==0` → `start = current_time`, `end = start + duration`
2) If `start > 0` → `end = start + duration`
3) If `end > 0` → `start = end - duration`

Warning behavior:
- If the previous row has both `duration` and `end` empty, a warning is emitted when processing the next `fixed=duration` row.
  (Even if the previous row effectively derived `end` using the “next row start” rule, it still warns if the *string fields* were empty.)


## 5. Timer extra behavior (Intermission)

When building the timeline for Timer, if there is a gap between entries (`end != next start`),
Timeline-kun automatically inserts an `Intermission` entry for that interval
(title is `Intermission`, instruction is empty).


## 6. BLE recording trigger (based on `instruction`)

Timer uses each stage’s `instruction` to decide recording start/stop triggers.

- The default keyword is **`(recording)`**.
- About **5 seconds before** the next stage starts (`offset_sec=5`), Timer checks the **next stage’s instruction**.
  If it contains `(recording)`, a “start recording” trigger fires.
- When leaving a stage with `(recording)`, a “stop recording” trigger runs (after a configured delay).

Therefore:
- “Start recording slightly before this task begins” → include `(recording)` in that task’s `instruction`
- “Keep recording across multiple tasks” → include `(recording)` in consecutive tasks’ `instruction`
  (If it is interrupted, Timer will treat it as a point to stop.)


## 7. Examples

### 7.1 Minimal example without the `end` column
Header (recommended: no spaces):

title,member,start,duration,fixed,instruction

Example:

```
title,member,start,duration,fixed,instruction
TASK A,MEMBER1,0:00:00,,start,Prepare for TASK B (recording)
TASK B,MEMBER1,0:04:00,0:05:00,start,Prepare for TASK C
TASK C,MEMBER1,,0:05:00,duration,
```


| title  | member  | start   | duration | fixed    | instruction |
| ------ | ------- | ------- | -------- | -------- | ----------- |
| TASK A | MEMBER1 | 0:00:00 |          | start    | Prepare for TASK B (recording) |
| TASK B | MEMBER1 | 0:04:00 | 0:05:00  | start    | Prepare for TASK C |
| TASK C | MEMBER1 |         | 0:05:00  | duration |             |
| ...    | ...     | ...     | ...      | ...      | ...         |



Notes:
- For `fixed=duration`, leaving start/end empty means “start at the previous end time”.
- For `fixed=start`, you must provide `start`, and `end` is determined by duration, end, or “next row start”.

### 7.2 With the `end` column (when you want to directly specify end for some rows)

```
title,member,start,end,duration,fixed,instruction
Task A,Alice,0:00:00,0:05:00,,start,
Task B,Bob,,,2:00,duration,
```

| title  | member | start   | end     | duration | fixed    | instruction |
| ------ | ------ | ------- | ------- | -------- | -------- | ----------- |
| Task A | Alice  | 0:00:00 | 0:05:00 |          | start    |             |
| Task B | Bob    |         |         | 2:00     | duration |             |
