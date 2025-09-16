from pygame import gfxdraw
from util import gradient

from ..common import status_icon

class lte_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=22)
        self.underlay_icon = 'signal_dark'
        self.clear()

    def update(self, data, icon):
        self.clear()

        mode_text = self.font.render(data.get('mode', ''), True, (255,255,255))
        self.surface.blit(mode_text, mode_text.get_rect(topleft=(4, 0)))

        try:
            rsrq = data.get('rsrq', '')
            rsrq = float(rsrq)

            rsrq_col = gradient(
                rsrq,
                {
                    -10: (0,255,0),
                    -15: (255,255,0),
                    -20: (255,165,0),
                    -30: (255,0,0)
                }
            )

            rsrq_text = self.font.render(data.get('rsrq', ''), True, rsrq_col)
            self.surface.blit(rsrq_text, rsrq_text.get_rect(midtop=(self.HW, 32)))
            self.draw_signal_bar(rsrq, rsrq_col)
        except ValueError:
            pass

        if 'bands' in data:
            band_text = self.font.render(data['bands'][0]['band'], True, (255,255,255))
            self.surface.blit(band_text, mode_text.get_rect(topright=(self.W - 4,0)))

        self.overlay_icon = icon
        super().update()

    def draw_signal_bar(self, rsrq, rsrq_col):
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
                (margin,self.H-margin), # bottom left
                (rsrq,self.H-margin), # bottom right
                (rsrq,self.H-(margin+offset+(rsrq/8))), # top right
                (margin,self.H-(margin+offset)) # top left
            ]

        gfxdraw.aapolygon(self.surface, shape, rsrq_col)
        gfxdraw.filled_polygon(self.surface, shape, rsrq_col)
