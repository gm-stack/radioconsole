import pygame
from pygame import surface

from ..common import status_icon

class gps_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=14)
        self.underlay_icon = 'satellite_dark'
        self.clear()

    def update(self, mode, sats, icon):
        self.clear()

        mode_text = self.font.render(mode, True, (255,255,255))
        self.surface.blit(mode_text, (30-(mode_text.get_width()/2), 20))

        sats_text = self.font.render(sats, True, (255,255,255))
        self.surface.blit(sats_text, (30-(sats_text.get_width()/2), 0))

        self.overlay_icon = icon
        super().update()