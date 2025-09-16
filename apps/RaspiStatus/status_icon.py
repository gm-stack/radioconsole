from pygame import gfxdraw

import fonts
from ..common import status_icon
from util import gradient

class raspi_status_icon(status_icon):
    def __init__(self):
        super().__init__(font_size=18)
        self.font_temperature = fonts.get_font("B612", "Regular", 24)
        self.underlay_icon = 'raspberrypi_dark'
        self.rendered_hostname = None
        self.clear()

    def render_hostname(self, data):
        # if we already have it, return it
        if self.rendered_hostname:
            return self.rendered_hostname

        # if no hostname, return None
        hostname = data.get('hostname')
        if not hostname:
            return None

        # start with 24 point
        font_size = 24
        while True:
            hostname_font = fonts.get_font("B612", "Regular", font_size)
            w,h = hostname_font.size(hostname)

            # if text fits, break out of loop
            if w < (self.W - 4):
                break

            # otherwise try again with smaller font, but don't bother below 6pt
            font_size -= 1
            if font_size < 6:
                break

        self.rendered_hostname = hostname_font.render(hostname, True, (255,255,255))
        return self.rendered_hostname

    def update(self, data, icon):
        self.clear()

        rendered_hostname = self.render_hostname(data)
        height_off = 20
        if rendered_hostname:
            hostname_loc = rendered_hostname.get_rect(center=(self.W/2, 16))
            if hostname_loc.y < 0:
                hostname_loc.y = 0
            self.surface.blit(rendered_hostname, hostname_loc)
            height_off = rendered_hostname.get_height()

        # todo: colour text
        temp_num = data.get('temp_num')

        temp_colour = gradient(
            temp_num,
            {
                60: (255,255,255), # white
                80: (255,222,33), # yellow
                85: (255,0,0) # red
            }
        )

        if temp_num:
            temp_text = self.font_temperature.render(f'{temp_num:.0f}\N{DEGREE SIGN}C', True, temp_colour)
            self.surface.blit(temp_text, temp_text.get_rect(midbottom=(self.W/2, self.H - 26)))

        # On second thoughts, this isn't actually that important, it's just clutter.
        # clock_text = self.font.render(data.get('freqdisp', '').split('/')[0], True, (255,255,255))
        # self.surface.blit(clock_text, clock_text.get_rect(midbottom=(self.W/2, self.H - 16)))

        try:
            cpu_percent = float(data.get('cpu_all_percent', ''))
            self.draw_cpu_bar(cpu_percent)
        except ValueError:
            pass

        self.overlay_icon = icon
        super().update()

    def draw_cpu_bar(self, cpu):
        margin = 4
        bar_height = 12

        # 0..100 to 0..(60 - (margin*2) - 2)
        cpu = (cpu / 100.0) * (self.W - (margin * 2) - 2)

        # require it to be at least 2
        # to have some graph
        cpu = max(cpu, 2.0)

        shape = [
                (margin,self.H-margin), # bottom left
                (cpu,self.H-margin), # bottom right
                (cpu,self.H-(margin+bar_height)), # top right
                (margin,self.H-(margin+bar_height)) # top left
            ]

        gfxdraw.aapolygon(self.surface, shape, (0, 128, 0, 255))
        gfxdraw.filled_polygon(self.surface, shape, (0, 128, 0, 255))
