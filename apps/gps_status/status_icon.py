import pygame
from pygame import surface

class gps_status_icon():
    surface = surface.Surface((60,60), pygame.SRCALPHA)
    bgcolour = (0,0,0,255)
    def __init__(self):
        self.font = pygame.font.Font("ttf/FiraCode-Regular.ttf", 12)
        self.surface.fill(self.bgcolour)

    def update(self, mode, sats):
        self.surface.fill(self.bgcolour)

        mode_text = self.font.render(mode, True, (255,255,255))
        self.surface.blit(mode_text, (0, 0))

        sats_text = self.font.render(sats, True, (255,255,255))
        self.surface.blit(sats_text, (60-sats_text.get_width(), 0))