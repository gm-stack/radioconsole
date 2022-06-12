import socket
import threading
import queue
import struct
import time

import pygame
from pygame import surface
import pygame_gui

import crash_handler

from AppManager.app import app

from config_reader import cfg

from . import turbo_colormap

class WaterfallDisplay(app):
    REL_BANDWIDTHS = {
        1200000: range(100000, 600001, 100000),
        600000: range(100000, 300001, 100000),
        300000: range(100000, 300001, 100000),
        150000: range(100000, 300001, 100000),
        75000: range(100000, 300001, 100000),
        37500: range(100000, 300001, 100000),
        18750: range(100000, 300001, 100000)
    }

    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)

        self.colourmap = [(int(c[0]*255), int(c[1]*255), int(c[2]*255)) for c in turbo_colormap.TURBO_COLORMAP_DATA]

        self.fft_queue = queue.Queue()

        self.net_status = ""
        self.net_status_updated = True

        self.params_updated = True

        self.decimate_zoom = True

        BUTTON_Y = cfg.display.DISPLAY_H - self.config.BUTTON_HEIGHT
        self.button_zoom_in = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                0, BUTTON_Y,
                128, self.config.BUTTON_HEIGHT
            ),
            text="Zoom In",
            manager=self.gui
        )
        self.button_zoom_out = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                128, BUTTON_Y,
                128, self.config.BUTTON_HEIGHT
            ),
            text="Zoom Out",
            manager=self.gui
        )
        self.button_absmode = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                cfg.display.DISPLAY_W - 128,
                BUTTON_Y,
                128, self.config.BUTTON_HEIGHT
            ),
            text="Relative Mode",
            manager=self.gui
        )
        self.button_zoommode = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                cfg.display.DISPLAY_W - 256,
                BUTTON_Y,
                128, self.config.BUTTON_HEIGHT
            ),
            text="FFT Zoom",
            manager=self.gui
        )
        if self.decimate_zoom:
            # preserve text when disabled as FFT Zoom
            self.button_zoommode.set_text("Decimate Zoom")

        self.label_status = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                256 + 1, BUTTON_Y + 1,
                cfg.display.DISPLAY_W - 512 - 2, self.config.BUTTON_HEIGHT/2 - 2
            ),
            text='',
            manager=self.gui
        )

        self.label_net_status = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                256 + 1, BUTTON_Y + 1 + self.config.BUTTON_HEIGHT/2,
                cfg.display.DISPLAY_W - 512 - 2, self.config.BUTTON_HEIGHT/2 - 2
            ),
            text='',
            manager=self.gui
        )

        self.X, self.Y, self.W, self.H = bounds
        self.WF_Y = self.Y + self.config.GRAPH_HEIGHT
        self.WF_H = self.H - self.config.GRAPH_HEIGHT - self.config.BUTTON_HEIGHT

        self.connected = False
        self.in_background = True

        self.waterfall_surf = surface.Surface((self.W, self.WF_H))
        self.graph_surf = surface.Surface((self.W, self.config.GRAPH_HEIGHT))

        self.num_fft_bins = None
        self.display_bandwidth = None

        self.absmode = False
        self.current_freq = None
        self.abs_freq_low = 7000000
        self.abs_freq_high = 7300000

        self.rel_bandwidth_index = 0
        self.rel_bandwidth = list(self.REL_BANDWIDTHS.keys())[self.rel_bandwidth_index]
        self.update_status()

        self.backend_thread = threading.Thread(target=self.backend_loop, daemon=True)
        self.backend_thread.start()

        self.udp_backend_thread = threading.Thread(target=self.udp_backend_loop, daemon=True)
        self.udp_backend_thread.start()

    def update_status(self):
        if self.rel_bandwidth > 1000000:
            relbw = f"{self.rel_bandwidth/1000000}M"
        else:
            relbw = f"{self.rel_bandwidth/1000}k"
        self.label_status.set_text(f"BW: {relbw}")

    def process_events(self, e):
        super().process_events(e)
        if e.type == pygame.USEREVENT and e.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if e.ui_element == self.button_zoom_in:
                self.rel_bandwidth_index += 1
                rel_bw_list = list(self.REL_BANDWIDTHS.keys())
                self.rel_bandwidth = rel_bw_list[self.rel_bandwidth_index % len(self.REL_BANDWIDTHS)]
                self.params_updated = True
                self.update_status()
            elif e.ui_element == self.button_zoom_out:
                self.rel_bandwidth_index -= 1
                rel_bw_list = list(self.REL_BANDWIDTHS.keys())
                self.rel_bandwidth = rel_bw_list[self.rel_bandwidth_index % len(self.REL_BANDWIDTHS)]
                self.params_updated = True
                self.update_status()
            elif e.ui_element == self.button_absmode:
                self.absmode = not self.absmode
                if self.absmode:
                    self.button_absmode.set_text("Absolute Mode")
                    self.button_zoom_in.disable()
                    self.button_zoom_out.disable()
                    self.button_zoommode.disable()
                else:
                    self.button_absmode.set_text("Relative Mode")
                    self.button_zoom_in.enable()
                    self.button_zoom_out.enable()
                    self.button_zoommode.enable()
                self.params_updated = True
            elif e.ui_element == self.button_zoommode:
                self.decimate_zoom = not self.decimate_zoom
                self.button_zoommode.set_text(
                    "Decimate Zoom" if self.decimate_zoom else "FFT Zoom"
                )
                self.params_updated = True

    def draw_wf(self, ffts, screen):
        self.waterfall_surf.lock()
        nfft = len(ffts)
        self.waterfall_surf.scroll(0, nfft)
        for i, fft in enumerate(ffts):
            for x in range(self.W):
                self.waterfall_surf.set_at((x, nfft - i), self.colourmap[fft[x]])
        self.waterfall_surf.unlock()

        screen.blit(self.waterfall_surf, (self.X, self.WF_Y), area=(0, 0, self.W, self.WF_H))
    
    def freq_to_x(self, freq):
        if self.absmode:
            centre_freq = (self.abs_freq_low + self.abs_freq_high) // 2
        else:
            centre_freq = self.current_freq
        centre_pixel = self.bounds.w / 2
        hz_per_pixel = (self.display_bandwidth) / float(self.bounds.w)

        return centre_pixel + int((freq - centre_freq) / hz_per_pixel)

    def draw_marker(self, freq, screen, highlight=False, relative=False):
        x = self.freq_to_x(freq)
        font = pygame.font.Font(None, 24)

        text_colour = (255, 0, 0) if highlight else (0, 255, 255)
        line_colour = (255, 0, 0) if highlight else (0, 128, 0)

        label = f"{int(freq/1000)}" if not relative \
            else f"{(freq-self.current_freq)/1000:+.1f}k".replace(".0", "")

        text = font.render(label, True, text_colour)
        text_w = text.get_width()
        text_h = text.get_height()

        text_x = max(min(x-(text_w/2), self.bounds.w - text_w), 0)
        screen.blit(text, (text_x, self.Y))

        if x > 0 and x < self.bounds.w:
            pygame.draw.line(screen, line_colour, (x, self.Y + text_h), (x, self.Y + self.config.GRAPH_HEIGHT + self.WF_H))

    def fade(self):
        # this is too slow to use
        arr = pygame.surfarray.pixels3d(self.graph_surf)
        for x, col in enumerate(arr):
            for y, pix in enumerate(col):
                arr[x][y] = [pix[1]*0.3, pix[1]*0.3, pix[1]*0.3]

    def draw_graph(self, fft, screen):
        #self.fade()
        self.graph_surf.lock()

        self.graph_surf.fill((0, 0, 0))

        pixels_25k = int(25000 / self.display_bandwidth * self.bounds.w)
        left_offset = int(self.bounds.w / 2) % pixels_25k

        for i in range(left_offset, self.bounds.w, pixels_25k):
            pygame.draw.line(self.graph_surf, (64, 64, 64), (i, 0), (i, self.config.GRAPH_HEIGHT))

        for i, j in zip(range(self.W), range(1, self.W)):
            try:
                this_y = self.config.GRAPH_HEIGHT - int(fft[i] * float(self.config.GRAPH_HEIGHT) / 255.0)
                next_y = self.config.GRAPH_HEIGHT - int(fft[j] * float(self.config.GRAPH_HEIGHT) / 255.0)
            except OverflowError:
                continue
            pygame.draw.line(self.graph_surf, (0, 255, 0), (i, this_y), (j, next_y))

        self.graph_surf.unlock()

        screen.blit(
            self.graph_surf,
            (self.X, self.Y),
            area=(0, 0, self.W, self.config.GRAPH_HEIGHT)
        )

    def set_net_status(self, status):
        self.net_status = status
        self.net_status_updated = True

    def send_loop(self):
        s = self.socket
        try:
            while True:
                if self.params_updated:
                    self.params_updated = False
                    print("updated params")
                    d = struct.pack(
                        '!BBHIBBxxxxxxxxxxxxxx', # 24 bytes
                        0x00, # version
                        0x00, # message (parameters)
                        self.bounds.w,
                        self.rel_bandwidth,
                        self.absmode,
                        self.decimate_zoom
                    )
                    s.sendall(d)
                    d = struct.pack(
                        '!BBHxxxxxxxxxxxxxxxxxxxx', # 24 bytes
                        0x00, # version
                        0x01, # message (switch to UDP) todo: make configurable
                        45362
                    )
                    s.sendall(d)
        except OSError as e:
            self.connected = False
            self.set_net_status(str(e))

    @crash_handler.monitor_thread
    def backend_loop(self):
        while True:
            if not self.in_background:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.connect((self.config.HOST, self.config.PORT))
                        self.set_net_status('Connected')
                        self.connected = True
                        self.params_updated = True
                        self.socket = s

                        self.send_thread = threading.Thread(target=self.send_loop, daemon=True)
                        self.send_thread.start()

                        while self.connected:
                            # todo: parse header
                            frame_size = self.bounds.w + 6
                            data = bytes()
                            while len(data) < frame_size:
                                rcvd = s.recv(frame_size-len(data))
                                if not rcvd:
                                    self.set_net_status('Reconnecting...')
                                    raise OSError("Disconnected")
                                data += rcvd
                            d = struct.unpack("!BBI", data[:6])
                            ver, msg, freq = d
                            if msg == 0x01:
                                self.current_freq = freq
                                self.fft_queue.put_nowait(data[6:])
                            
                            if self.in_background:
                                s.close()
                                self.set_net_status('Disconnected')
                                break

                    except OSError as e:
                        self.connected = False
                        self.set_net_status(str(e))
            time.sleep(1)
    
    @crash_handler.monitor_thread
    def udp_backend_loop(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as u:
            u.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            u.bind(('0.0.0.0', 45362))
            while True:
                #if addr == # ?
                frame_size = self.bounds.w + 6
                data = bytes()
                while len(data) < frame_size:
                    rcvd, addr = u.recvfrom(frame_size-len(data))
                    if not rcvd:
                        continue
                    data += rcvd
                d = struct.unpack("!BBI", data[:6])
                ver, msg, freq = d
                if msg == 0x01:
                    self.current_freq = freq
                    self.fft_queue.put_nowait(data[6:])
                    udp_status = "Connected (+udp)"
                    if self.net_status != udp_status:
                        self.set_net_status(udp_status)


    def update(self, dt):
        if self.net_status_updated:
            self.net_status_updated = False
            self.label_net_status.set_text(self.net_status)
        super().update(dt)

    def draw(self, screen):
        if self.absmode: # absolute frequency display
             self.display_bandwidth = self.abs_freq_high - self.abs_freq_low
        else:
             self.display_bandwidth = self.rel_bandwidth

        ffts = []
        items = self.fft_queue.qsize()
        while items:
            ffts.append(self.fft_queue.get(block=False))
            items -= 1
        if ffts:
            self.draw_wf(ffts, screen)
            self.draw_graph(ffts[-1], screen) # only need to draw graph once

        self.gui.draw_ui(screen)

        if not self.connected:
            return True

        if self.absmode:
            if self.current_freq is not None:
                self.draw_marker(self.current_freq, screen, highlight=True)
                self.draw_marker(7000000, screen)
                self.draw_marker(7100000, screen)
                self.draw_marker(7200000, screen)
                self.draw_marker(7300000, screen)
        else:
            self.draw_marker(self.current_freq, screen, highlight=True, relative=True)
            #for m in self.REL_BANDWIDTHS[self.rel_bandwidth]:
            #    self.draw_marker(config.CURRENT_FREQ + m, screen, relative=True)
            #    self.draw_marker(config.CURRENT_FREQ - m, screen, relative=True)
        return True

    def backgrounded(self):
        self.in_background = True

    def foregrounded(self):
        self.in_background = False

    
