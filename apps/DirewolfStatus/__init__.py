import ctypes
import datetime
import threading
import collections
import time
import socket

import pygame
import aprslib

import crash_handler
from .status_icon import direwolf_status_icon
from ..common.time_format import hh_mm_ss_since
from ..common.layout_utils import split_rect_horz
from ..common.LogViewerStatusApp import DockerLogViewerStatusApp
from util import stat_view, stat_display

class DirewolfStatus(DockerLogViewerStatusApp):
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

        self.services = ['carpi-compose-direwolf-hf-aprs-digi-1', 'carpi-compose-direwolf-hf-aprs-1']

        self.ui = {}
        y = bounds.y

        terminal_bounds = pygame.Rect(bounds)

        self.has_rx_packet = False
        self.has_ig_tx_packet = False
        self.has_rf_tx_packet = False

        self.rf_tx_packet_payload = ""
        self.rf_tx_packet_igate_at = None
        self.rf_tx_packet_igate_time = None
        self.last_rf_tx_packet_igate_time = None
        self.last_rf_packet_igated = False

        self.igated_packets_seen = set()
        self.aprs_igates_seen = {}
        self.aprs_igates_seen_count = collections.defaultdict(int)
        self.aprs_igates_updated = True

        self.rx_packet_time = None
        self.ig_tx_packet_time = None
        self.rf_tx_packet_time = None

        self.igate_server = ""
        self.igate_server_name = ""

        def rx_packet(msg, match):
            self.has_rx_packet = True
            self.rx_packet_time = msg.timestamp

        def ig_tx_packet(msg, match):
            self.has_ig_tx_packet = True
            self.ig_tx_packet_time = msg.timestamp
            self.data_good('tx_time', no_data_allowed_time=self.config.tx_issue_time)

        def rf_tx_packet(msg, match):
            self.has_rf_tx_packet = True
            self.rf_tx_packet_time = msg.timestamp
            self.rf_tx_packet_payload = self.aprs_packet_payload(match[1])
            self.rf_tx_packet_igate_at = None
            self.last_rf_packet_igated = False
            self.ui['last_heard'].set_text("?")
            self.ui['last_heard_by'].set_text("?")
            self.data_good('tx_time', no_data_allowed_time=self.config.tx_issue_time)

        def igate_server(msg, match):
            self.igate_server = match[1]
            self.ui['igate_server'].set_text(f"{self.igate_server} -> {self.igate_server_name}")

        def igate_server_name(msg, match):
            self.igate_server_name = match[1]
            self.ui['igate_server'].set_text(f"{self.igate_server} -> {self.igate_server_name}")

        self.process_messages = [
            {"r": r'\S*: Sample rate approx\. .* receive audio level \S* (\d*)', 'ui': ['audio_level']},
            {"r": r'\[ig\](?! #) (.*)', 'ui': ['ig_tx_packet'], 'passthrough': True, 'func': ig_tx_packet},
            {"r": r'\[0L\] (.*)', 'ui': ['rf_tx_packet'], 'passthrough': True, 'func': rf_tx_packet},
            {"r": r'\[\d.\d\] (.*)', 'ui': ['rx_packet'], 'passthrough': True, 'func': rx_packet},
            {"r": r'Error getting data from radio'},
            {"r": r'Now connected to IGate server (.*) \(.*\)', 'passthrough': True, 'func': igate_server },
            {"r": r'\[ig\] # logresp \S* verified, server (\S*)', 'func': igate_server_name, 'passthrough': True},
            {"r": r'Error reading from IGate server\.\s*Closing connection.()', 'ui': ['igate_server']},
            {"r": r'.* audio level = (\d*)\(', 'ui': ['audio_level_pkt']}
        ]

        super().__init__(terminal_bounds, config, name)

        # todo: word wrap
        self.ui['rx_packet'] = stat_view(
            relative_rect=pygame.Rect(0, y, bounds.w, 64),
            name='rx_rf',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 64
        self.ui['rx_packet_ago'] = stat_view(
            relative_rect=pygame.Rect(0, y, bounds.w/2, 32),
            name='time ago',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        self.ui['audio_level_pkt'] = stat_view(
            relative_rect=pygame.Rect(bounds.w/2, y, bounds.w/4, 32),
            name='pkt_level',
            manager=self.gui,
            split='lr'
        )
        self.ui['audio_level'] = stat_view(
            relative_rect=pygame.Rect(600, y, bounds.w/4, 32),
            name='audio_level',
            manager=self.gui,
            split='lr'
        )

        y += 40
        self.ui['ig_tx_packet'] = stat_view(
            relative_rect=pygame.Rect(0, y, bounds.w, 32),
            name='tx_igate',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 32
        self.ui['ig_tx_packet_ago'] = stat_view(
            relative_rect=pygame.Rect(0, y, bounds.w/2, 32),
            name='time ago',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        self.ui['igate_server'] = stat_view(
            relative_rect=pygame.Rect(bounds.w/2,y,bounds.w/2,32),
            name='igate_s',
            manager=self.gui,
            split='lr',
            label_s=100
        )

        y += 40
        self.ui['rf_tx_packet'] = stat_view(
            relative_rect=pygame.Rect(0, y, bounds.w, 32),
            name='tx_rf',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 32
        self.ui['rf_tx_packet_ago'] = stat_view(
            relative_rect=pygame.Rect(0, y, 266, 32),
            name='last sent',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        self.ui['last_heard'] = stat_view(
            relative_rect=pygame.Rect(266, y, 266, 32),
            name='igated',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        self.ui['last_heard_by'] = stat_view(
            relative_rect=pygame.Rect(532, y, 268, 32),
            name='igated by',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 32

        num_igate_boxes = 5
        igate_boxes = pygame.Rect(self.bounds.x, y, self.bounds.w, 32)
        self.ui['igates_seen'] = []
        for r in split_rect_horz(igate_boxes, num_igate_boxes):
            self.ui['igates_seen'].append(stat_display(
                object_id="#igate_value",
                relative_rect=r,
                manager=self.gui,
                text=""
            ))
        y += 40

        terminal_bounds.top = y
        terminal_bounds.height = (bounds.h + bounds.y) - y
        self.terminal_view.set_bounds(terminal_bounds)

        self.status_icon = direwolf_status_icon()
        self.status_icon_icon = None
        self.status_icons = [self.status_icon.surface]
        self.status_icon.update(
            self.status_icon_icon,
            self.ssh_connection_issue,
            self.rx_packet_time,
            self.ig_tx_packet_time,
            self.rf_tx_packet_time,
            self.last_rf_packet_igated,
        )
        self.status_icons_updated = True

        self.aprs_backend_thread = None
        self.restart_backend_thread()

        self.data_updated = True
        self.data_good('tx_time', no_data_allowed_time=self.config.tx_issue_time)

    def aprs_packet_payload(self, pkt):
        if not ":" in pkt:
            return pkt
        return pkt.split(":",1)[1]

    def one_second_tick(self, dt):
        if self.has_rx_packet:
            rx_packet_time = hh_mm_ss_since(self.rx_packet_time)
            self.ui['rx_packet_ago'].set_text(rx_packet_time)

        if self.has_ig_tx_packet:
            ig_tx_packet_time = hh_mm_ss_since(self.ig_tx_packet_time)
            self.ui['ig_tx_packet_ago'].set_text(ig_tx_packet_time)

        if self.has_rf_tx_packet:
            rf_tx_packet_time = hh_mm_ss_since(self.rf_tx_packet_time)
            self.ui['rf_tx_packet_ago'].set_text(rf_tx_packet_time)

        # aprs-is packets may be delayed, or log messages may be delayed
        # search our list of unmatched packets for one that matches
        if not self.rf_tx_packet_igate_at:
            for packet in list(self.igated_packets_seen):
                if packet[0] == self.rf_tx_packet_payload:
                    # assume it was igated roughly when it was sent
                    self.rf_tx_packet_igate_at = self.rf_tx_packet_time
                    self.ui['last_heard_by'].set_text(packet[1])
                    self.igated_packets_seen.remove(packet)
                    self.last_rf_packet_igated = True

        # sort igates by most recent seen
        igates_most_recent = sorted(
            self.aprs_igates_seen.keys(),
            key=lambda k: self.aprs_igates_seen[k],
            reverse=True
        )

        # go through list and set them into ui
        for i, f in enumerate(self.ui['igates_seen']):
            if i >= len(igates_most_recent):
                f.set_text("")
            else:
                igate = igates_most_recent[i]
                count = self.aprs_igates_seen_count[igate]
                msg = f"{igate} x{count} {hh_mm_ss_since(self.aprs_igates_seen[igate])}"
                f.set_text(msg)

        if self.rf_tx_packet_igate_at:
            rf_tx_packet_igate_time = hh_mm_ss_since(self.rf_tx_packet_igate_at)
            if rf_tx_packet_igate_time != self.last_rf_tx_packet_igate_time:
                self.ui['last_heard'].set_text(rf_tx_packet_igate_time)
                self.last_rf_tx_packet_igate_time = rf_tx_packet_igate_time
                self.data_updated = True
                # todo: green text on status icon

        if self.has_rx_packet or self.has_ig_tx_packet or self.has_rf_tx_packet:
            self.status_icon.update(
                self.status_icon_icon,
                self.ssh_connection_issue,
                self.rx_packet_time,
                self.ig_tx_packet_time,
                self.rf_tx_packet_time,
                self.last_rf_packet_igated,
            )
            self.status_icons_updated = True
            self.data_updated = True

    def no_data_update_for(self, data_type, sec_since):
        if data_type == 'tx_time':
            self.status_icon_icon = 'warning_red'
            self.status_icon.update(
                self.status_icon_icon,
                self.ssh_connection_issue,
                self.rx_packet_time,
                self.ig_tx_packet_time,
                self.rf_tx_packet_time,
                self.last_rf_packet_igated,
            )
        elif data_type == 'aprs_is':
            self.restart_backend_thread()

    def update(self, dt):
        self.status_icon.update(
            self.status_icon_icon,
            self.ssh_connection_issue,
            self.rx_packet_time,
            self.ig_tx_packet_time,
            self.rf_tx_packet_time,
            self.last_rf_packet_igated,
        )
        self.status_icons_updated = True
        return super().update(dt)

    def restart_backend_thread(self):
        if self.aprs_backend_thread:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.aprs_backend_thread.ident),
                ctypes.py_object(SystemExit)
            )

        self.aprs_backend_thread = threading.Thread(target=self.aprs_backend_loop, daemon=True)
        self.aprs_backend_thread.start()

    @crash_handler.monitor_thread
    def aprs_backend_loop(self):

        def recv_igate(pkt):
            path = pkt.get('path', [])
            if len(path) >= 2:
                qcons = path[0]
                igate = path[-1]
                if qcons.lower() not in ('qao', 'qar'):
                    return
                print(pkt)

                self.terminal_view.write(
                    f"{datetime.datetime.now().strftime('%H:%M:%S')}: [aprs-is>] {pkt['raw']}\n",
                    colour='brightwhite'
                )

                self.aprs_igates_seen[igate] = datetime.datetime.now()
                self.aprs_igates_seen_count[igate] += 1
                self.aprs_igates_updated = True

                payload = self.aprs_packet_payload(pkt['raw']) # part after the first ':'
                self.igated_packets_seen.add((payload, igate))
                self.data_updated = True

        def parse(pkt):
            self.data_good("aprs_is", 300.0)
            if pkt[0] != "#":
                try:
                    parsed = aprslib.parse(pkt)
                    recv_igate(parsed)
                except aprslib.ParseError as e:
                    self.terminal_view.write(
                        f"{datetime.datetime.now().strftime('%H:%M:%S')}: invalid APRS packet {e}\n",
                        colour='red'
                    )

        while True:
            self.data_good("aprs_is", 300.0)

            callsign = self.config.aprs_monitor.upper()

            try:
                self.terminal_view.write(
                    f"{datetime.datetime.now().strftime('%H:%M:%S')}: Connecting to APRS-IS from Radioconsole\n",
                    colour='brightwhite'
                )

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("rotate.aprs2.net", 14580))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                banner = s.recv(512).decode("UTF-8").rstrip("\r\n")
                if banner[0] != "#":
                    print("invalid banner")
                    continue
                print(f"connected to aprs-is: {banner}")

                callsign = f"{self.config.aprs_monitor}-{self.config.aprs_ssid}"
                login = f"user {callsign} pass -1 vers radioconsole 1.0.0 filter p/{callsign}\r\n"
                s.sendall(login.encode())

                msg = bytearray()
                while True:
                    byte = s.recv(1)
                    if len(byte) == 0:
                        print("socket errored")
                        break

                    if byte in (b'\r', b'\n'):
                        if len(msg):
                            parse(msg.decode('utf-8'))
                            msg = bytearray()
                    else:
                        msg += byte

                self.terminal_view.write(
                    f"{datetime.datetime.now().strftime('%H:%M:%S')}: APRS-IS consumer stopped\n",
                    colour='red'
                )
            except OSError as e:
                self.terminal_view.write(
                    f"{datetime.datetime.now().strftime('%H:%M:%S')}: Connection error: {str(e)}\n",
                    colour='red'
                )
                self.data_updated = True

            except EOFError as e:
                self.terminal_view.write(
                    f"{datetime.datetime.now().strftime('%H:%M:%S')}: EOF error: {str(e)}\n",
                    colour='red'
                )
                self.data_updated = True
