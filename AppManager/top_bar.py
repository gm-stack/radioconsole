import pygame
import pygame_gui
import fonts

from config_reader import cfg

class top_bar(object):
    bounds = None
    switcher = None
    gui = None
    redraw = True
    mouse_down = False
    mouse_pos = None

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
        self.status_icons = {}

    def set_status_icons(self, icons: dict):
        self.status_icons = icons
        self.redraw = True

    def draw_status_icons(self, screen, mouse=None):
        xpos = cfg.display.display_w
        ypos = cfg.display.top_bar_size

        for i, (icon, app) in enumerate(self.status_icons.items()):
            icon_w = icon.get_width()
            icon_h = icon.get_height()
            xpos -= (icon_w + 2)
            icon_rect = pygame.Rect(xpos, ypos - icon_h - 4, icon_w, icon_h)

            if self.mouse_down and icon_rect.collidepoint(self.mouse_pos):
                border = pygame.Rect(xpos - 2, ypos - icon_h - 6, icon_w + 4, icon_h + 4)
                pygame.draw.rect(screen.surf, (0, 255, 0), border)

            screen.surf.blit(icon, (xpos, ypos - icon_h - 4))
            if self.switcher.FRONTMOST_APP == app:
                underline = pygame.Rect(xpos, icon_h, icon_w, 2)
                pygame.draw.rect(screen.surf, (0, 255, 0), underline)

    def switch_if_status_icon_selected(self):
        # FIXME: less code duplication:
        xpos = cfg.display.display_w
        ypos = cfg.display.top_bar_size
        for i, (icon, app) in enumerate(self.status_icons.items()):
            icon_w = icon.get_width()
            icon_h = icon.get_height()
            xpos -= (icon_w + 2)
            icon_rect = pygame.Rect(xpos, ypos - icon_h - 4, icon_w, icon_h)

            if icon_rect.collidepoint(self.mouse_pos):
                self.switcher.switchFrontmostApp(app)
                return


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
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_down = True
            self.mouse_pos = e.pos
        if e.type == pygame.MOUSEMOTION:
            if self.mouse_down:
                self.mouse_pos = e.pos
                self.redraw = True
        if e.type == pygame.MOUSEBUTTONUP:
            self.switch_if_status_icon_selected()
            self.mouse_down = False
            self.mouse_pos = None
        if e.type == pygame.USEREVENT:
            self.redraw = True
            if e.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if e.ui_element == self.back_to_switcher_button:
                    self.switcher.switchFrontmostApp('switcher')
