from ..common import status_icon

class gps_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=22)
        self.underlay_icon = 'satellite_dark'
        self.clear()

    def update(self, mode, sats, maidenhead, icon):
        self.clear()

        sats_text = self.font.render(sats, True, (255,255,255))
        self.surface.blit(sats_text, sats_text.get_rect(midtop=(self.HW,0)))

        mode_text = self.font.render(mode, True, (255,255,255))
        self.surface.blit(mode_text, mode_text.get_rect(midtop=(self.HW,28)))

        mh_text = self.font.render(maidenhead[:6], True, (255,255,255))
        self.surface.blit(mh_text, mh_text.get_rect(midtop=(self.HW,56)))

        self.overlay_icon = icon
        super().update()
