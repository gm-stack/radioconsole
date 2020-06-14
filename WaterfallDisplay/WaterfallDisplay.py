import pygame

import config

from . import turbo_colormap

class WaterfallDisplay(object):
    REL_BANDWIDTHS = {
        1200000: range(100000, 600001, 100000),
        600000: range(100000, 300001, 100000),
        300000: range(100000, 300001, 100000),
        150000: range(100000, 300001, 100000),
        75000: range(100000, 300001, 100000),
        37500: range(100000, 300001, 100000),
        18750: range(100000, 300001, 100000)
    }

    def __init__(self, rf, bounds):
        self.X, self.Y, self.W, self.H = bounds
        self.WF_Y = self.Y + config.GRAPH_HEIGHT
        self.WF_H = self.H - config.GRAPH_HEIGHT
        
        self.waterfall_surf = pygame.Surface((self.W, self.WF_H))
        self.graph_surf = pygame.Surface((self.W, config.GRAPH_HEIGHT))
        self.rf = rf

        self.num_fft_bins = None
        self.display_bandwidth = None

        self.absmode = False
        self.abs_freq_low = 7000000
        self.abs_freq_high = 7300000

        self.rel_bandwidth_index = 0
        self.rel_bandwidth = list(self.REL_BANDWIDTHS.keys())[self.rel_bandwidth_index]

    def draw_wf(self, fft, screen):
        self.waterfall_surf.scroll(0, 1)
        self.waterfall_surf.lock()
        for i in range(self.W):
            pixel_colour = turbo_colormap.interpolate_or_clip(fft[i])
            pixel_colour = [int(c*255) for c in pixel_colour]
            self.waterfall_surf.set_at((i, 0), pixel_colour )
        self.waterfall_surf.unlock()

        screen.blit(self.waterfall_surf, (self.X,self.WF_Y), area=(0, 0, self.W, self.WF_H))
    
    def freq_to_x(self, freq):
        if self.absmode:
            centre_freq = (self.abs_freq_low + self.abs_freq_high) // 2
        else:
            centre_freq = config.CURRENT_FREQ
        centre_pixel = config.DISPLAY_W / 2
        hz_per_pixel = (self.display_bandwidth) / float(config.DISPLAY_W)
        
        return centre_pixel + int((freq - centre_freq) / hz_per_pixel)

    def draw_marker(self, freq, screen, highlight=False, relative=False):
        x = self.freq_to_x(freq)
        font = pygame.font.Font(None, 24)

        text_colour = (255, 0, 0) if highlight else (0, 255, 255)
        line_colour = (255, 0, 0) if highlight else (0, 128, 0)
        
        label = f"{int(freq/1000)}" if not relative else f"{(freq-config.CURRENT_FREQ)/1000:+.1f}k".replace(".0","")

        text = font.render(label, True, text_colour)
        text_w = text.get_width()
        text_h = text.get_height()

        text_x = max(min(x-(text_w/2), config.DISPLAY_W - text_w), 0)
        screen.blit(text, (text_x, self.Y))
        
        if x > 0 and x < config.DISPLAY_W:
            pygame.draw.line(screen, line_colour, (x, self.Y + text_h), (x, self.Y + self.H))

    def draw_graph(self, fft, screen):
        self.graph_surf.fill((0, 0, 0))
        for i,j in zip(range(self.W), range(1,self.W)):
            try:
                this_y = config.GRAPH_HEIGHT - int(fft[i] * float(config.GRAPH_HEIGHT))
                next_y = config.GRAPH_HEIGHT - int(fft[j] * float(config.GRAPH_HEIGHT))
            except OverflowError:
                continue
            pygame.draw.line(self.graph_surf, (0,255,0), (i, this_y), (j, next_y))

        screen.blit(self.graph_surf, (self.X, self.Y), area=(0, 0, self.W, config.GRAPH_HEIGHT))

    def draw(self, screen):
        total_fft_bw = (config.SAMPLE_RATE)
        if self.absmode: # absolute frequency display
            self.display_bandwidth = self.abs_freq_high - self.abs_freq_low
            self.num_fft_bins = int((total_fft_bw / self.display_bandwidth) * config.DISPLAY_W)
            
            centre_freq = config.CURRENT_FREQ
            centre_bin = self.num_fft_bins // 2
            hz_per_pixel = total_fft_bw / float(self.num_fft_bins)

            leftside_bin = centre_bin + int((self.abs_freq_low - centre_freq) / hz_per_pixel)

            fft = self.rf.fft(self.num_fft_bins)[::-1][leftside_bin:]

            fft = (fft - config.RF_MIN) / (config.RF_MAX - config.RF_MIN)
        else:
            self.display_bandwidth = self.rel_bandwidth
            self.num_fft_bins = int((total_fft_bw / self.display_bandwidth) * config.DISPLAY_W)

            centre_freq = config.CURRENT_FREQ
            centre_bin = self.num_fft_bins // 2
            hz_per_pixel = total_fft_bw / float(self.num_fft_bins)

            leftside_bin = centre_bin + int((centre_freq - (self.rel_bandwidth / 2) - centre_freq) / hz_per_pixel)

            fft = self.rf.fft(self.num_fft_bins)[::-1][leftside_bin:]
            fft = (fft - config.RF_MIN) / (config.RF_MAX - config.RF_MIN)

        
        self.draw_wf(fft, screen)
        self.draw_graph(fft, screen)

        if self.absmode:
            self.draw_marker(config.CURRENT_FREQ, screen, highlight=True)
            self.draw_marker(7000000, screen)
            self.draw_marker(7100000, screen)
            self.draw_marker(7200000, screen)
            self.draw_marker(7300000, screen)
        else:
            self.draw_marker(config.CURRENT_FREQ, screen, highlight=True, relative=True)
            for m in self.REL_BANDWIDTHS[self.rel_bandwidth]:
                self.draw_marker(config.CURRENT_FREQ + m, screen, relative=True)
                self.draw_marker(config.CURRENT_FREQ - m, screen, relative=True)




    def keydown(self, k, m):
        if k == 'up' and not (m & pygame.KMOD_SHIFT):
            config.RF_MAX += 10
            print(f"rf_max: {config.RF_MAX}")
            return True
        if k == 'down' and not (m & pygame.KMOD_SHIFT):
            config.RF_MAX -= 10
            print(f"rf_max: {config.RF_MAX}")
            return True
        if k == 'up' and (m & pygame.KMOD_SHIFT):
            config.RF_MIN += 10
            print(f"rf_min: {config.RF_MIN}")
            return True
        if k == 'down' and (m & pygame.KMOD_SHIFT):
            config.RF_MIN -= 10
            print(f"rf_min: {config.RF_MIN}")
            return True
        if k == 'r':
            self.absmode = not self.absmode
            return True
        if k == 'left':
            self.rel_bandwidth_index -= 1
            self.rel_bandwidth = list(self.REL_BANDWIDTHS.keys())[self.rel_bandwidth_index % len(self.REL_BANDWIDTHS)]
            return True
        if k == 'right':
            self.rel_bandwidth_index += 1
            self.rel_bandwidth = list(self.REL_BANDWIDTHS.keys())[self.rel_bandwidth_index % len(self.REL_BANDWIDTHS)]
            return True
        return False
