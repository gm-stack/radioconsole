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

        y = display.TOP_BAR_SIZE

        self.ui_element_values['id'] = pygame_gui.elements.ui_label.UILabel(
            relative_rect=pygame.Rect(0, y, 512, 32),
            text='', manager=self.gui, object_id="#param_label"
        )
        # self.ui_element_values['hostname'] = pygame_gui.elements.ui_label.UILabel(
        #     relative_rect=pygame.Rect(64, y, 256, 32),
        #     text='', manager=self.gui, object_id="#param_value"
        # )

        # self.ui_element_labels['ipaddr'] = pygame_gui.elements.ui_label.UILabel(
        #     relative_rect=pygame.Rect(, y, 128, 32),
        #     text='ipaddr', manager=self.gui, object_id="#param_label"
        # )
        # self.ui_element_values['ipaddr'] = pygame_gui.elements.ui_label.UILabel(
        #     relative_rect=pygame.Rect(320, y, 128, 32),
        #     text='', manager=self.gui, object_id="#param_value"
        # )

        # self.ui_element_labels['model'] = pygame_gui.elements.ui_label.UILabel(
        #     relative_rect=pygame.Rect(384, y, 416, 32),
        #     text='model', manager=self.gui, object_id="#param_label"
        # )
        # self.ui_element_values['model'] = pygame_gui.elements.ui_label.UILabel(
        #     relative_rect=pygame.Rect(448, y, 352, 32),
        #     text='', manager=self.gui, object_id="#param_value"
        # )

        y += config.line_height

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
                    relative_rect=pygame.Rect(128, y, 128, 32),
                    text='',
                    manager=self.gui,
                    object_id="#param_value"
                )
                y += config.line_height

        create_ui_elements(['frequency', 'volts_core', 'temp'])

        for i, ui_element in enumerate(['undervolt', 'freqcap', 'core_throttled', 'templimit']):
            self.ui_element_labels[ui_element] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(i*128, y, 128, 32),
                text=ui_element,
                manager=self.gui,
                object_id="#param_label"
            )
            self.ui_element_values[ui_element] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(i*128, y+config.line_height, 128, 32),
                text='',
                manager=self.gui,
                object_id="#param_value"
            )
        y += config.line_height * 2.5

        self.data = {}

        self.backend_thread = threading.Thread(
            target=self.run_command,
            daemon=True
        )
        self.backend_thread.start()

    def parse_vc_throttle_status(self, status):
        if not status:
            return {}
        status = int(status.split('=')[1],16)

        undervolt = bool(status & 0x1)
        freqcap = bool(status & 0x2)
        throttled = bool(status & 0x4)
        templimit = bool(status & 0x8)

        prev_undervolt = bool(status & 0x10000)
        prev_freqcap = bool(status & 0x20000)
        prev_throttled = bool(status & 0x40000)
        prev_templimit = bool(status & 0x80000)

        return {
            'undervolt': 'ALERT' if undervolt else ('PREV' if prev_undervolt else 'OK'),
            'freqcap': 'ALERT' if freqcap else ('PREV' if prev_freqcap else 'OK'),
            'core_throttled': 'ALERT' if throttled else ('PREV' if prev_throttled else 'OK'),
            'templimit': 'ALERT' if templimit else ('PREV' if prev_templimit else 'OK')
        }

    def frequency(self, freq):
        if not freq:
            return ''
        freq = int(freq.split("=")[1])
        return f"{freq/1000000.0:.0f}MHz"

    def update(self, dt):
        if self.data_updated:
            self.data.update(self.parse_vc_throttle_status(self.data.get('throttled')))
            self.data['id'] = f"{self.data.get('hostname', '')}: {self.data.get('model', '')}"
            self.data['frequency'] = self.frequency(self.data.get('clock_arm'))
            self.data['volts_core'] = self.data.get('volts_core','').split('=')[-1]
            self.data['temp'] = self.data.get('temp', '').split('=')[-1].replace("'",'\N{DEGREE SIGN}')

            for key, gui in self.ui_element_values.items():
                gui.set_text(self.data.get(key, ''))

        super().update(dt)

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