import pygame

from ..common import status_icon
from ..common import time_format

class direwolf_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=14)
        self.font_bigger = pygame.font.Font("ttf/B612-Regular.ttf", 16)
        self.underlay_icon = 'direwuff_dark'
        self.clear()

    def update(self, icon, rx, tx_ig, tx_rf, tx_rf_igated):
        self.clear()

        rx = self.font.render(time_format.mm_ss_since(rx), True, (0xFF,0xFF,0xFF))
        self.surface.blit(rx, rx.get_rect(midtop=(30,0)))

        tx_ig = self.font.render(time_format.mm_ss_since(tx_ig), True, (0xFF,0xFF,0xFF))
        self.surface.blit(tx_ig, tx_ig.get_rect(midtop=(30,20)))


        if tx_rf_igated:
            colour = (0x00,0xFF,0x00)
        else:
            colour = (0xFF,0xA5,0x00)

        if not tx_rf:
            colour = (0xFF,0xFF,0xFF)

        tx_rf = self.font.render(time_format.mm_ss_since(tx_rf), True, colour)
        self.surface.blit(tx_rf, tx_rf.get_rect(midtop=(30,40)))

        self.overlay_icon = icon
        super().update()