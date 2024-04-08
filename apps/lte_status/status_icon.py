import pygame
from pygame import surface

from ..common import status_icon

class lte_status_icon(status_icon):
    def __init__(self):
        super().__init__()

    def update(self, data, icon):
        self.clear()

        mode_text = self.font.render(data.get('mode', ''), True, (255,255,255))
        self.surface.blit(mode_text, (0, 0))

        # todo: colour text
        mode_text = self.font.render(data.get('rsrq', ''), True, (255,255,255))
        self.surface.blit(mode_text, (0, 16))

        if 'bands' in data:
            band_text = self.font.render(data['bands'][0]['band'], True, (255,255,255))
            self.surface.blit(band_text, (60-band_text.get_width(), 0))
        
        self.overlay_icon = icon
        super().update()