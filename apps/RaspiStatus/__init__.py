import time
import threading

import pygame
import pygame_gui
import paramiko

import crash_handler
from AppManager.app import app
from config_reader import cfg

class RaspiStatus(app):
    ui_element_labels = {}
    ui_element_values = {}

    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)

        self.gui = pygame_gui.UIManager(cfg.display.size, cfg.theme_file)

        y = display.TOP_BAR_SIZE

        def create_ui_elements(l):
            nonlocal y
            for ui_element in l:
                self.ui_element_labels[ui_element] = pygame_gui.elements.ui_label.UILabel(
                    relative_rect=pygame.Rect(0, y, 128, 32),
                    text=ui_element,
                    manager=self.gui,
                    object_id="#param_label"
                )
                self.ui_element_values[ui_element] = pygame_gui.elements.ui_label.UILabel(
                    relative_rect=pygame.Rect(128, y, 384, 32),
                    text='',
                    manager=self.gui,
                    object_id="#param_value"
                )
                y += config.line_height

        create_ui_elements(['model', 'hostname', 'clock_arm', 'throttled', 'volts_core', 'temp'])

        self.data = {}
        self.data_updated = False

        self.backend_thread = threading.Thread(
            target=self.run_command,
            daemon=True
        )
        self.backend_thread.start()

    def draw(self, screen):
        self.gui.draw_ui(screen)

    def update(self, dt):
        if self.data_updated:
            for key, gui in self.ui_element_values.items():
                gui.set_text(self.data.get(key, ''))

            self.data_updated = False
        self.gui.update(dt)

    def process_events(self, e):
        self.gui.process_events(e)

    @crash_handler.monitor_thread_exception
    def run_command(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        while True:
            try:
                ssh.connect(
                    self.config.host,
                    username=self.config.username,
                    port=self.config.port,
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

                self.data['model'] = run_command('cat /proc/device-tree/model')
                self.data['hostname'] = run_command('hostname')

                while True:
                    self.data['clock_arm'] = run_command('vcgencmd measure_clock arm')
                    self.data['throttled'] = run_command('vcgencmd get_throttled')
                    self.data['volts_core'] = run_command('vcgencmd measure_volts core')
                    self.data['temp'] = run_command('vcgencmd measure_temp')

                    self.data_updated = True
                    time.sleep(self.config.refresh_seconds)

            except OSError as e:
                raise e
                #self.error_message(f"\nConnection error: {str(e)}, "
                #    + f"retrying in {self.config.retry_seconds}s" if onceonly else '')
            except paramiko.SSHException as e:
                raise e
                #self.error_message(f"\nSSH error: {str(e)}, "
                #    + f"retrying in {self.config.retry_seconds}s" if onceonly else '')

            time.sleep(self.config.refresh_seconds)