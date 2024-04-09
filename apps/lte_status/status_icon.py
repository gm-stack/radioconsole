import pygame
from pygame import surface, gfxdraw

from ..common import status_icon

class lte_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=14)
        self.underlay_icon = 'signal_dark'
        self.clear()

    def update(self, data, icon):
        self.clear()

        mode_text = self.font.render(data.get('mode', ''), True, (255,255,255))
        self.surface.blit(mode_text, (4, 0))

        # todo: colour text
        try:
            rsrq = data.get('rsrq', '')
            rsrq = float(rsrq)
            if rsrq > -10:
                colour = (0, 255, 0, 255)
            elif rsrq > -15:
                colour = (255, 255, 0, 255)
            elif rsrq > -20:
                colour = (255, 165, 0, 255)
            else:
                colour = (255, 0, 0, 255)

            rsrq_text = self.font.render(data.get('rsrq', ''), True, colour)
            self.surface.blit(rsrq_text, (4, 20))
            self.draw_signal_bar(rsrq)
        except ValueError:
            pass

        if 'bands' in data:
            band_text = self.font.render(data['bands'][0]['band'], True, (255,255,255))
            self.surface.blit(band_text, (56-band_text.get_width(), 0))
        
        self.overlay_icon = icon
        super().update()

    def draw_signal_bar(self, rsrq):
        # -20..0 is now 0..20
        rsrq += 20.0
        rsrq = max(rsrq, 0.0)
        rsrq = min(rsrq, 20.0)
        
        # 0..20 now 0..48
        rsrq *= 2.4
        
        # require it to be at least 2
        # to have some graph
        rsrq = max(rsrq, 2.0)

        margin = 4
        offset = 5

        shape = [
                (margin,60-margin), # bottom left
                (rsrq,60-margin), # bottom right
                (rsrq,60-(margin+offset+(rsrq/8))), # top right
                (margin,60-(margin+offset)) # top left
            ]

        gfxdraw.aapolygon(self.surface, shape, (0, 128, 0, 255))
        gfxdraw.filled_polygon(self.surface, shape, (0, 128, 0, 255))