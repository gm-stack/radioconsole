import threading
import time

import pygame
import pygame_gui

import crash_handler
from config_reader import cfg
from AppManager.app import app
from .backends import backends
from util import timegraph

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
            self.ui_element_labels[ui_element] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(0, y, 128, 32),
                text=ui_element,
                manager=self.gui,
                object_id="#param_label"
            )
            self.ui_element_values[ui_element] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(128, y, 384, 32),
                text='',
                manager=self.gui,
                object_id="#param_value"
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

        for ui_element in ['rsrq', 'rsrp', 'rssi', 'temp', 'netmode']:
            self.ui_element_labels[ui_element] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(0, y, 128, 32),
                text=ui_element,
                manager=self.gui,
                object_id="#param_label"
            )
            self.ui_element_values[ui_element] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(128, y, 128, 32),
                text='',
                manager=self.gui,
                object_id="#param_value"
            )
            self.ui_element_graphs[ui_element] = timegraph(
                pygame.Rect(256, y, 544, 32)
            )
            
            y += config.line_height


    @crash_handler.monitor_thread
    def backend_loop(self):
        while True:
            self.data = self.backend.fetch_stats()
            self.data_updated = True
            time.sleep(1.0)

    def rsrq_to_colour(self, rsrq):
        if rsrq > -10:
            return (0, 255, 0, 255)
        elif rsrq > -15:
            return (255, 255, 0, 255)
        elif rsrq > -20:
            return (255, 165, 0, 255)
        return (255, 0, 0, 255)
    
    def rsrp_to_colour(self, rsrp):
        if rsrp > -80:
            return (0, 255, 0, 255)
        elif rsrp > -90:
            return (255, 255, 0, 255)
        elif rsrp > -100:
            return (255, 165, 0, 255)
        return (255, 0, 0, 255)
    
    def rssi_to_colour(self, rssi):
        if rssi > -65:
            return (0, 255, 0, 255)
        elif rssi > -75:
            return (255, 255, 0, 255)
        elif rssi > -85:
            return (255, 165, 0, 255)
        return (255, 0, 0, 255)
    
    def temp_to_colour(self, temp):
        if temp > 70:
            return (255, 165, 0, 255)
        if temp > 80:
            return (255, 0, 0, 255)
        return (0, 255, 0, 255)

    def update(self, dt):
        if self.data_updated:
            for key in ['mode', 'modem', 'lac', 'netmode']:
                self.ui_element_values[key].set_text(self.data.get(key, ''))
            

            colourfuncs = {
                'rsrq': self.rsrq_to_colour,
                'rsrp': self.rsrp_to_colour,
                'rssi': self.rssi_to_colour,
                'temp': self.temp_to_colour
            }
            for key in ['rsrq', 'rsrp', 'rssi', 'temp']:
                unit = "\N{DEGREE SIGN}C" if key == 'temp' else " dB" if key == 'rsrq' else " dBm"
                value = self.data.get(key)
                if value:
                    try:
                        value = float(value)
                        self.ui_element_values[key].set_text(f"{value:.1f}{unit}")
                        self.ui_element_graphs[key].datapoint(value)
                        if key in colourfuncs:
                            colour = colourfuncs[key](value)
                            if self.ui_element_values[key].text_colour != colour:
                                self.ui_element_values[key].text_colour = colour
                                self.ui_element_values[key].rebuild()
                    except ValueError:
                        self.ui_element_values[key].set_text("")
                else:
                    self.ui_element_values[key].set_text("")
                    #self.ui_element_graphs[key].datapoint(None)
            

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