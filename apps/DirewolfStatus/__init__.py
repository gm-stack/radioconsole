import datetime

import pygame

from .status_icon import direwolf_status_icon
from ..common.time_format import hh_mm_ss
from ..common.LogViewerStatusApp import LogViewerStatusApp
from util import stat_view

class DirewolfStatus(LogViewerStatusApp):
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

        self.services = ['direwolf', 'direwolf-digi']

        self.ui = {}
        y = bounds.y

        terminal_bounds = pygame.Rect(bounds)

        self.has_rx_packet = False
        self.has_ig_tx_packet = False
        self.has_rf_tx_packet = False

        self.rx_packet_time = -1.0
        self.ig_tx_packet_time = -1.0
        self.rf_tx_packet_time = -1.0

        self.last_rx_packet_time = None
        self.last_ig_tx_packet_time = None
        self.last_rf_tx_packet_time = None

        self.igate_server = ""
        self.igate_server_name = ""

        def rx_packet(msg, match):
            self.has_rx_packet = True
            self.rx_packet_time = (datetime.datetime.now() - msg.timestamp).total_seconds()

        def ig_tx_packet(msg, match):
            self.has_ig_tx_packet = True
            self.ig_tx_packet_time = (datetime.datetime.now() - msg.timestamp).total_seconds()

        def rf_tx_packet(msg, match):
            self.has_rf_tx_packet = True
            self.rf_tx_packet_time = (datetime.datetime.now() - msg.timestamp).total_seconds()

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

        super().__init__(terminal_bounds, config, "DirewolfLogViewer")

        # todo: word wrap
        self.ui['rx_packet'] = stat_view(
            relative_rect=pygame.Rect(0, y, 800, 64),
            name='rx_rf',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 64
        self.ui['rx_packet_ago'] = stat_view(
            relative_rect=pygame.Rect(0, y, 400, 32),
            name='time ago',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        self.ui['audio_level_pkt'] = stat_view(
            relative_rect=pygame.Rect(400, y, 200, 32),
            name='pkt_level',
            manager=self.gui,
            split='lr'
        )
        self.ui['audio_level'] = stat_view(
            relative_rect=pygame.Rect(600, y, 200, 32),
            name='audio_level',
            manager=self.gui,
            split='lr'
        )

        y += 40
        self.ui['ig_tx_packet'] = stat_view(
            relative_rect=pygame.Rect(0, y, 800, 32),
            name='tx_igate',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 32
        self.ui['ig_tx_packet_ago'] = stat_view(
            relative_rect=pygame.Rect(0, y, 400, 32),
            name='time ago',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        self.ui['igate_server'] = stat_view(
            relative_rect=pygame.Rect(400,y,400,32),
            name='igate_s',
            manager=self.gui,
            split='lr',
            label_s=100
        )

        y += 40
        self.ui['rf_tx_packet'] = stat_view(
            relative_rect=pygame.Rect(0, y, 800, 32),
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
        y += 40

        terminal_bounds.top = y
        terminal_bounds.height = (bounds.h + bounds.y) - y
        self.terminal_view.set_bounds(terminal_bounds)

        self.status_icon = direwolf_status_icon()
        self.status_icons = [self.status_icon.surface]
        self.status_icon.update(None, self.rx_packet_time, self.ig_tx_packet_time, self.rf_tx_packet_time)
        self.status_icons_updated = True
        self.data_updated = True

    def update(self, dt):
        if self.has_rx_packet:
            self.rx_packet_time += dt
            rx_packet_time = hh_mm_ss(self.rx_packet_time)
            if rx_packet_time != self.last_rx_packet_time:
                self.ui['rx_packet_ago'].set_text(rx_packet_time)
                self.status_icon.update(None, self.rx_packet_time, self.ig_tx_packet_time, self.rf_tx_packet_time)
                self.last_rx_packet_time = rx_packet_time
            self.data_updated = True

        if self.has_ig_tx_packet:
            self.ig_tx_packet_time += dt
            ig_tx_packet_time = hh_mm_ss(self.ig_tx_packet_time)
            if ig_tx_packet_time != self.last_ig_tx_packet_time:
                self.ui['ig_tx_packet_ago'].set_text(ig_tx_packet_time)
                self.status_icon.update(None, self.rx_packet_time, self.ig_tx_packet_time, self.rf_tx_packet_time)
                self.last_ig_tx_packet_time = ig_tx_packet_time
            self.data_updated = True

        if self.has_rf_tx_packet:
            self.rf_tx_packet_time += dt
            rf_tx_packet_time = hh_mm_ss(self.rf_tx_packet_time)
            if rf_tx_packet_time != self.last_rf_tx_packet_time:
                self.ui['rf_tx_packet_ago'].set_text(rf_tx_packet_time)
                self.status_icon.update(None, self.rx_packet_time, self.ig_tx_packet_time, self.rf_tx_packet_time)
                self.last_rf_tx_packet_time = rf_tx_packet_time
            self.data_updated = True

        return super().update(dt)