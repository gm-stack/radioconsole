import os
import pygame
import pygame_gui
import fonts
from config_reader import cfg
from .top_bar import top_bar

base_path = os.path.dirname(__file__)

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
    status_icons_collection = {}

    def __init__(self, screen):
        self.gui = pygame_gui.UIManager(cfg.display.size)
        fonts.load_fonts(self.gui)
        print("fonts loaded, loading theme")
        self.gui.get_theme().load_theme(cfg.theme_file)
        self.top_bar = top_bar(self)
        self.screen = screen
        self.logo = pygame.image.load(os.path.join(base_path, "../logo.png"))
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
                self.gui.draw_ui(screen.surf)
                self.redraw = False
                return True
            return False or tbdraw
        else:
            # TODO: return dirty rects?
            return self.running_apps[self.FRONTMOST_APP].draw(screen.surf) or tbdraw

    def collect_status_icons(self):
        if any([app.status_icons_updated for app in self.running_apps.values()]):
            # any app has status_icons_updated true
            # this could probably be optimised better (i.e. only grab what's changed)
            # but it's a pretty minor optimisation
            self.status_icons_collection = {}
            for app in self.running_apps.values():
                for status_icon in app.get_status_icons():
                    self.status_icons_collection[status_icon] = app.name
            return True
        return False

    def update(self, dt):
        if self.collect_status_icons():
            self.top_bar.set_status_icons(self.status_icons_collection)
        self.top_bar.update(dt)
        if self.FRONTMOST_APP == 'switcher':
            self.gui.update(dt)
        for app_name, app in self.running_apps.items():
            app.update(dt)

    def createAppButton(self, appname):
        total_padding = (cfg.switcher.buttons_x + 1) * cfg.switcher.button_margin
        button_w = (cfg.display.display_w - total_padding) // cfg.switcher.buttons_x
        button_num = len(self.running_apps_buttons)
        button_col = button_num % cfg.switcher.buttons_x
        button_row = button_num // cfg.switcher.buttons_x

        self.running_apps_buttons[appname] = pygame_gui.elements.UIButton(
            object_id="#launcher_button",
            relative_rect=pygame.Rect(
                cfg.switcher.button_margin + ((button_w + cfg.switcher.button_margin) * button_col),
                cfg.display.top_bar_size+4 + cfg.switcher.button_margin + \
                    ((cfg.switcher.button_h + cfg.switcher.button_margin) * button_row),
                button_w,
                cfg.switcher.button_h
            ),
            text=appname,
            manager=self.gui
        )

    def app_launched(self, appname, app):
        self.running_apps[appname] = app
        self.createAppButton(appname)

    def switchFrontmostApp(self, appname, redraw=True):
        if self.FRONTMOST_APP != 'switcher':
            self.running_apps[self.FRONTMOST_APP].backgrounded()
        self.FRONTMOST_APP = appname
        self.top_bar.updateAppLabel(appname)
        if redraw:
            self.screen.surf.fill((0, 0, 0))
            if appname == 'switcher':
                self.redraw = True
                self.screen.surf.blit(
                    self.logo,
                    (cfg.display.display_w - self.logo_size[0],
                    cfg.display.display_h - self.logo_size[1])
                )
            else:
                self.running_apps[self.FRONTMOST_APP].had_event = True
            if self.FRONTMOST_APP != 'switcher':
                self.running_apps[self.FRONTMOST_APP].foregrounded()
