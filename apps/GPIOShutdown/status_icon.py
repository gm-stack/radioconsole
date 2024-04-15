from ..common import status_icon
from ..common import time_format

import fonts

class gpio_shutdown_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=14)
        self.font_bigger = fonts.get_font("B612", "Regular", 16)
        self.underlay_icon = 'power_dark'
        self.clear()

    def update(self, icon, timer, colour, status):
        self.clear()

        countdown_text = time_format.mm_ss(timer)

        status_text = self.font.render(status, True, (0xFF,0xFF,0xFF))
        self.surface.blit(status_text, status_text.get_rect(midtop=(30,0)))

        timer_text = self.font_bigger.render(countdown_text, True, colour)
        self.surface.blit(timer_text, timer_text.get_rect(midbottom=(30,56)))

        self.overlay_icon = icon
        super().update()