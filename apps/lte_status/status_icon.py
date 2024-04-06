import pygame
from pygame import surface

class lte_status_icon():
    surface = surface.Surface((60,60), pygame.SRCALPHA)
    bgcolour = (0,0,0,255)
    def __init__(self):
        self.font = pygame.font.Font("ttf/B612-Regular.ttf", 12)
        self.surface.fill(self.bgcolour)

    def update(self, data):
        self.surface.fill(self.bgcolour)

        mode_text = self.font.render(data.get('mode', ''), True, (255,255,255))
        self.surface.blit(mode_text, (0, 0))

        # colour text
        mode_text = self.font.render(data.get('rsrq', ''), True, (255,255,255))
        self.surface.blit(mode_text, (0, 16))

        if 'bands' in data:
            band_text = self.font.render(data['bands'][0]['band'], True, (255,255,255))
            self.surface.blit(band_text, (60-band_text.get_width(), 0))