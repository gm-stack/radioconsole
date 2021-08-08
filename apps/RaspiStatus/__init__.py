import time
import threading

import pygame
import paramiko

import crash_handler
from AppManager.app import app
from config_reader import cfg
from util import timegraph, stat_display, stat_label, stat_view, stat_view_graph, extract_number
from .status_icon import raspi_status_icon

class RaspiStatus(app):
    ui_element_labels = {}
    ui_element_values = {}
    ui_element_graphs = {}
    cpu_graph_y = {}

    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)

        y = display.TOP_BAR_SIZE

        def create_ui(host):
            nonlocal y

            self.ui_element_labels[host] = {}
            self.ui_element_values[host] = {}
            self.ui_element_graphs[host] = {}

            self.ui_element_values[host]['id'] = stat_label(
                relative_rect=pygame.Rect(0, y, 800, 32),
                text='', manager=self.gui
            )
            y += config.line_height

            for ui_element, unit in {'frequency': '', 'cpu_temp': "\N{DEGREE SIGN}C", 'free_mem': 'MB'}.items():
                self.ui_element_graphs[host][ui_element] = stat_view_graph(
                    relative_rect=pygame.Rect(0, y, 800, 32),
                    text_w=256,
                    name=ui_element,
                    manager=self.gui,
                    unit=unit
                )
                y += config.line_height

            for i, ui_element in enumerate(['undervolt', 'freqcap', 'core_throttled', 'templimit']):
                self.ui_element_values[host][ui_element] = stat_view(
                    relative_rect=pygame.Rect(i*110, y, 110, 64),
                    name=ui_element,
                    manager=self.gui,
                    split='tb',
                    colourmap={
                        'ALERT': (255, 0, 0, 255),
                        'PREV': (255, 255, 0, 255),
                        'OK': (0, 255, 0, 255),
                        None: (127, 127, 127, 255)
                    },
                    colourmap_mode='equals'
                )

            self.ui_element_labels[host]['cpu'] = stat_label(
                relative_rect=pygame.Rect(440, y, 32, 64),
                text='cpu',
                manager=self.gui
            )
            self.cpu_graph_y[host] = y

            y += config.line_height * 2.5

        self.data = {}
        self.host_updated = {host['host']: True for host in self.config.hosts}

        for host in self.config.hosts:
            create_ui(host['host'])
            self.data[host['host']] = {}
            status_icon = raspi_status_icon()
            self.status_icons.append(status_icon.surface)
            self.backend_thread = threading.Thread(
                target=self.run_command,
                args=[host, status_icon],
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
        data['n_cpus'] = len(statlines)
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
        for hostconfig in self.config.hosts:
            host = hostconfig['host']
            if self.host_updated[host]:
                self.host_updated[host] = False
                data = self.data[host]
                data.update(self.parse_vc_throttle_status(data.get('throttled')))

                data['id'] = f"{data.get('hostname', '')}: {data.get('model', '')}" \
                    if not data.get('status') else data['status']

                if self.data[host].get('freqdisp'):
                    self.ui_element_graphs[host]['frequency'].update(
                        self.data[host].get('volts'),
                        self.data[host].get('freqdisp')
                    )

                self.ui_element_graphs[host]['cpu_temp'].update(extract_number(data.get('temp')))

                data.update(self.parse_meminfo(data.get('meminfo')))

                mem_available = extract_number(data.get('MemAvailable'))
                if mem_available:
                    self.ui_element_graphs[host]['free_mem'].update(mem_available/1024)

                for key, gui in self.ui_element_values[host].items():
                    gui.set_text(data.get(key, ''))

                self.parse_procstat(data)
                if 'n_cpus' in data:
                    if host in self.cpu_graph_y:
                        y = self.cpu_graph_y[host]
                        del self.cpu_graph_y[host]
                        cpu_h = int(64 / data['n_cpus'])
                        for i in range(data['n_cpus']):
                            self.ui_element_graphs[host][f"cpu{i}_percent"] = timegraph(
                                pygame.Rect(472, y+(i*cpu_h), 328, cpu_h),
                                max_value=100.0,
                                min_value=0.0
                            )

                    for i in range(data['n_cpus']):
                        g = f"cpu{i}_percent"
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
    def run_command(self, host, status_icon):
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

                    self.data[host['host']]['volts'] = extract_number(self.data[host['host']]['volts_core'])
                    self.data[host['host']]['clock'] = extract_number(self.data[host['host']]['clock_arm'])
                    if self.data[host['host']]['clock'] and self.data[host['host']]['volts']:
                        self.data[host['host']]['freqdisp'] = f"{self.data[host['host']]['clock']/1000000.0:.0f}MHz/{float(self.data[host['host']]['volts']):.2f}V"
                    else:
                        self.data[host['host']]['freqdisp'] = ""

                    self.data[host['host']]['temp_num'] = extract_number(self.data[host['host']]['temp'])

                    self.host_updated[host['host']] = True
                    self.data_updated = True
                    status_icon.update(self.data[host['host']])
                    time.sleep(self.config.refresh_seconds)

            except OSError as e:
                self.data[host['host']]['status'] = f"Connection error: {str(e)}"
                self.host_updated[host['host']] = True
                self.data_updated = True

            except paramiko.SSHException as e:
                self.data[host['host']]['status'] = f"SSH error: {str(e)}"
                self.host_updated[host['host']] = True
                self.data_updated = True

            time.sleep(self.config.refresh_seconds)