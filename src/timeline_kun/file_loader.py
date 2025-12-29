import os

from . import csv_to_timetable


class FileLoader:
    def __init__(
        self,
        intermission_desc="Intermission",
        fallback_encoding="utf-8-sig",
    ):
        self.stage_list = []
        self.intermission_desc = intermission_desc
        self.fallback_encoding = fallback_encoding
        self.encoding = None

    def _read_file(self, tar_path):
        self.stage_list = []
        self.encoding = None

        if not os.path.exists(tar_path):
            print(f"File not found: {tar_path}")
            return None
        try:
            with open(tar_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.encoding = "utf-8"
            return content
        except UnicodeDecodeError:
            print(f"UTF-8 decoding failed, falling back to {self.fallback_encoding}")
            try:
                with open(tar_path, "r", encoding=self.fallback_encoding) as f:
                    content = f.read()
                self.encoding = self.fallback_encoding
                return content
            except UnicodeDecodeError:
                print(
                    f"{self.fallback_encoding} decoding also failed, falling back to cp932"
                )
                try:
                    with open(tar_path, "r", encoding="cp932") as f:
                        content = f.read()
                    self.encoding = "cp932"
                    return content
                except UnicodeDecodeError:
                    self.encoding = None
                    raise ValueError(f"File encoding not supported")

    def load_file_for_preview(self, csv_path):
        timetable_csv_str = self._read_file(csv_path)
        if timetable_csv_str is None:
            return "Load file failed", None
        time_table = csv_to_timetable.TimeTable()
        try:
            warn_msg = time_table.load_csv_str(timetable_csv_str)
        except ValueError as e:
            raise e
        return warn_msg, time_table

    def load_file_for_timer(self, start_index: int, csv_path: str):
        timetable_csv_str = self._read_file(csv_path)
        if timetable_csv_str is None:
            return
        time_table = csv_to_timetable.TimeTable()
        time_table.load_csv_str(timetable_csv_str)

        start_row = time_table.get_timetable()[start_index]
        for i, row in enumerate(time_table.get_timetable()):
            if i < start_index:
                continue
            self.stage_list.append(
                {
                    "title": row["title"],
                    "start_dt": row["start"] - start_row["start"],
                    "end_dt": row["end"] - start_row["start"],
                    "duration": row["end"] - row["start"],
                    "member": row["member"],
                    "instruction": row["instruction"],
                }
            )

        # Intermission check
        intermission_list = []
        for i, stage in enumerate(self.stage_list):
            # check if intermission space exists
            current_end_dt = stage["end_dt"]
            if i + 1 < len(self.stage_list):
                next_start_dt = self.stage_list[i + 1]["start_dt"]
                if current_end_dt != next_start_dt:
                    intermission_list.append(
                        {
                            "title": self.intermission_desc,
                            "start_dt": current_end_dt,
                            "end_dt": next_start_dt,
                            "duration": next_start_dt - current_end_dt,
                            "member": "",
                            "instruction": "",
                        }
                    )
                else:
                    intermission_list.append(None)
        # Insert intermission into stage list from the end
        for i in range(len(intermission_list) - 1, -1, -1):
            if intermission_list[i] is not None:
                self.stage_list.insert(i + 1, intermission_list[i])

    def get_stage_list(self):
        return self.stage_list

    def get_encoding(self):
        return self.encoding

    def clear(self):
        self.stage_list = []

def utf8_to_utf8bom(tar_path: str, fallback_encoding: str) -> bool:
    """
    Save as UTF-8 with BOM so it can be opened in Excel.
    First, try reading as UTF-8; if that fails, read using fallback_encoding.
    Then, write the content back as UTF-8 with BOM.
    """
    try:
        with open(tar_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError as e:
        try:
            with open(tar_path, "r", encoding=fallback_encoding) as f:
                content = f.read()
        except UnicodeDecodeError as e:
            print(f"Error converting {tar_path}: {e}")
            return False

    with open(tar_path, "w", encoding="utf-8-sig") as f:
        f.write(content)
    return True
