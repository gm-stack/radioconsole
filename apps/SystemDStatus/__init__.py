import time
import threading
import json
import types

import pygame
import pygame_gui
import paramiko

import crash_handler
from AppManager.app import app
from config_reader import cfg
from util import timegraph, stat_display, stat_label, stat_view, stat_view_graph, extract_number
from .status_icon import systemd_status_icon

from ..LogViewer import LogViewer

class SystemDStatus(LogViewer):
    service_status = {}
    ui_element_values = {}
    ui_element_start_stop_buttons = {}
    ui_element_status_buttons = {}

    data_updated = False

    def __init__(self, bounds, config, display, name):
        log_viewer_cfg = types.SimpleNamespace(
            username=config.username,
            host=config.host,
            port=config.port,
            retry_seconds=5,
            command='',
            commands=[],
            command_button_h=0,
            command_buttons_x=1,
            command_button_margin=0
        )

        super().__init__(bounds, log_viewer_cfg, display, f"{name}_logviewer")
        self.config = config

        y_off = display.TOP_BAR_SIZE
        x = 0

        self.status_icon = systemd_status_icon()
        self.status_icons = [self.status_icon.surface]
        self.status_icon.update(0,0,0,icon=None)
        self.status_icons_updated = True

        def create_ui(service):
            nonlocal y_off
            nonlocal x

            y = y_off

            self.ui_element_values[service] = {}

            self.ui_element_start_stop_buttons[pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    x + 315, y,
                    80, 32
                ),
                text="Start",
                manager=self.gui
            )] = service

            self.ui_element_values[service]['description'] = stat_label(
                relative_rect=pygame.Rect(x, y, 315, 32),
                text=service, manager=self.gui
            )

            y += 32

            self.ui_element_status_buttons[pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    x, y,
                    80, 32
                ),
                text="Status",
                manager=self.gui
            )] = service

            self.ui_element_values[service]['load'] = stat_view(
                relative_rect=pygame.Rect(x + 80, y, 90, 32),
                name='load',
                manager=self.gui,
                split='no_label',
                colourmap={
                    'loaded': (0, 255, 0, 255),
                    'masked': (0, 0, 255, 255),
                    'not-found': (255, 0, 0, 255),
                    None: (127, 127, 127, 255)
                },
                colourmap_mode='equals'
            )

            self.ui_element_values[service]['sub'] = stat_view(
                relative_rect=pygame.Rect(x + 170, y, 120, 32),
                name='sub',
                manager=self.gui,
                split='no_label',
                colourmap={
                    'auto-restart': (255, 165, 0, 255),
                    'exited': (255, 165, 0, 255),
                    'failed': (255, 0, 0, 255),
                    'running': (0, 255, 0, 255),
                    None: (127, 127, 127, 255)
                },
                colourmap_mode='equals'
            )

            self.ui_element_values[service]['active'] = stat_view(
                relative_rect=pygame.Rect(x + 290, y, 105, 32),
                name='active',
                manager=self.gui,
                split='no_label',
                colourmap={
                    'activating': (255, 165, 0, 255),
                    'active': (0, 255, 0, 255),
                    'failed': (255, 0, 0, 255),
                    None: (127, 127, 127, 255)
                },
                colourmap_mode='equals'
            )

            if (x + 400) >= display.DISPLAY_W:
                y_off += 74
                x = 0
            else:
                x += 400

        for service in self.config.services:
            create_ui(service)

        self.run_ssh_func_persistent(
            self.config,
            'service_state',
            self.do_fetch_service_info,
            self.config.services
        )
        self.max_no_data_seconds = int(config.retry_seconds) * 4.0
        self.data_good("services", no_data_allowed_time=self.max_no_data_seconds)
        self.no_data = False

        self.remaining_bounds = pygame.Rect(
            0,
            y_off,
            cfg.display.DISPLAY_W,
            cfg.display.DISPLAY_H - y_off
        )
        # resize terminal view down to cover only 
        # remaining space, as it inited fullscreen
        self.terminal_view.set_bounds(self.remaining_bounds)


    def setup_logviewer(self, service):
        self.set_tail_command(f"journalctl --no-hostname -f -u {service}.service")

    def update(self, dt):
        if self.data_updated:
            count = 0
            running = 0
            activating = 0
            errored = 0
            for unit_name in self.config.services:
                service = self.service_status.get(unit_name, {})
                self.ui_element_values[unit_name]['description'].set_text(service.get('description', unit_name))
                self.ui_element_values[unit_name]['load'].set_text(service.get('load', ''))
                self.ui_element_values[unit_name]['sub'].set_text(service.get('sub', ''))
                self.ui_element_values[unit_name]['active'].set_text(service.get('active', ''))
                
                button_text = "Start" if service.get('active') in ('inactive', 'disabled', 'failed') else 'Stop'
                [ button.set_text(button_text) 
                    for button in self.ui_element_start_stop_buttons.keys()
                    if self.ui_element_start_stop_buttons[button] == unit_name ]
                if service:
                    count += 1
                if service.get('active') == "active":
                    running += 1
                if service.get('active') == 'activating':
                    activating += 1
                if service.get('active') == 'failed':
                    errored += 1
                
            icon = None
            if activating > 0:
                icon = 'warning_orange'
            if errored > 0 or self.no_data:
                icon = 'warning_red'

            self.status_icon.update(count, running, errored, icon=icon)
            self.status_icons_updated = True
        super().update(dt)
    
    def no_data_update_for(self, data_for, sec_since):
        self.service_status = {}
        self.status_icon.update(0,0,0, icon='warning_red')
        self.status_icons_updated = True
        self.no_data = True

    def draw(self, screen):
        if super().draw(screen):
            return True
        return False

    def process_events(self, e):
        super().process_events(e)
        if e.type == pygame.USEREVENT and e.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if e.ui_element in self.ui_element_start_stop_buttons:
                service = self.ui_element_start_stop_buttons[e.ui_element]
                self.setup_logviewer(service)
                def run_cmd(ts):
                    res = self.run_command(ts, f"sudo service {service} {e.ui_element.text.lower()}")
                    self.console_message_onceonly(res)
                    # immediately reload service info
                    self.do_fetch_service_info(ts, self.config.services)
                self.run_ssh_func_single(self.config, run_cmd)
            elif e.ui_element in self.ui_element_status_buttons:
                service = self.ui_element_status_buttons[e.ui_element]
                self.setup_logviewer(service)


    def do_fetch_service_info(self,ts,services):
        def run_command(cmd):
            return self.run_command(ts,cmd)

        list_units = run_command('systemctl list-units --type=service --all --output json --no-pager')
        units = json.loads(list_units)
        
        list_unit_files = run_command('systemctl list-unit-files --type=service --all --output json --no-pager')
        unit_files = json.loads(list_unit_files)

        unit_details = {}

        for service in services:
            unit = [unit for unit in units if unit['unit'] == f"{service}.service"]
            if len(unit) >= 1:
                unit_details[service] = unit[0]
            else:
                unit = [unit for unit in unit_files if unit['unit_file'] == f"{service}.service"]
                if len(unit) >= 1:
                    unit_details[service] = {
                        "description": service,
                        "load": 'unloaded',
                        "active": unit[0]['state']
                    }
                else:
                    unit_details[service] = { "description": f"Unit {service} not found"}
        
        prev_service_status = self.service_status
        self.service_status = unit_details
        if prev_service_status != self.service_status:
            self.data_updated = True
            self.data_good("services", no_data_allowed_time=self.max_no_data_seconds)
            self.no_data = False