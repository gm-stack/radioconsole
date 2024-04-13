import pygame

from ..common import status_icon
from ..common import time_format

class direwolf_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=14)
        self.font_bigger = pygame.font.Font("ttf/B612-Regular.ttf", 16)
        self.underlay_icon = 'direwuff_dark'
        self.clear()

    def update(self, icon, rx, tx_ig, tx_rf):
        self.clear()

        rx = self.font.render(time_format.mm_ss(rx), True, (0xFF,0xFF,0xFF))
        self.surface.blit(rx, rx.get_rect(midtop=(30,0)))

        tx_ig = self.font.render(time_format.mm_ss(tx_ig), True, (0xFF,0xFF,0xFF))
        self.surface.blit(tx_ig, tx_ig.get_rect(midtop=(30,20)))

        tx_rf = self.font.render(time_format.mm_ss(tx_rf), True, (0xFF,0xFF,0xFF))
        self.surface.blit(tx_rf, tx_rf.get_rect(midtop=(30,40)))

        self.overlay_icon = icon
        super().update()