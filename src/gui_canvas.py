import tkinter as tk

rect_colors = [
    "#a9a9af",
    "#7c7c83",
    "#d5d5e0",
    "#6a607d",
    "#b0c0d6",
    "#8f8e9e",
    "#a3a3bc",
    "#e0e0fb",
    "#85859f",
    "#c1c1d0",
    "#b0b0ce",
    "#ebebfa",
    "#9b9ba6",
    "#d8d8ef",
]


class Canvas(tk.Canvas):
    fonts = {
        "tiny": {
            "font": ("Helvetica", 8),
            "spacing": 60,
            "height": 8,
        },
        "small": {
            "font": ("Helvetica", 10),
            "spacing": 70,
            "height": 10,
        },
        "normal": {
            "font": ("Helvetica", 12),
            "spacing": 80,
            "height": 12,
        },
    }

    def __init__(self, master, bg="white", width=700):
        super().__init__(master, bg=bg, width=width)
        self.rect_width = 200

    def set_font(self, font):
        self.font = self.fonts[font]["font"]

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
            84, y_start, self.rect_width, y_end, fill=color, outline="#101010", tag=tag
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
