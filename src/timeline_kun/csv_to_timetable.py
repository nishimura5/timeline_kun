import datetime
import csv
import io

from . import time_format


class TimeTable:
    BOM = "\ufeff"

    def __init__(self):
        self.time_table = []
        self.current_time = 0

    @staticmethod
    def _cell(row, idx: int) -> str:
        if idx is None or idx < 0:
            return ""
        if idx >= len(row):
            return ""
        return row[idx].strip()

    def load_csv_str(self, csv_str):
        warn_msg = ""
        # UTF-8 BOM removal
        if csv_str.startswith(self.BOM):
            bom_len = len(self.BOM)
            csv_str = csv_str[bom_len:]

        reader = csv.reader(io.StringIO(csv_str))

        rows = []
        for row in reader:
            if not row or all(cell.strip() == "" for cell in row):
                continue
            rows.append(row)

        required_headers = [
            "title",
            "member",
            "duration",
            "start",
            "fixed",
            "instruction",
        ]

        # Empty file check
        if not rows:
            raise ValueError(
                f"Header missing required field: {', '.join(required_headers)}"
            )

        # Validate the header
        header = [h.strip().lower() for h in rows[0]]
        header_dict = {header[i]: i for i in range(len(header))}

        missing_headers = [rh for rh in required_headers if rh not in header_dict]
        if missing_headers:
            raise ValueError(
                f"Header missing required field: {', '.join(missing_headers)}"
            )

        if "end" not in header_dict:
            is_no_end = True
            header_dict["end"] = -1
        else:
            is_no_end = False

        has_end_time = True

        data_rows = rows[1:]
        for i, line in enumerate(data_rows):
            (
                title,
                member,
                duration_sec_str,
                start_sec_str,
                end_sec_str,
                fixed,
                instruction,
            ) = self._asign(line, header_dict, is_no_end)

            duration_sec = time_format.str_to_seconds(duration_sec_str)
            start_sec = time_format.str_to_seconds(start_sec_str)
            end_sec = time_format.str_to_seconds(end_sec_str)

            if fixed not in ["start", "duration"]:
                raise ValueError(f"[line {i + 1}] Invalid fixed code: {fixed}")

            has_error = False
            if fixed == "start":
                if start_sec < self.current_time:
                    warn_msg = f"[line {i + 1}] {title} conflict with the previous line"
                    has_error = True

                if start_sec == 0 and i != 0:
                    raise ValueError(
                        f"[line {i + 1}] Start must be set in fixed==start"
                    )

                if duration_sec > 0:
                    end_sec = start_sec + duration_sec
                elif end_sec > 0:
                    end_sec = end_sec
                else:
                    next_row = self._find_next_nonempty_row(data_rows, i)
                    if next_row is None:
                        raise ValueError(f"[line {i + 1}] No next line")
                    end_sec = self.get_next_start(line, next_row, header_dict)
                    if end_sec == 0:
                        end_sec = start_sec

            elif fixed == "duration":
                if duration_sec == 0:
                    raise ValueError(
                        f"[line {i + 1}] Duration must be set in fixed==duration"
                    )
                if start_sec == 0 and end_sec == 0:
                    start_sec = self.current_time
                    end_sec = start_sec + duration_sec
                elif start_sec > 0:
                    end_sec = start_sec + duration_sec
                elif end_sec > 0:
                    start_sec = end_sec - duration_sec

                if (i > 0) and (has_end_time is False):
                    warn_msg = (
                        f"[line {i + 1}] No duration (or end) in the previous line"
                    )
                    has_error = True

            start_td = datetime.timedelta(seconds=start_sec)
            end_td = datetime.timedelta(seconds=end_sec)

            self.time_table.append(
                {
                    "title": title,
                    "start": start_td,
                    "end": end_td,
                    "member": member,
                    "duration_sec": duration_sec_str,
                    "start_sec": start_sec_str,
                    "end_sec": end_sec_str,
                    "fixed": fixed,
                    "instruction": instruction,
                    "has_error": has_error,
                }
            )

            self.current_time = end_sec
            has_end_time = (end_sec_str != "") or (duration_sec_str != "")

        for i in range(1, len(self.time_table)):
            if self.time_table[i]["start"] < self.time_table[i - 1]["start"]:
                warn_msg = (
                    f"[line {i + 1}] Start time is earlier than the previous line"
                )
                self.time_table[i]["has_error"] = True
                break

        return warn_msg

    def _asign(self, row, header_dict, is_no_end=False):
        title = self._cell(row, header_dict["title"])
        member = self._cell(row, header_dict["member"])
        duration_sec_str = self._cell(row, header_dict["duration"])
        start_sec_str = self._cell(row, header_dict["start"])
        instruction = self._cell(row, header_dict["instruction"])

        if is_no_end:
            end_sec_str = ""
        else:
            end_sec_str = self._cell(row, header_dict["end"])

        fixed = self._cell(row, header_dict["fixed"])

        return (
            title,
            member,
            duration_sec_str,
            start_sec_str,
            end_sec_str,
            fixed,
            instruction,
        )

    def _find_next_nonempty_row(self, data_rows, current_index: int):
        for j in range(current_index + 1, len(data_rows)):
            row = data_rows[j]
            if row and any(c.strip() != "" for c in row):
                return row
        return None

    def get_timetable(self):
        return self.time_table

    def get_timetable_as_str(self):
        ret_table = []
        for entry in self.time_table:
            start_str = time_format.timedelta_to_str(entry["start"])
            end_str = time_format.timedelta_to_str(entry["end"])
            ret_table.append(
                {
                    "title": entry["title"],
                    "start": start_str,
                    "end": end_str,
                    "member": entry["member"],
                }
            )
        return ret_table

    def get_next_start(self, current_row, next_row, header_dict):
        (
            title,
            member,
            duration_sec_str,
            start_sec_str,
            end_sec_str,
            fixed,
            instruction,
        ) = self._asign(next_row, header_dict, False)
        if start_sec_str == "0":
            raise ValueError(f"next_start_sec is 0: {current_row}")
        return time_format.str_to_seconds(start_sec_str)
