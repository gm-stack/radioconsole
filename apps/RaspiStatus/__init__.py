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

        def create_ui(host):
            nonlocal y

            self.ui_element_labels[host] = {}
            self.ui_element_values[host] = {}
            self.ui_element_graphs[host] = {}

            self.ui_element_values[host]['id'] = pygame_gui.elements.ui_label.UILabel(
                relative_rect=pygame.Rect(0, y, 800, 32),
                text='', manager=self.gui, object_id="#param_label"
            )

            y += config.line_height

            def create_ui_elements(l):
                nonlocal y
                for ui_element in l:
                    self.ui_element_labels[host][ui_element] = pygame_gui.elements.ui_label.UILabel(
                        relative_rect=pygame.Rect(0, y, 128, 32),
                        text=ui_element,
                        manager=self.gui,
                        object_id="#param_label"
                    )
                    self.ui_element_values[host][ui_element] = pygame_gui.elements.ui_label.UILabel(
                        relative_rect=pygame.Rect(128, y, 128, 32),
                        text='',
                        manager=self.gui,
                        object_id="#param_value"
                    )
                    self.ui_element_graphs[host][ui_element] = timegraph(
                        pygame.Rect(256, y, 544, 32)
                    )

                    y += config.line_height

            create_ui_elements(['frequency', 'cpu_temp', 'free_mem'])

            for i, ui_element in enumerate(['undervolt', 'freqcap', 'core_throttled', 'templimit']):
                self.ui_element_labels[host][ui_element] = pygame_gui.elements.ui_label.UILabel(
                    relative_rect=pygame.Rect(i*110, y, 110, 32),
                    text=ui_element,
                    manager=self.gui,
                    object_id="#param_label"
                )
                self.ui_element_values[host][ui_element] = pygame_gui.elements.ui_label.UILabel(
                    relative_rect=pygame.Rect(i*110, y+config.line_height, 110, 32),
                    text='',
                    manager=self.gui,
                    object_id="#param_value"
                )

            self.ui_element_labels[host]['cpu'] = pygame_gui.elements.ui_label.UILabel(
                    relative_rect=pygame.Rect(440, y, 32, 64),
                    text='cpu',
                    manager=self.gui,
                    object_id="#param_label"
            )
            for i in range(4):
                self.ui_element_graphs[host][f"cpu{i}_percent"] = timegraph(
                    pygame.Rect(472, y+(i*16), 328, 16),
                    max_value=100.0,
                    min_value=0.0
                )

            y += config.line_height * 2.5

        self.data = {}

        for host in self.config.hosts:
            create_ui(host['host'])
            self.data[host['host']] = {}
            self.backend_thread = threading.Thread(
                target=self.run_command,
                args=[host],
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

    def colour_for_throttle_status(self, status):
        return {
            'ALERT': (255, 0, 0, 255),
            'PREV': (255, 255, 0, 255),
            'OK': (0, 255, 0, 255)
        }.get(status, (127, 127, 127, 255))

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

    def parse_procstat(self, data):
        stat = data.get('stat')
        if not stat:
            return
        statlines = [l for l in stat.split('\n') if l.startswith('cpu') and not l.startswith('cpu ')]
        for line in statlines:
            lp = line.split(" ")
            cpu_num = int(lp[0][3])
            nums = [int(x) for x in lp[1:]]

            prev_idletime = data.get(f"cpu{cpu_num}_idletime", 0)
            idletime = nums[3]

            prev_totaltime = data.get(f"cpu{cpu_num}_totaltime", 0)
            totaltime = sum(nums)

            if totaltime == prev_totaltime: # no time passed since last measurement
                return

            data[f"cpu{cpu_num}_percent"] = 1.0 - ((idletime - prev_idletime) / (totaltime - prev_totaltime))
            data[f"cpu{cpu_num}_idletime"] = idletime
            data[f"cpu{cpu_num}_totaltime"] = totaltime

    def update(self, dt):
        if self.data_updated:
            for hostconfig in self.config.hosts:
                host = hostconfig['host']
                data = self.data[host]
                data.update(self.parse_vc_throttle_status(data.get('throttled')))
                data['id'] = f"{data.get('hostname', '')}: {data.get('model', '')}" \
                    if not data.get('status') else data['status']

                volts = data.get('volts_core', '').split('=')[-1].rstrip('V')
                freq = self.frequency(data.get('clock_arm'))
                if freq and volts:

                    data['frequency'] = f"{freq/1000000.0:.0f}MHz/{float(volts):.2f}V"
                    self.ui_element_graphs[host]['frequency'].datapoint(freq)

                temp = data.get('temp', '').split('=')[-1].rstrip("'C")
                if temp:
                    data['cpu_temp'] = f"{temp}\N{DEGREE SIGN}C"
                    self.ui_element_graphs[host]['cpu_temp'].datapoint(float(temp))

                data.update(self.parse_meminfo(data.get('meminfo')))

                mem_available = data.get('MemAvailable')
                if mem_available:
                    data['free_mem'] = self.mb(mem_available)
                    self.ui_element_graphs[host]['free_mem'].datapoint(float(mem_available)/1024)

                for key, gui in self.ui_element_values[host].items():
                    gui.set_text(data.get(key, ''))

                for ui_element in ['undervolt', 'freqcap', 'core_throttled', 'templimit']:
                    el = self.ui_element_values[host][ui_element]
                    c = self.colour_for_throttle_status(data.get(ui_element))
                    if el.text_colour != c:
                        el.text_colour = c
                        el.rebuild()

                self.parse_procstat(data)
                for g in ['cpu0_percent', 'cpu1_percent', 'cpu2_percent', 'cpu3_percent']:
                    cpu_percent = data.get(g)
                    if cpu_percent:
                        self.ui_element_graphs[host][g].datapoint(cpu_percent)

        super().update(dt)

    def draw(self, screen):
        if super().draw(screen):
            for host_graphs in self.ui_element_graphs.values():
                for graph in host_graphs.values():
                    graph.draw(screen)
            return True
        return False

    @crash_handler.monitor_thread_exception
    def run_command(self, host):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        while True:
            try:
                ssh.connect(
                    host['host'],
                    username=host['username'],
                    port=host['port'],
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

                self.data[host['host']]['model'] = run_command('cat /proc/device-tree/model')
                self.data[host['host']]['hostname'] = run_command('hostname')

                while True:
                    self.data[host['host']]['clock_arm'] = run_command('vcgencmd measure_clock arm')
                    self.data[host['host']]['throttled'] = run_command('vcgencmd get_throttled')
                    self.data[host['host']]['volts_core'] = run_command('vcgencmd measure_volts core')
                    self.data[host['host']]['temp'] = run_command('vcgencmd measure_temp')
                    self.data[host['host']]['meminfo'] = run_command('cat /proc/meminfo')
                    self.data[host['host']]['stat'] = run_command('cat /proc/stat')


                    self.data[host['host']]['status'] = ''

                    self.data_updated = True
                    time.sleep(self.config.refresh_seconds)

            except OSError as e:
                self.data[host['host']]['status'] = f"Connection error: {str(e)}"
                self.data_updated = True
            except paramiko.SSHException as e:
                self.data[host['host']]['status'] = f"SSH error: {str(e)}"
                self.data_updated = True

            time.sleep(self.config.refresh_seconds)