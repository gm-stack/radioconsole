import signal
signal.signal(signal.SIGHUP, lambda s, f: None)
# pylint: disable=wrong-import-position

import sys

import pygame

from config_reader import cfg

import crash_handler
import AppManager
import apps
import pygame_ft5406

ts = pygame_ft5406.ft5406Events()

pygame.display.init()
ts.start()
pygame.font.init()
screen = pygame.display.set_mode(cfg.display.size)

def safe_exit():
    pygame.quit()
    ts.stop()
    sys.exit()

crash_handler.register(screen, safe_exit)

try:
    sw = AppManager.appSwitcher(screen)
    am = AppManager.appManager(sw)

    am.register_app('rtl_fft', apps.WaterfallDisplay)
    am.register_app('gpsd', apps.gps_status)
    am.register_app('lte_status', apps.lte_status)
    am.register_app('log_viewer', apps.LogViewer)
    am.register_app('raspi_status', apps.RaspiStatus)

    am.instantiate_apps()
    if len(sys.argv) > 1:
        sw.switchFrontmostApp(sys.argv[1])

    clock = pygame.time.Clock()
    while True:
        time_delta = clock.tick(cfg.display.TARGET_FPS)/1000.0
        for e in pygame.event.get():
            if e.type is pygame.QUIT:
                safe_exit()
            sw.process_events(e)
        sw.update(time_delta)
        sw.draw(screen)
        pygame.display.update()

# pylint: disable=broad-except
except Exception as e:
    crash_handler.crash(e)
