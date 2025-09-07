import datetime

from . import time_format


class TimeTable:
    BOM = "\ufeff"

    def __init__(self):
        self.time_table = []
        self.current_time = 0

    def load_csv_str(self, csv_str):
        warn_msg = ""
        # UTF-8 BOM removal
        if csv_str.startswith(self.BOM):
            bom_len = len(self.BOM)
            csv_str = csv_str[bom_len:]

        lines = csv_str.strip().split("\n")

        # Validate the header
        header = lines[0].strip().split(",")
        # header-correct_header dictionary to get the index of each header
        header_dict = {header[i]: i for i in range(len(header))}

        # Process each row
        if "end" not in header_dict.keys():
            is_no_end = True
            header_dict["end"] = -1
        else:
            is_no_end = False
        # For checking if the previous row has an end time by "end_sec_str" or "duration_sec_str"
        has_end_time = True
        for i, line in enumerate(lines[1:]):
            # Skip if the line is empty like ",,,,," or ",,,,"
            if line.strip().replace(",", "") == "":
                print(f"[line {i + 1}] Empty line")
                continue

            (
                title,
                member,
                duration_sec_str,
                start_sec_str,
                end_sec_str,
                fixed,
                instruction,
            ) = self._asign(line, header_dict, is_no_end)

            duration_sec = time_format.time_str_to_seconds(duration_sec_str)
            start_sec = time_format.time_str_to_seconds(start_sec_str)
            end_sec = time_format.time_str_to_seconds(end_sec_str)
            if fixed not in ["start", "duration", "none"]:
                raise ValueError(f"[line {i + 1}] Invalid fixed code: {fixed}")

            has_error = False
            if fixed == "start":
                if start_sec < self.current_time:
                    warn_msg = f"[line {i + 1}] {title} Conflict with the previous line"
                    has_error = True

                if start_sec == 0 and i != 0:
                    raise ValueError(
                        f"[line {i + 1}] start_sec must be set in fixed==start"
                    )
                if duration_sec > 0:
                    end_sec = start_sec + duration_sec
                elif end_sec > 0:
                    end_sec = end_sec
                # if duration and end are not set, get the next start time
                elif i < len(lines) - 2:
                    next_line = lines[i + 2]
                    end_sec = self.get_next_start(line, next_line, header_dict)
                    if end_sec == 0:
                        end_sec = start_sec
                else:
                    raise ValueError(f"[line {i + 1}] No next line")
            elif fixed == "duration":
                if duration_sec == 0:
                    raise ValueError(
                        f"[line {i + 1}] duration_sec must be set in fixed==duration"
                    )
                if start_sec == 0 and end_sec == 0:
                    start_sec = self.current_time
                    end_sec = start_sec + duration_sec
                elif start_sec > 0:
                    start_sec = start_sec
                    end_sec = start_sec + duration_sec
                elif end_sec > 0:
                    end_sec = end_sec
                    start_sec = end_sec - duration_sec
                if (i > 0) and (has_end_time is False):
                    warn_msg = (
                        f"[line {i + 1}] No Duration (or End) in the previous line"
                    )
                    has_error = True

            start_td = datetime.timedelta(seconds=start_sec)
            end_td = datetime.timedelta(seconds=end_sec)

            # Add task start and end times to the timetable
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

            # Update current time
            self.current_time = end_sec
            has_end_time = end_sec_str != "" or duration_sec_str != ""
        return warn_msg

    def _asign(self, line_str, header_dict, is_no_end=False):
        splited_line = line_str.strip().split(",")
        title = splited_line[header_dict["title"]]
        member = splited_line[header_dict["member"]]
        duration_sec_str = splited_line[header_dict["duration"]]
        start_sec_str = splited_line[header_dict["start"]]
        if is_no_end:
            end_sec_str = ""
        else:
            end_sec_str = splited_line[header_dict["end"]]
        fixed = splited_line[header_dict["fixed"]]
        if "instruction" in header_dict.keys():
            instruction = splited_line[header_dict["instruction"]]
        else:
            instruction = ""
        return (
            title,
            member,
            duration_sec_str,
            start_sec_str,
            end_sec_str,
            fixed,
            instruction,
        )

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

    def get_next_start(self, current_line, next_line, header_dict):
        (
            title,
            member,
            duration_sec_str,
            start_sec_str,
            end_sec_str,
            fixed,
            instruction,
        ) = self._asign(next_line, header_dict)
        if start_sec_str == "0":
            raise ValueError(f"next_start_sec is 0: {current_line}")
        return time_format.time_str_to_seconds(start_sec_str)
