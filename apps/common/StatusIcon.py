import pygame
from .IconManager import radioconsole_icons

import fonts

IMAGE_CACHE = None

ICON_W = 92
ICON_H = 90

class status_icon(object):
    def __init__(self, font_size=16):
        self.overlay_icon = None
        self.underlay_icon = None

        self.W, self.H = ICON_W, ICON_H
        self.HW = self.W / 2 # HW = half-width

        self.surface = pygame.surface.Surface((self.W,self.H), pygame.SRCALPHA)
        self.bgcolour = (0,0,0,255)
        self.font = fonts.get_font("B612", "Regular", font_size)
        self.clear()

    def clear(self):
        self.surface.fill(self.bgcolour)
        if self.underlay_icon and self.underlay_icon in radioconsole_icons:
            self.surface.blit(radioconsole_icons[self.underlay_icon], (0,0))

    def update(self):
        if self.overlay_icon and self.overlay_icon in radioconsole_icons:
            self.surface.blit(radioconsole_icons[self.overlay_icon], (0,0))
