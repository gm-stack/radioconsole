import signal
signal.signal(signal.SIGHUP, lambda s, f: None)
# pylint: disable=wrong-import-position

import sys

import pygame
import pygame.freetype

from config_reader import cfg

import crash_handler
import AppManager
import apps
import pygame_ft5406
import splash_screen
import display_rotation

ts = pygame_ft5406.ft5406Events()

pygame.display.init()
ts.start()
pygame.freetype.init()
pygame.font.init()

screen = display_rotation.RotationAdaptor(cfg.display.size, cfg.display.rotate)

display = pygame.display.set_mode(screen.get_display_size())
screen.set_display(display)


splash = splash_screen.splash_screen(screen)
splash.draw_splash()

def safe_exit():
    pygame.quit()
    ts.stop()
    sys.exit()

crash_handler.register(screen, safe_exit)

try:
    sw = AppManager.appSwitcher(screen)
    am = AppManager.appManager(sw)

    splash.update_status("register apps")
    am.register_app('rtl_fft', apps.WaterfallDisplay)
    am.register_app('gpsd', apps.gps_status)
    am.register_app('lte_status', apps.lte_status)
    am.register_app('log_viewer', apps.LogViewer)
    am.register_app('raspi_status', apps.RaspiStatus)
    am.register_app('systemd_status', apps.SystemDStatus)
    am.register_app('docker_status', apps.DockerStatus)
    am.register_app('systemd_log_viewer', apps.SystemDLogViewer)
    am.register_app('docker_log_viewer', apps.DockerLogViewer)
    am.register_app('gpio_shutdown_status', apps.GPIOShutdown)
    am.register_app('ardop_status', apps.ARDOPStatus)
    am.register_app('direwolf_status', apps.DirewolfStatus)
    am.register_app('usb_status', apps.USBStatus)

    splash.update_status("instantiating apps")
    if len(sys.argv) > 1:
        am.instantiate_apps(splash.update_status, only=sys.argv[1])
        sw.switchFrontmostApp(sys.argv[1])
    else:
        am.instantiate_apps(splash.update_status)
        sw.switchFrontmostApp('switcher')

    clock = pygame.time.Clock()
    while True:
        time_delta = clock.tick(cfg.display.target_fps)/1000.0
        for e in pygame.event.get():
            if e.type is pygame.QUIT:
                safe_exit()
            sw.process_events(e)
        sw.update(time_delta)
        if sw.draw(screen):
            screen.update()

# pylint: disable=broad-except
except Exception as e:
    crash_handler.crash(e)
