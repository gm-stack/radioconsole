import pygame
from pygame import surface

from ..common import status_icon

class gps_status_icon(status_icon):
    def __init__(self):
        super().__init__()

    def update(self, mode, sats, icon):
        self.clear()

        mode_text = self.font.render(mode, True, (255,255,255))
        self.surface.blit(mode_text, (0, 0))

        sats_text = self.font.render(sats, True, (255,255,255))
        self.surface.blit(sats_text, (60-sats_text.get_width(), 0))

        self.overlay_icon = icon
        super().update()