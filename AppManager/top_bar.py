import pygame
import pygame_gui
import fonts

from config_reader import cfg

class top_bar(object):
    bounds = None
    switcher = None
    gui = None
    redraw = True

    def __init__(self, sw):
        self.bounds = (0, 0, cfg.display.display_w, cfg.display.top_bar_size)
        self.switcher = sw
        self.gui = pygame_gui.UIManager(
            (cfg.display.display_w, cfg.display.top_bar_size)
        )
        fonts.load_fonts(self.gui)
        self.gui.get_theme().load_theme(cfg.theme_file)
        self.appname_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(132, 2, cfg.display.top_bar_app_label_width, cfg.display.top_bar_size-4),
            text='switcher',
            manager=self.gui
        )

        self.back_to_switcher_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(2, 2, 128, cfg.display.top_bar_size-4),
            text='to switcher',
            manager=self.gui
        )
        self.status_icons = []

    def set_status_icons(self, icons):
        self.status_icons = icons
        self.redraw = True

    def draw_status_icons(self, screen):
        xpos = cfg.display.display_w
        ypos = cfg.display.top_bar_size

        for icon in self.status_icons:
            icon_w = icon.get_width()
            icon_h = icon.get_height()
            xpos -= (icon_w + 2)
            screen.surf.blit(icon, (xpos, ypos - icon_h - 2))

    def updateAppLabel(self, appname):
        self.appname_label.set_text(appname)

    def update(self, dt):
        self.gui.update(dt)

    def draw(self, screen):
        if self.redraw:
            pygame.draw.rect(screen.surf, (64, 64, 64), self.bounds)
            self.gui.draw_ui(screen.surf)
            self.draw_status_icons(screen)
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
