def save_as_svg(tk_canvas, filename):
    svg = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    width = tk_canvas.winfo_width() + 100
    height = tk_canvas.winfo_height()
    svg += f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>\n"

    for item in tk_canvas.find_all():
        if tk_canvas.type(item) == "rectangle":
            x1, y1, x2, y2 = tk_canvas.coords(item)
            color = tk_canvas.itemcget(item, "fill")
            svg += f"<rect x='{x1}' y='{y1}' width='{x2-x1}' height='{y2-y1}' fill='{color}' stroke='black' />\n"
        elif tk_canvas.type(item) == "text":
            x, y = tk_canvas.coords(item)
            text = tk_canvas.itemcget(item, "text")
            anchor = tk_canvas.itemcget(item, "anchor")
            font = tk_canvas.itemcget(item, "font")
            font_size = int(font.split(" ")[1])

            if anchor == "e":
                anchor = "end"
            elif anchor == "w":
                anchor = "start"
            elif anchor == "n":
                anchor = "middle"

            y += font_size / 2 - 2
            svg += f"<text x='{x}' y='{y}' font-family='Helvetica' font-size='{font_size}' text-anchor='{anchor}'>{text}</text>\n"
        elif tk_canvas.type(item) == "line":
            x1, y1, x2, y2 = tk_canvas.coords(item)
            svg += f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='black' />\n"

    svg += "</svg>"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(svg)
