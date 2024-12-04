import tkinter as tk


class Canvas(tk.Canvas):
    def __init__(self, master, bg="white", width=700):
        super().__init__(master, bg=bg, width=width)
        self.rect_width = 200

    def set_font(self, font):
        self.font = font

    def set_scale(self, scale):
        self.scale = scale

    def draw_start_line(self, start, total_duration):
        self.delete("start_line")
        self.delete("highlight")
        start_sec = start.total_seconds()
        y_start = start_sec * self.scale + 20
        self._create_start_line(84, y_start, 10, "red")
        self.tag_lower("start_line")
        self.delete("time")

    def _create_start_line(self, x, y, size, color):
        self.create_polygon(
            x - size,
            y - size / 2,
            x,
            y,
            x - size,
            y + size / 2,
            fill=color,
            tag="start_line",
        )

    def create_rect(self, start, duration, color, tag="rect"):
        start_sec = start.total_seconds()
        duration_sec = duration.total_seconds()
        y_start = start_sec * self.scale + 20
        rect_height = duration_sec * self.scale
        y_end = y_start + rect_height
        self.create_rectangle(
            84,
            y_start,
            self.rect_width,
            y_end,
            fill=color,
            outline="#101010",
            tag=tag
        )
        return rect_height

    def create_time(self, start, text):
        start_sec = start.total_seconds()
        y_start = start_sec * self.scale + 20
        if y_start < 10:
            return
        self.create_text(
            70,
            y_start,
            text=text,
            anchor="e",
            font=self.font,
            tag="time",
        )

    def create_label(self, start, duration, text):
        start_sec = start.total_seconds()
        duration_sec = duration.total_seconds()
        y_start = start_sec * self.scale + 20
        rect_height = duration_sec * self.scale
        y_end = y_start + rect_height
        self.create_text(
            self.rect_width + 10,
            (y_start + y_end) / 2,
            text=text,
            anchor="w",
            font=self.font,
        )
