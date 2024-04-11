import pygame
import gps
from pygame import surface

from ..common import status_icon

class gps_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=14)
        self.underlay_icon = 'satellite_dark'
        self.clear()

    def update(self, mode, sats, maidenhead, icon):
        self.clear()

        mode_text = self.font.render(mode, True, (255,255,255))
        self.surface.blit(mode_text, mode_text.get_rect(midtop=(30,20)))

        sats_text = self.font.render(sats, True, (255,255,255))
        self.surface.blit(sats_text, sats_text.get_rect(midtop=(30,0)))

        mh_text = self.font.render(maidenhead[:6], True, (255,255,255))
        self.surface.blit(mh_text, mh_text.get_rect(midtop=(30,40)))

        self.overlay_icon = icon
        super().update()