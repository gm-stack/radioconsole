import pygame
import pygame_gui
from config_reader import cfg
from .top_bar import top_bar

class appSwitcher(object):
    FRONTMOST_APP = 'switcher'
    gui = None
    top_bar = None
    running_apps = {}
    running_apps_buttons = {}
    screen = None
    logo = None
    logo_size = None
    redraw = False
    status_icons_collection = []

    def __init__(self, screen):
        self.gui = pygame_gui.UIManager(cfg.display.size, cfg.theme_file)
        self.top_bar = top_bar(self)
        self.screen = screen
        self.logo = pygame.image.load("logo.png")
        self.logo_size = self.logo.get_size()
        self.switchFrontmostApp('switcher', False)

    def process_events(self, e):
        self.top_bar.process_events(e)
        if self.FRONTMOST_APP == 'switcher':
            self.gui.process_events(e)
            if e.type == pygame.USEREVENT:
                self.redraw = True
                if e.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if e.ui_element in self.running_apps_buttons.values():
                        self.switchFrontmostApp(e.ui_element.text)
        else:
            self.running_apps[self.FRONTMOST_APP].process_events(e)

    def draw(self, screen):
        tbdraw = self.top_bar.draw(screen)
        if self.FRONTMOST_APP == 'switcher':
            if self.redraw:
                self.gui.draw_ui(screen)
                self.redraw = False
                return True
            return False or tbdraw
        else:
            # TODO: return dirty rects?
            return self.running_apps[self.FRONTMOST_APP].draw(screen) or tbdraw

    def collect_status_icons(self):
        if any([app.status_icons_updated for app in self.running_apps.values()]):
            # any app has status_icons_updated true
            # this could probably be optimised better (i.e. only grab what's changed)
            # but it's a pretty minor optimisation
            self.status_icons_collection = []
            for app in self.running_apps.values():
                for status_icon in app.get_status_icons():
                    self.status_icons_collection.append(status_icon)
            return True
        return False

    def update(self, dt):
        if self.collect_status_icons():
            self.top_bar.set_status_icons(self.status_icons_collection)
        self.top_bar.update(dt)
        if self.FRONTMOST_APP == 'switcher':
            self.gui.update(dt)
        else:
            self.running_apps[self.FRONTMOST_APP].update(dt)

    def createAppButton(self, appname):
        total_padding = (cfg.switcher.BUTTONS_X + 1) * cfg.switcher.BUTTON_MARGIN
        button_w = (cfg.display.DISPLAY_W - total_padding) // cfg.switcher.BUTTONS_X
        button_num = len(self.running_apps_buttons)
        button_col = button_num % cfg.switcher.BUTTONS_X
        button_row = button_num // cfg.switcher.BUTTONS_X

        self.running_apps_buttons[appname] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                cfg.switcher.BUTTON_MARGIN + ((button_w + cfg.switcher.BUTTON_MARGIN) * button_col),
                cfg.display.TOP_BAR_SIZE+4 + cfg.switcher.BUTTON_MARGIN + \
                    ((cfg.switcher.BUTTON_H + cfg.switcher.BUTTON_MARGIN) * button_row),
                button_w,
                cfg.switcher.BUTTON_H
            ),
            text=appname,
            manager=self.gui
        )

    def app_launched(self, appname, app):
        self.running_apps[appname] = app
        self.createAppButton(appname)

    def switchFrontmostApp(self, appname, redraw=True):
        print(f"switching to {appname}")
        if self.FRONTMOST_APP != 'switcher':
            self.running_apps[self.FRONTMOST_APP].backgrounded()
        self.FRONTMOST_APP = appname
        self.top_bar.updateAppLabel(appname)
        if redraw:
            self.screen.fill((0, 0, 0))
            if appname == 'switcher':
                self.redraw = True
                self.screen.blit(
                    self.logo,
                    (cfg.display.DISPLAY_W - self.logo_size[0],
                    cfg.display.DISPLAY_H - self.logo_size[1])
                )
            else:
                self.running_apps[self.FRONTMOST_APP].had_event = True
            if self.FRONTMOST_APP != 'switcher':
                self.running_apps[self.FRONTMOST_APP].foregrounded()
