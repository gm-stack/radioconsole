import pygame
from pygame import surface

from ..common import status_icon

class systemd_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=14)
        self.underlay_icon = 'services_dark'
        self.clear()

    def update(self, total, running, errored, icon):
        self.clear()

        running_count = self.font.render(f"{running}/{total}", True, (255,255,255))
        self.surface.blit(running_count, (30-(running_count.get_width()/2), 0))

        errs_text = self.font.render(f"{errored} errs", True, (255,255,255))
        self.surface.blit(errs_text, (30-(errs_text.get_width()/2), 20))

        self.overlay_icon = icon
        super().update()