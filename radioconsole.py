import sys

import pygame

from config_reader import cfg
import AppManager
import apps

if __name__ == '__main__':
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((cfg.display.DISPLAY_W, cfg.display.DISPLAY_H))

    sw = AppManager.appSwitcher(screen)
    am = AppManager.appManager(sw)

    am.register_app('rtl_fft', apps.WaterfallDisplay)
    am.register_app('gpsd', apps.gps_status)
    am.register_app('lte_status', apps.lte_status)

    am.instantiate_apps()
    if len(sys.argv) > 1:
        sw.switchFrontmostApp(sys.argv[1])

    clock = pygame.time.Clock()
    while True:
        time_delta = clock.tick(cfg.display.TARGET_FPS)/1000.0
        for e in pygame.event.get():
            if e.type is pygame.QUIT:
                pygame.quit()
                sys.exit()
            sw.process_events(e)

        sw.update(time_delta)

        sw.draw(screen)
        pygame.display.update()
