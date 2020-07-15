import pygame
import pygame_gui

from config_reader import cfg

class app(object):
    config = None
    bounds = None
    display = None

    def __init__(self, bounds, config, display):
        self.config = config
        self.bounds = bounds
        self.display = display
        self.gui = pygame_gui.UIManager(cfg.display.size, cfg.theme_file)
        self.had_event = True
        self.data_updated = True
        self._had_update = True

    def update(self, dt):
        self._had_update = self.data_updated
        # avoids a race condition if another update arrives between now and draw()
        # and a subclass's update() method looks at data_updated to see if it should run
        self.data_updated = False
        self.gui.update(dt)
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
