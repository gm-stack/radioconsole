from ..common import status_icon

class systemd_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=24)
        self.underlay_icon = 'services_dark'
        self.clear()

    def update(self, total, running, errored, icon):
        self.clear()

        running_count = self.font.render(f"{running}/{total}", True, (255,255,255))
        self.surface.blit(running_count, running_count.get_rect(midtop=(self.HW, 0)))

        errs_text = self.font.render(f"{errored} err", True, (255,255,255))
        self.surface.blit(errs_text, errs_text.get_rect(midtop=(self.W/2, 20)))

        self.overlay_icon = icon
        super().update()
