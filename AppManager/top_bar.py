import pygame
import pygame_gui

from config_reader import cfg

class top_bar(object):
    bounds = None
    switcher = None
    gui = None
    redraw = True

    def __init__(self, sw):
        self.bounds = (0, 0, cfg.display.DISPLAY_W, cfg.display.TOP_BAR_SIZE)
        self.switcher = sw
        self.gui = pygame_gui.UIManager(
            (cfg.display.DISPLAY_W, cfg.display.TOP_BAR_SIZE),
            cfg.theme_file
        )
        self.appname_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(132, 2, cfg.display.TOP_BAR_APP_LABEL_WIDTH, cfg.display.TOP_BAR_SIZE-4),
            text='switcher',
            manager=self.gui
        )

        self.back_to_switcher_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(2, 2, 128, cfg.display.TOP_BAR_SIZE-4),
            text='to switcher',
            manager=self.gui
        )

    def updateAppLabel(self, appname):
        self.appname_label.set_text(appname)
        #redraw = True

    def update(self, dt):
        self.gui.update(dt)

    def draw(self, screen):
        if self.redraw:
            pygame.draw.rect(screen, (64, 64, 64), self.bounds)
            self.gui.draw_ui(screen)
            self.redraw = False
            return True
        return False

    def process_events(self, e):
        self.gui.process_events(e)
        if e.type == pygame.USEREVENT:
            self.redraw = True
            if e.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if e.ui_element == self.back_to_switcher_button:
                    self.switcher.switchFrontmostApp('switcher')
