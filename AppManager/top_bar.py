import pygame
import pygame_gui

from config_reader import cfg

class top_bar(object):
    bounds = None
    switcher = None
    gui = None
    def __init__(self, sw):
        self.bounds = (0, 0, cfg.display.DISPLAY_W, cfg.display.TOP_BAR_SIZE)
        self.switcher = sw
        self.gui = pygame_gui.UIManager((cfg.display.DISPLAY_W, cfg.display.TOP_BAR_SIZE))
        self.appname_label = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(2, 2, 128, cfg.display.TOP_BAR_SIZE-4),
            text='switcher',
            manager=self.gui
        )

    def updateAppLabel(self, appname):
        self.appname_label.set_text(appname)

    def update(self, dt):
        self.gui.update(dt)

    def draw(self, screen):
        pygame.draw.rect(screen, (64, 64, 64), self.bounds)
        self.gui.draw_ui(screen)

    def process_events(self, e):
        self.gui.process_events(e)
        if e.type == pygame.USEREVENT and e.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if e.ui_element == self.appname_label:
                self.switcher.switchFrontmostApp('switcher')
