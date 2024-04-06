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

from ..LogViewer import LogViewer

class SystemDStatus(app):
    service_status = {}
    ui_element_values = {}
    ui_element_start_stop_buttons = {}
    ui_element_status_buttons = {}

    log_viewer = None

    data_updated = False

    def __init__(self, bounds, config, display, name):
        super().__init__(bounds, config, display, name)

        y_off = display.TOP_BAR_SIZE
        x = 0

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

        self.backend_thread = threading.Thread(
            target=self.run_command,
            args=[self.config],
            daemon=True
        )
        self.backend_thread.start()

        self.remaining_bounds = pygame.Rect(
            0,
            y_off,
            cfg.display.DISPLAY_W,
            cfg.display.DISPLAY_H - y_off
        )


    def setup_logviewer(self, service):
        name = f"systemd_logviewer_{service}"
        if self.log_viewer and name == self.log_viewer.name:
            return

        command = f"journalctl --no-hostname -f -u {service}.service"

        log_viewer_cfg = types.SimpleNamespace(
            username=self.config.username,
            host=self.config.host,
            port=self.config.port,
            retry_seconds=5,
            command=command,
            commands=[],
            command_button_h=0,
            command_buttons_x=1,
            command_button_margin=0
        )

        if self.log_viewer:
            self.log_viewer.stop_backend_thread()
            del self.log_viewer
        
        self.log_viewer = LogViewer(self.remaining_bounds, log_viewer_cfg, self.display, name)


    def update(self, dt):
        if self.data_updated:
            for unit_name in self.config.services:
                service = self.service_status.get(unit_name, None)
                if service:
                    self.ui_element_values[unit_name]['description'].set_text(service.get('description', unit_name))
                    self.ui_element_values[unit_name]['load'].set_text(service.get('load', ''))
                    self.ui_element_values[unit_name]['sub'].set_text(service.get('sub', ''))
                    self.ui_element_values[unit_name]['active'].set_text(service.get('active', ''))
                    
                    button_text = "Start" if service.get('active') in ('inactive', 'disabled', 'failed') else 'Stop'
                    [ button.set_text(button_text) 
                        for button in self.ui_element_start_stop_buttons.keys()
                        if self.ui_element_start_stop_buttons[button] == unit_name ]

        if self.log_viewer:
            self.log_viewer.update(dt)
            if self.log_viewer._had_update:
                self.data_updated = True
        super().update(dt)

    def draw(self, screen):
        if self.log_viewer:
            self.log_viewer.draw(screen)
        if super().draw(screen):
            return True
        return False

    def process_events(self, e):
        super().process_events(e)
        if e.type == pygame.USEREVENT and e.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if e.ui_element in self.ui_element_start_stop_buttons:
                service = self.ui_element_start_stop_buttons[e.ui_element]
                self.setup_logviewer(service)
                self.log_viewer.run_command(f"sudo service {service} {e.ui_element.text.lower()}")
                # todo: immediate refresh
            elif e.ui_element in self.ui_element_status_buttons:
                service = self.ui_element_status_buttons[e.ui_element]
                self.setup_logviewer(service)
                

    @crash_handler.monitor_thread_exception
    def run_command(self, config):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        services = set(config.services)

        while True:
            try:
                ssh.connect(
                    config.host,
                    username=config.username,
                    port=config.port,
                    timeout=5,
                    banner_timeout=10
                )

                ts = ssh.get_transport()

                def run_command(cmd):
                    ch = ts.open_session()
                    ch.set_combine_stderr(True)
                    stdout = ch.makefile('rb', -1)
                    ch.exec_command(cmd)
                    res = bytes()
                    while True:
                        out = stdout.channel.recv(1024)
                        if not out:
                            break
                        else:
                            res += out
                    return res.decode('UTF-8').rstrip(' \t\r\n\x00')

                while True:
                    self.status = ""
                    
                    try:
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
                        
                        self.service_status = unit_details

                    except Exception as e:
                        print(e)
                    
                    self.data_updated = True
                    time.sleep(self.config.refresh_seconds)

            except OSError as e:
                self.status = f"Connection error: {str(e)}"
                self.data_updated = True

            except paramiko.SSHException as e:
                self.status = f"SSH error: {str(e)}"
                self.data_updated = True

            time.sleep(1)