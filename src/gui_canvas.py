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
        self.mode = "vertical"
        self.rect_width = 15

    def set_font(self, font):
        self.font = self.fonts[font]["font"]

    def set_scale(self, scale):
        self.scale = scale

    def set_direction(self, mode):
        if mode not in ["horizontal", "vertical"]:
            raise ValueError("mode must be 'horizontal' or 'vertical'")
        self.mode = mode

    def draw_start_line(self, start, total_duration):
        self.delete("start_line")
        self.delete("highlight")
        start_sec = start.total_seconds()
        if self.mode == "vertical":
            y_start = start_sec * self.scale + 20
            self._create_start_mark_right(84, y_start, 10, "red")
        else:
            x_start = start_sec * self.scale + 50
            self._create_start_mark_up(x_start, 200 + self.rect_width, 10, "red")
        self.tag_lower("start_line")
        self.delete("time")

    def _create_start_mark_right(self, x, y, size, color):
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

    def _create_start_mark_up(self, x, y, size, color):
        self.create_polygon(
            x - size / 2,
            y + size,
            x,
            y,
            x + size / 2,
            y + size,
            fill=color,
            tag="start_line",
        )

    def create_rect(self, start, duration, color, tag="rect"):
        start_sec = start.total_seconds()
        duration_sec = duration.total_seconds()
        rect_length = duration_sec * self.scale
        if self.mode == "vertical":
            y_start = start_sec * self.scale + 20
            y_end = y_start + rect_length
            self.create_rectangle(
                84,
                y_start,
                84 + self.rect_width,
                y_end,
                fill=color,
                outline="#101010",
                tag=tag,
            )
        else:
            x_start = start_sec * self.scale + 50
            x_end = x_start + rect_length
            self.create_rectangle(
                x_start,
                200,
                x_end,
                200 + self.rect_width,
                fill=color,
                outline="#101010",
                tag=tag,
            )
        return rect_length

    def create_time(self, start, text):
        start_sec = start.total_seconds()
        if self.mode == "vertical":
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
        else:
            x_start = start_sec * self.scale + 50
            self.create_text(
                x_start,
                210 + self.rect_width,
                text=text,
                anchor="n",
                font=self.font,
                tag="time",
            )
            self.create_line(
                x_start,
                200,
                x_start,
                208 + self.rect_width,
                fill="#101010",
                tag="time",
            )

    def create_label(self, start, duration, title_str, time_str):
        start_sec = start.total_seconds()
        duration_sec = duration.total_seconds()
        rect_length = duration_sec * self.scale
        if self.mode == "vertical":
            y_start = start_sec * self.scale + 20
            y_end = y_start + rect_length
            self.create_text(
                100 + self.rect_width,
                (y_start + y_end) / 2,
                text=f"{title_str} ({time_str})",
                anchor="w",
                font=self.font,
            )
        else:
            x_start = start_sec * self.scale + 50
            x_end = x_start + rect_length
            self.create_text(
                (x_start + x_end) / 2,
                150,
                text=f"{title_str}\n{time_str}",
                anchor="n",
                font=self.font,
            )
            self.create_line(
                (x_start + x_end) / 2,
                175,
                (x_start + x_end) / 2,
                200,
                fill="#101010",
            )
