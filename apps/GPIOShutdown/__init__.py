import re
import math

import pygame
import pygame_gui

from ..common import time_format
from ..common.LogViewerStatusApp import LogViewerStatusApp
from util import stat_display
from .status_icon import gpio_shutdown_status_icon

class GPIOShutdown(LogViewerStatusApp):

    default_config = {
        "port": 22,
        "username": "pi",
        "retry_seconds": 5,
        "max_scrollback": 50000,
        "command_button_h": 48,
        "command_buttons_x": 0,
        "command_button_margin": 2,
        "filter_lines": [],
        "commands": [],
        "show_service_name": None,
        "shutdown_time": 300
    }

    def __init__(self, bounds, config, name):
        self.GPIOShutdownConfig = config

        terminal_bounds = pygame.Rect(bounds)
        terminal_bounds.top += 200
        terminal_bounds.height -= 200

        self.services = ['gpio_shutdown']

        self.shutdown_timer_running = False
        self.shutdown_timer = -1.0

        def pin_low(msg, match):
            self.shutdown_timer = float(self.GPIOShutdownConfig.shutdown_time)
            self.update_shutdown_timer("pwr on", (0xFF,0xFF,0xFF))
            self.shutdown_timer_running = False
            self.countdown.set_text_colour((0xCC,0xCC,0xCC))
            self.countdown_label.set_text_colour((0xCC,0xCC,0xCC))
            self.countdown_label.set_text("gpio_shutdown running, power keyed")
            self.data_updated = True

        def pin_high(msg, match):
            self.shutdown_timer = float(self.GPIOShutdownConfig.shutdown_time)
            self.update_shutdown_timer("pwr off", (0xFF,0xA5,0x00))
            self.shutdown_timer_running = True
            self.countdown.set_text_colour((0xCC,0x84,0x00))
            self.countdown_label.set_text_colour((0xCC,0x84,0x00))
            self.countdown_label.set_text("power unkeyed, will shut down")
            self.data_updated = True

        def pin_still_high(msg, match):
            self.shutdown_timer = float(match.group(1))
            self.update_shutdown_timer("pwr off", (0xFF,0xA5,0x00))
            self.shutdown_timer_running = True
            self.countdown.set_text_colour((0xCC,0x84,0x00))
            self.countdown_label.set_text_colour((0xCC,0x84,0x00))
            self.countdown_label.set_text("power unkeyed, will shut down")
            self.data_updated = True

        def radioconsole_stopped(msg, match):
            self.shutdown_timer = -1.0
            self.shutdown_timer_running = False
            self.update_shutdown_timer("stopped", (0xCC,0xCC,0xCC))
            self.countdown.set_text("--:--.---")
            self.countdown_label.set_text("gpio_shutdown not running")
            self.countdown.set_text_colour((0x66,0x66,0x66))
            self.countdown_label.set_text_colour((0x66,0x66,0x66))
            self.data_updated = True

        def radioconsole_started(msg, match):
            self.shutdown_timer = float(self.GPIOShutdownConfig.shutdown_time)
            self.update_shutdown_timer("pwr on", (0xFF,0xFF,0xFF))
            self.shutdown_timer_running = False
            self.countdown.set_text_colour((0xCC,0xCC,0xCC))
            self.countdown_label.set_text_colour((0xCC,0xCC,0xCC))
            self.countdown_label.set_text("gpio_shutdown running, power keyed")
            self.data_updated = True

        self.process_messages = [
            {"r": r'pin \d* state is now low', 'func': pin_low},
            {"r": r'pin \d* state is now high', 'func': pin_high},
            {"r": r'pin \d* still high, shutdown in (\d*)s', 'func': pin_still_high},
            {"r": r'Stopped Radioconsole gpio_shutdown', 'func': radioconsole_stopped},
            {"r": r'Started Radioconsole gpio_shutdown.', 'func': radioconsole_started},

        ]

        super().__init__(terminal_bounds, config, "GPIOLogViewer")

        stat_loc = pygame.Rect((0,0),(bounds.w,125))
        stat_loc.midtop = (bounds.w/2,bounds.y)

        self.countdown = stat_display(
                    object_id="#countdown",
                    relative_rect=stat_loc,
                    manager=self.gui,
                    text='--:--.---'
        )
        stat_loc.midtop = (400,bounds.y+125)
        stat_loc.height = 50
        self.countdown_label = stat_display(
                    object_id="#countdown_label",
                    relative_rect=stat_loc,
                    manager=self.gui,
                    text='gpio_shutdown status unknown'
        )

        self.status_icon = gpio_shutdown_status_icon()
        self.status_icons = [self.status_icon.surface]
        self.status_icon.update(None, self.shutdown_timer, ((0xCC,0xCC,0xCC)), "?")
        self.status_icons_updated = True
        self.data_updated = True

    def update_shutdown_timer(self, status, colour):
        self.countdown.set_text(time_format.mm_ss_fff(self.shutdown_timer))
        self.countdown.set_text_colour(colour)
        self.countdown_label.set_text_colour(colour)
        self.status_icon.update(None, self.shutdown_timer, colour, status)

    def update(self, dt):
        if self.shutdown_timer_running:
            self.shutdown_timer -= dt
            if self.shutdown_timer <= 0.0:
                self.shutdown_timer = 0.0
                self.shutdown_timer_running = False
            colour=(0xFF,0xC5,0x00)
            if self.shutdown_timer < 30.0:
                colour = (0xFF,0x00,0x00)
            self.update_shutdown_timer("pwr off", colour)
            self.data_updated = True
        return super().update(dt)