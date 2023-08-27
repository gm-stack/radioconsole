import pygame

from config_reader import cfg

class appManager(object):
    available_apps = {}
    switcher = None
    def __init__(self, sw):
        self.switcher = sw

    def register_app(self, name, appclass):
        print(f"Registered {name}: {appclass}")
        self.available_apps[name] = appclass

    def instantiate_apps(self, status_cb):
        for appname, appcfg in cfg.modules.items():
            if appcfg.type not in self.available_apps:
                raise NotImplementedError(
                    f"Error starting app {appname}: {appcfg.type} not a recognised app"
                )
            status_cb(f"init {appname}")
            app = self.available_apps[appcfg.type](
                bounds=pygame.Rect(
                    0,
                    cfg.display.TOP_BAR_SIZE,
                    cfg.display.DISPLAY_W,
                    cfg.display.DISPLAY_H - cfg.display.TOP_BAR_SIZE
                ),
                config=appcfg.config,
                display=cfg.display
            )
            self.switcher.app_launched(appname, app)
