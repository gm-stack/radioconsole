import threading
import time

import pygame
import pygame_gui

import crash_handler
from config_reader import cfg
from AppManager.app import app
from .backends import backends

class lte_status(app):
    backend = None
    gui = None
    backend_thread = None
    data = None
    data_updated = False
    ui_element_labels = {}
    ui_element_values = {}
    band_labels = {}
    band_values = [{}, {}]

    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)
        self.backend = backends[config.backend](config)
        self.gui = pygame_gui.UIManager(cfg.display.size, cfg.theme_file)

        self.backend_thread = threading.Thread(target=self.backend_loop, daemon=True)
        self.backend_thread.start()

        y = display.TOP_BAR_SIZE

        def create_ui_elements(l):
            nonlocal y
            for ui_element in l:
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

        create_ui_elements(['mode', 'modem', 'lac'])

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

        create_ui_elements(['ecio', 'rscp', 'per', 'temp', 'down'])

    @crash_handler.monitor_thread
    def backend_loop(self):
        while True:
            self.data = self.backend.fetch_stats()
            self.data_updated = True
            time.sleep(1.0)

    def draw(self, screen):
        self.gui.draw_ui(screen)

    def update(self, dt):
        if self.data_updated:
            for key, gui in self.ui_element_values.items():
                gui.set_text(self.data.get(key, ''))

            for key, gui in self.band_values[0].items():
                gui.set_text(self.data['bands'][0][key])
            if len(self.data['bands']) == 2:
                for key, gui in self.band_values[1].items():
                    gui.set_text(self.data['bands'][1][key])
            else:
                for key, gui in self.band_values[1].items():
                    gui.set_text('')

            self.data_updated = False

        self.gui.update(dt)

    def process_events(self, e):
        self.gui.process_events(e)
