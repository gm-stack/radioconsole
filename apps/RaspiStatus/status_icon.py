from pygame import gfxdraw

from ..common import status_icon

class raspi_status_icon(status_icon):
    def __init__(self):
        super().__init__()
        self.underlay_icon = 'raspberrypi_dark'
        self.clear()

    def update(self, data, icon):
        self.clear()

        host_text = self.font.render(data.get('hostname', ''), True, (255,255,255))
        self.surface.blit(host_text, host_text.get_rect(midtop=(30, 0)))

        # todo: colour text
        temp_num = data.get('temp_num')
        if temp_num:
            temp_text = self.font.render(f'{temp_num:.1f}\N{DEGREE SIGN}C', True, (255,255,255))
            self.surface.blit(temp_text, temp_text.get_rect(midtop=(30, 16)))

        clock_text = self.font.render(data.get('freqdisp', '').split('/')[0], True, (255,255,255))
        self.surface.blit(clock_text, clock_text.get_rect(midtop=(30, 32)))

        try:
            cpu_percent = float(data.get('cpu_all_percent', ''))
            self.draw_cpu_bar(cpu_percent)
        except ValueError:
            pass

        self.overlay_icon = icon
        super().update()

    def draw_cpu_bar(self, cpu):
        margin = 4
        bar_height = 6

        # 0..100 to 0..(60 - (margin*2) - 2)
        cpu = (cpu / 100.0) * (60 - (margin * 2) - 2)

        # require it to be at least 2
        # to have some graph
        cpu = max(cpu, 2.0)

        shape = [
                (margin,60-margin), # bottom left
                (cpu,60-margin), # bottom right
                (cpu,60-(margin+bar_height)), # top right
                (margin,60-(margin+bar_height)) # top left
            ]

        gfxdraw.aapolygon(self.surface, shape, (0, 128, 0, 255))
        gfxdraw.filled_polygon(self.surface, shape, (0, 128, 0, 255))