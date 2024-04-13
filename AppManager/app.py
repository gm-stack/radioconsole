import time

import pygame
import pygame_gui
import fonts

from config_reader import cfg

class app(object):
    default_config = {}
    config = None
    bounds = None

    def __init__(self, bounds, config, name):
        self.config = config
        self.bounds = bounds
        self.name = name

        self.gui = pygame_gui.UIManager(cfg.display.size, cfg.theme_file)
        fonts.load_fonts(self.gui)

        self.had_event = True
        self.data_updated = True
        self._had_update = True

        self.status_icons_updated = True
        self.status_icons = []

        self.last_known_good_data = {}
        self.last_known_good_seconds = {}
        self.no_data_allowed_time = {}

        self.one_second_tick_time = 0.0

    def data_good(self, data_for='', no_data_allowed_time=10.0):
        self.last_known_good_data[data_for] = time.monotonic()
        self.no_data_allowed_time[data_for] = no_data_allowed_time

    def check_last_good_data(self, dt):
        for last_data_type, last_data in self.last_known_good_data.items():
            last_data_good_seconds = time.monotonic() - last_data

            if last_data_good_seconds > self.no_data_allowed_time[last_data_type]:
                self.last_known_good_seconds[last_data_type] += dt
            else:
                self.last_known_good_seconds[last_data_type] = 0

            if self.last_known_good_seconds[last_data_type] >= 1.0:
                self.last_known_good_seconds[last_data_type] -= 1.0
                self.no_data_update_for(last_data_type, int(round(last_data_good_seconds)))

    def no_data_update_for(self, data_type, sec_since):
        print(f"{self.name}: no data recvd for \"{data_type}\" for {sec_since}s, and no handler in app for this")

    def one_second_tick(self, dt):
        pass

    def update(self, dt):
        self.one_second_tick_time += dt
        if self.one_second_tick_time >= 1.0:
            self.one_second_tick(self.one_second_tick_time)
            self.one_second_tick_time -= 1.0
        self._had_update = self.data_updated
        # avoids a race condition if another update arrives between now and draw()
        # and a subclass's update() method looks at data_updated to see if it should run
        self.data_updated = False
        self.gui.update(dt)
        if self.last_known_good_data:
            self.check_last_good_data(dt)
        return self._had_update

    def process_events(self, e):
        if e.type != pygame.MOUSEMOTION:
            self.had_event = True
        self.gui.process_events(e)

    def draw(self, screen):
        if self.had_event or self._had_update:
            self.had_event = False
            self._had_update = False
            self.gui.draw_ui(screen)
            return True
        return False

    def get_status_icons(self):
        self.status_icons_updated = False
        return self.status_icons

    def foregrounded(self):
        pass

    def backgrounded(self):
        pass