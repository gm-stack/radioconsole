import threading
import time

import requests
import pygame
import pygame_gui

import crash_handler
from config_reader import cfg
from AppManager.app import app
from .backends import backends
from util import timegraph, stat_view, stat_view_graph, extract_number

class lte_status(app):
    backend = None
    backend_thread = None
    ui_element_labels = {}
    ui_element_values = {}
    ui_element_graphs = {}
    band_labels = {}
    band_values = [{}, {}]

    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)
        self.backend = backends[config.backend](config)
        self.data = {}

        self.backend_thread = threading.Thread(target=self.backend_loop, daemon=True)
        self.backend_thread.start()

        y = display.TOP_BAR_SIZE

        for ui_element in ['mode', 'modem', 'lac']:
            self.ui_element_values[ui_element] = stat_view(
                relative_rect=pygame.Rect(0, y, 512, 32),
                label_s=128,
                name=ui_element,
                manager=self.gui
            )
            y += config.line_height

        y += config.line_height / 2

        pygame_gui.elements.ui_label.UILabel(
            relative_rect=pygame.Rect(128, y, 128, 32),
            text='CA 0',
            manager=self.gui,
            object_id="#param_label"
        )
        pygame_gui.elements.ui_label.UILabel(
            relative_rect=pygame.Rect(256, y, 128, 32),
            text='CA 1',
            manager=self.gui,
            object_id="#param_label"
        )
        y += config.line_height

        for ui_element in ['band_name', 'freq', 'bandwidth']:
            self.band_labels[ui_element] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(0, y, 128, 32),
                text=ui_element,
                manager=self.gui,
                object_id="#param_label"
            )
            self.band_values[0][ui_element] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(128, y, 128, 32),
                text='',
                manager=self.gui,
                object_id="#param_value"
            )
            self.band_values[1][ui_element] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(256, y, 128, 32),
                text='',
                manager=self.gui,
                object_id="#param_value_none"
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
                relative_rect=pygame.Rect(0, y, 800, 32),
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
                self.data = {'mode': e.args[0].reason.args[0].split(':')[-1]}
            self.data_updated = True
            time.sleep(1.0)

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

        super().update(dt)

    def draw(self, screen):
        if super().draw(screen):
            for graph in self.ui_element_graphs.values():
                graph.draw(screen)
            return True
        return False