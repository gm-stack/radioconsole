import pygame
from pygame import surface

from ..common import status_icon

class raspi_status_icon(status_icon):
    def __init__(self):
        super().__init__()

    def update(self, data, icon):
        self.clear()

        host_text = self.font.render(data.get('hostname', ''), True, (255,255,255))
        self.surface.blit(host_text, (0, 0))

        # colour text
        temp_num = data.get('temp_num')
        if temp_num:
            temp_text = self.font.render(f'{temp_num:.1f}\N{DEGREE SIGN}C', True, (255,255,255))
            self.surface.blit(temp_text, (0, 16))

        clock_text = self.font.render(data.get('freqdisp', '').split('/')[0], True, (255,255,255))
        self.surface.blit(clock_text, (0, 32))

        self.overlay_icon = icon
        super().update()