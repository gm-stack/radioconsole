from util import gradient
from ..common import status_icon
from ..common import time_format

import fonts

class gpio_shutdown_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=22)
        #self.font_bigger = fonts.get_font("B612", "Regular", 16)
        self.underlay_icon = 'power_dark'
        self.clear()

    def update(self, icon, ssh_connection_issue, timer, colour, status):
        self.clear()

        status_text = self.font.render(status, True, colour)
        self.surface.blit(status_text, status_text.get_rect(midtop=(self.HW,0)))

        countdown_text = time_format.mm_ss(timer)
        countdown_colour = gradient(
            timer,
            {
                300: (0,255,0), # green
                60: (255,222,33), # yellow
                30: (255,0,0) # red
            }
        )

        timer_text = self.font.render(countdown_text, True, countdown_colour)
        self.surface.blit(timer_text, timer_text.get_rect(midtop=(self.HW,32)))

        if ssh_connection_issue:
            self.overlay_icon = 'warning_red'
        else:
            self.overlay_icon = icon

        super().update()
