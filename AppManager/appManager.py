from types import SimpleNamespace

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

    def instantiate_apps(self, status_cb, only=None):
        if only:
            modules = {
                m:c for m,c in cfg.modules.items()
                if c.display_name == only
            }
            if len(modules) == 0:
                print(f"Error: No module '{only}' found, modules defined in config are: ")
                print("\n".join([f"- {c.display_name}" for m,c in cfg.modules.items()]))
                exit()
            cfg.modules = modules
        for appname, appcfg in cfg.modules.items():
            if appcfg.type not in self.available_apps:
                raise NotImplementedError(
                    f"Error starting app {appname}: {appcfg.type} not a recognised app"
                )
            status_cb(f"init {appname}")

            app_class = self.available_apps[appcfg.type]

            instance_config = app_class.default_config.copy()
            instance_config.update(appcfg.config)

            app = app_class(
                bounds=pygame.Rect(
                    0,
                    cfg.display.top_bar_size,
                    cfg.display.display_w,
                    cfg.display.display_h - cfg.display.top_bar_size
                ),
                config=SimpleNamespace(**instance_config),
                name=appname
            )
            self.switcher.app_launched(appname, app)
