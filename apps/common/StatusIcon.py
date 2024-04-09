import pygame
from .IconManager import radioconsole_icons

IMAGE_CACHE = None

class status_icon(object):
    def __init__(self, font_size=12):
        self.overlay_icon = None
        self.underlay_icon = None
        self.surface = pygame.surface.Surface((60,60), pygame.SRCALPHA)
        self.bgcolour = (0,0,0,255)
        self.font = pygame.font.Font("ttf/B612-Regular.ttf", font_size)
        self.clear()
    
    def clear(self):
        self.surface.fill(self.bgcolour)
        if self.underlay_icon and self.underlay_icon in radioconsole_icons:
            self.surface.blit(radioconsole_icons[self.underlay_icon], (0,0))
    
    def update(self):
        if self.overlay_icon and self.overlay_icon in radioconsole_icons:
            self.surface.blit(radioconsole_icons[self.overlay_icon], (0,0))