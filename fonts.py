def load_fonts(gui):
    gui.add_font_paths(
        font_name="B612",
        regular_path="ttf/B612-Regular.ttf", 
        bold_path="ttf/B612-Bold.ttf",
        italic_path="ttf/B612-Italic.ttf",
        bold_italic_path="ttf/B612-BoldItalic.ttf",
    )
    gui.add_font_paths(
        font_name="B612Mono",
        regular_path="ttf/B612Mono-Regular.ttf", 
        bold_path="ttf/B612Mono-Bold.ttf",
        italic_path="ttf/B612Mono-Italic.ttf",
        bold_italic_path="ttf/B612Mono-BoldItalic.ttf",
    )
    gui.preload_fonts([
        {
            "name": "B612",
            "point_size": 14,
            "style": "regular"
        },
        {
            "name": "B612Mono",
            "point_size": 14,
            "style": "regular"
        }
    ])