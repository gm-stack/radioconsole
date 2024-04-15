import os

import pygame

base_path = os.path.dirname(__file__)
font_cache = {}
fonts = {
    "B612": {
        "regular_path": "ttf/B612-Regular.ttf",
        "bold_path": "ttf/B612-Bold.ttf",
        "italic_path": "ttf/B612-Italic.ttf",
        "bold_italic_path": "ttf/B612-BoldItalic.ttf"
    },
    "B612Mono": {
        "regular_path": "ttf/B612Mono-Regular.ttf",
        "bold_path": "ttf/B612Mono-Bold.ttf",
        "italic_path": "ttf/B612Mono-Italic.ttf",
        "bold_italic_path": "ttf/B612Mono-BoldItalic.ttf"
    }
}

def load_fonts(gui):
    for font_name, font in fonts.items():
        font_paths = {
            arg: os.path.join(base_path, font_path)
            for arg, font_path in font.items()
        }

        gui.add_font_paths(
            font_name=font_name,
            **font_paths
        )

    for size in (9, 10, 12, 14, 16, 18, 20, 24):
        gui.preload_fonts([
            {'name': font_name, 'point_size': size, 'style': 'regular'}
            for font_name in fonts
        ])

def get_font(font_name, font_style, font_size):
    key = (font_name, font_style, font_size)
    if key in font_cache:
        return font_cache[key]

    font_path = os.path.join(base_path, f"ttf/{font_name}-{font_style}.ttf")
    font = pygame.font.Font(font_path, font_size)
    font_cache[key] = font
    return font