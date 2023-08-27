import pygame
from pygame import surface

class raspi_status_icon():
    surface = None
    bgcolour = (0,0,0,255)
    def __init__(self):
        self.surface = surface.Surface((60,60), pygame.SRCALPHA)
        self.font = pygame.font.Font("ttf/FiraCode-Regular.ttf", 12)
        self.surface.fill(self.bgcolour)

    def update(self, data):
        self.surface.fill(self.bgcolour)

        if data.get('status') != '':
            return

        host_text = self.font.render(data.get('hostname', ''), True, (255,255,255))
        self.surface.blit(host_text, (0, 0))

        # colour text
        temp_num = data.get('temp_num', 0.0)
        temp_text = self.font.render(f'{temp_num:.1f}\N{DEGREE SIGN}C', True, (255,255,255))
        self.surface.blit(temp_text, (0, 16))

        clock_text = self.font.render(data.get('freqdisp', '').split('/')[0], True, (255,255,255))
        self.surface.blit(clock_text, (0, 32))