import re
import math

import pygame
import pygame_gui

from ..common.LogViewerStatusApp import LogViewerStatusApp
from util import stat_view, stat_label, stat_display

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

        self.process_messages = [
            {"r": r'\S*: Sample rate approx\. .* receive audio level \S* (\d*)', 'ui': ['audio_level']},
            {"r": r'\[ig\](?! #) (.*)', 'ui': ['igate_packet']},
            {"r": r'\[0L\] (.*)', 'ui': ['radio_packet']},
            {"r": r'\[\d.\d\] (.*)', 'ui': ['rx_packet']},
            {"r": r'Error getting data from radio'},
            {"r": r'Now connected to IGate server (.*)', 'ui': ['igate_server']},
            {"r": r'\[ig\] # logresp \S* verified, server (\S*)', 'ui': ['igate_server_name']},
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
        self.ui['igate_packet_ago'] = stat_view(
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
        self.ui['igate_packet'] = stat_view(
            relative_rect=pygame.Rect(0, y, 800, 32),
            name='tx_igate',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 32
        self.ui['igate_packet_ago'] = stat_view(
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
        y += 32
        self.ui['igate_server_name'] = stat_view(
            relative_rect=pygame.Rect(400,y,400,32),
            name='igate_s',
            manager=self.gui,
            split='lr',
            label_s=100
        )

        y += 40
        self.ui['radio_packet'] = stat_view(
            relative_rect=pygame.Rect(0, y, 800, 32),
            name='tx_rf',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 32
        self.ui['radio_packet_ago'] = stat_view(
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




        # self.ui['protomode'] = stat_view(
        #     relative_rect=pygame.Rect(610, y, 190, 32),
        #     name='mode',
        #     manager=self.gui,
        #     split='lr'
        # )
        # y += 32
        # self.ui['bandwidth'] = stat_view(
        #     relative_rect=pygame.Rect(610, y, 190, 32),
        #     name='bandwidth',
        #     manager=self.gui,
        #     split='lr'
        # )



        # self.ui['input_peaks'] = stat_display(
        #     relative_rect=pygame.Rect(0, y, 800, 32),
        #     manager=self.gui,
        #     text="input_peaks"
        # )

        # y += 32
        # self.ui['status'] = stat_view(
        #     relative_rect=pygame.Rect(0, y, 800, 32),
        #     manager=self.gui,
        #     name="status",
        #     split='lr',
        #     label_s=100
        # )


        terminal_bounds.top = y
        terminal_bounds.height = (bounds.h + bounds.y) - y - config.command_button_h
        print(terminal_bounds)
        self.terminal_view.set_bounds(terminal_bounds)

        self.data_updated = True

    #def filter(self, line):
    #    filtered_msg = super().filter(line)
    #    print(str(filtered_msg.msg.message))