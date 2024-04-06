import threading
import time

import requests
import pygame
from pygame import surface
import pygame_gui

import crash_handler
from config_reader import cfg
from AppManager.app import app
from .backends import backends
from util import timegraph, stat_label, stat_display, stat_view, stat_view_graph, extract_number
from .status_icon import lte_status_icon
from ..LogViewer import TerminalView

class lte_status(app):
    backend = None
    backend_thread = None
    ui_element_labels = {}
    ui_element_values = {}
    ui_element_graphs = {}
    band_labels = {}
    band_values = [{}, {}]

    def __init__(self, bounds, config, display, name):
        super().__init__(bounds, config, display, name)
        self.backend = backends[config.backend](config)
        self.data = {}

        self.status_icon = lte_status_icon()
        self.status_icons = [self.status_icon.surface]

        self.backend_thread = threading.Thread(target=self.backend_loop, daemon=True)
        self.backend_thread.start()

        y = display.TOP_BAR_SIZE

        self.button_reboot = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(display.DISPLAY_W - 256, y, 256, 64),
            text="Reboot Modem",
            manager=self.gui
        )

        for ui_element in ['mode', 'modem', 'lac']:
            self.ui_element_values[ui_element] = stat_view(
                relative_rect=pygame.Rect(0, y, 512, 32),
                label_s=128,
                name=ui_element,
                manager=self.gui
            )
            y += config.line_height

        y += config.line_height / 2

        stat_label(
            relative_rect=pygame.Rect(128, y, 128, 32),
            text='CA 0',
            manager=self.gui
        )
        stat_label(
            relative_rect=pygame.Rect(256, y, 128, 32),
            text='CA 1',
            manager=self.gui
        )

        self.terminal_view = TerminalView(
            bounds.w - 389, (bounds.h + bounds.y) - y, 389, y, "lte_config"
        )

        y += config.line_height

        for ui_element in ['band_name', 'freq', 'bandwidth']:
            self.band_labels[ui_element] = stat_label(
                relative_rect=pygame.Rect(0, y, 128, 32),
                text=ui_element,
                manager=self.gui
            )
            self.band_values[0][ui_element] = stat_display(
                relative_rect=pygame.Rect(128, y, 128, 32),
                text='',
                manager=self.gui
            )
            self.band_values[1][ui_element] = stat_display(
                relative_rect=pygame.Rect(256, y, 128, 32),
                text='',
                manager=self.gui
            )
            y += config.line_height

        y += config.line_height / 2

        for ui_element, kwargs in {
            'rsrq': {
                'unit': ' dB',
                'colourmap': {
                    -10: (0, 255, 0, 255),
                    -15: (255, 255, 0, 255),
                    -20: (255, 165, 0, 255),
                    None: (255, 0, 0, 255)
                }
            },
            'rsrp': {
                'unit': ' dBm',
                'colourmap': {
                    -80: (0, 255, 0, 255),
                    -90: (255, 255, 0, 255),
                    -100: (255, 165, 0, 255),
                    None: (255, 0, 0, 255)
                }
            },
            'rssi': {
                'unit': ' dBm',
                'colourmap': {
                    -65: (0, 255, 0, 255),
                    -75: (255, 255, 0, 255),
                    -85: (255, 165, 0, 255),
                    None: (255, 0, 0, 255)
                }
            },
            'temp': {
                'unit': "\N{DEGREE SIGN}C",
                'colourmap': {
                    70: (255, 165, 0, 255),
                    80: (255, 0, 0, 255),
                    None: (0, 255, 0, 255)
                }
            },
            'netmode': {'unit': ''}
        }.items():
            self.ui_element_graphs[ui_element] = stat_view_graph(
                relative_rect=pygame.Rect(0, y, 384, 32),
                text_w=256,
                name=ui_element,
                manager=self.gui,
                colourmap_mode='gt',
                **kwargs
            )
            y += config.line_height

    @crash_handler.monitor_thread
    def backend_loop(self):
        while True:
            try:
                self.data = self.backend.fetch_stats()
            except requests.exceptions.RequestException as e:
                try:
                    errargs = e.args[0].reason.args
                    err = errargs[0] if type(errargs[0]) is str else errargs[1]
                    self.data = {'mode': err.split(':')[-1]}
                except:
                    self.data = {'mode': str(e)}
            self.data_updated = True
            self.status_icon.update(self.data)
            self.status_icons_updated = True
            time.sleep(1.0)

    prev_mode = None
    prev_bands = []
    prev_lac = None

    def update(self, dt):
        if self.data_updated:
            for key in ['mode', 'modem', 'lac']:
                self.ui_element_values[key].set_text(self.data.get(key, ''))

            for key in ['rsrq', 'rsrp', 'rssi', 'temp']:
                value = extract_number(self.data.get(key))
                self.ui_element_graphs[key].update(value)

            if 'bands' in self.data:
                for key, gui in self.band_values[0].items():
                    gui.set_text(self.data['bands'][0][key])

                if len(self.data['bands']) == 2:
                    for key, gui in self.band_values[1].items():
                        gui.set_text(self.data['bands'][1][key])
                else:
                    for key, gui in self.band_values[1].items():
                        gui.set_text('')
            
                if self.data['mode'] != self.prev_mode or self.data['bands'] != self.prev_bands:
                    self.prev_bands = self.data['bands']
                    self.prev_mode = self.data.get("mode")
                    self.log_bands()
                
                if self.data.get("lac") != self.prev_lac:
                    self.prev_lac = self.data.get("lac")
                    self.log_lac()

                    
        super().update(dt)

    
    def log_bands(self):
        band_names = ",".join([ f"{band['band']}@{band['freq']}/{band['bandwidth']}" for band in self.data['bands'] ])
        self.log_msg(f"Using {self.data.get('mode')} at {band_names}")

    def log_lac(self):
        self.log_msg(f"Now connected to LAC {self.data.get('lac')}")

    def log_msg(self, msg):
        timestamp = time.strftime('%H:%M:%S')
        self.terminal_view.write(f"{timestamp}: {msg}\n")
    
    def draw(self, screen):
        if super().draw(screen):
            self.terminal_view.draw(screen)
            for graph in self.ui_element_graphs.values():
                graph.draw(screen)
            return True
        return False

    def process_events(self, e):
        super().process_events(e)
        if e.type == pygame.USEREVENT and e.user_type == pygame_gui.UI_BUTTON_PRESSED:
            self.backend.reboot_modem()
            self.log_msg("Rebooting modem...")