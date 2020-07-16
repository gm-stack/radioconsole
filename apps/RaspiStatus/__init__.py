import time
import threading

import pygame
import pygame_gui
import paramiko

import crash_handler
from AppManager.app import app
from config_reader import cfg
from util import timegraph

class RaspiStatus(app):
    ui_element_labels = {}
    ui_element_values = {}
    ui_element_graphs = {}

    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)

        y = display.TOP_BAR_SIZE

        self.ui_element_values['id'] = pygame_gui.elements.ui_label.UILabel(
            relative_rect=pygame.Rect(0, y, 800, 32),
            text='', manager=self.gui, object_id="#param_label"
        )

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
                self.ui_element_graphs[ui_element] = timegraph(
                    pygame.Rect(256, y, 544, 32)
                )

                y += config.line_height

        create_ui_elements(['frequency', 'temp', 'free_mem'])

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
            return
        return int(freq.split("=")[1])

    def mb(self, kb):
        if not kb:
            return ''
        return f"{int(kb)/1024:.0f}MB"

    def parse_meminfo(self, meminfo):
        if not meminfo:
            return {}
        params = {}
        for l in meminfo.split('\n'):
            l = l.split(":")
            params[l[0]] = l[1].strip().rstrip('kB')
        return params

    def update(self, dt):
        if self.data_updated:
            self.data.update(self.parse_vc_throttle_status(self.data.get('throttled')))
            self.data['id'] = f"{self.data.get('hostname', '')}: {self.data.get('model', '')}" \
                if not self.data.get('status') else self.data['status']

            freq = self.frequency(self.data.get('clock_arm'))
            if freq:
                self.data['frequency'] = f"{freq/1000000.0:.0f}MHz"
                self.ui_element_graphs['frequency'].datapoint(freq)

            #self.data['volts_core'] = self.data.get('volts_core', '').split('=')[-1]

            temp = self.data.get('temp', '').split('=')[-1].rstrip("'C")
            if temp:
                self.data['temp'] = f"{temp}\N{DEGREE SIGN}C"
                self.ui_element_graphs['temp'].datapoint(float(temp))

            self.data.update(self.parse_meminfo(self.data.get('meminfo')))

            mem_available = self.data.get('MemAvailable')
            if mem_available:
                self.data['free_mem'] = self.mb(mem_available)
                self.ui_element_graphs['free_mem'].datapoint(float(mem_available)/1024)

            for key, gui in self.ui_element_values.items():
                gui.set_text(self.data.get(key, ''))

        super().update(dt)

    def draw(self, screen):
        if super().draw(screen):
            for graph in self.ui_element_graphs.values():
                graph.draw(screen)
            return True
        return False

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
                    #self.data['volts_core'] = run_command('vcgencmd measure_volts core')
                    self.data['temp'] = run_command('vcgencmd measure_temp')
                    self.data['meminfo'] = run_command('cat /proc/meminfo')

                    self.data['status'] = ''

                    self.data_updated = True
                    time.sleep(self.config.refresh_seconds)

            except OSError as e:
                self.data['status'] = f"Connection error: {str(e)}"
                self.data_updated = True
            except paramiko.SSHException as e:
                self.data['status'] = f"SSH error: {str(e)}"
                self.data_updated = True

            time.sleep(self.config.refresh_seconds)