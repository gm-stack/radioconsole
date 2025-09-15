import pygame

from ..common.LogViewerStatusApp import DockerLogViewerStatusApp
from util import stat_view, stat_display

class ARDOPStatus(DockerLogViewerStatusApp):
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

        self.services = ['carpi-compose-ardopcf-1']

        self.ui = {}
        y = bounds.y

        terminal_bounds = pygame.Rect(bounds)

        self.process_messages = [
            {"r": r'Sending Frame Type (.*)', "ui": ['tx_frame']},
            {"r": r'Input peaks = ([-\d]*, [-\d]*)', "ui": ['input_peaks']},
            {"r": r'strMycall=(\S*)', "ui": ['mycall']},
            {"r": r'strTargetCall=(\S*)', "ui": ['tocall']},
            {"r": r'\[DecodeFrame\] Frame: (\S*)', "ui": ['rx_frame']},
            {"r": r'Constellation Quality= (\d*)', "ui": ['quality']},
            {"r": r'\[STATUS: (.*)]', "ui": ['status']},
            {"r": r'new (?:Protocol )?[sS]tate ([a-zA-Z]*)', "ui": ['state']},
            {"r": r'going to ([a-zA-Z]*) state', "ui": ['state']},
            {"r": r'Sending Frame Type ([0-9]*[A-Z]*\.\d*\.\d*S?)\.[EO]', "ui": ['mode']},
            {"r": r'New Mode: ([0-9]*[A-Z]*\.\d*\.\d*S?)', "ui": ['mode']},
            {"r": r'SESSION BW = (\d*) HZ', "ui": ['bandwidth']},
            {"r": r'ConAck: (\d*) Hz', "ui": ['bandwidth']},
            {"r": r'Setting ProtocolMode to (.*)\.', "ui": ['protomode']},
        ]

        super().__init__(terminal_bounds, config, name)

        self.ui['rx_frame'] = stat_view(
            relative_rect=pygame.Rect(0, y, 300, 32),
            name='rx_frame',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        self.ui['quality'] = stat_view(
            relative_rect=pygame.Rect(300, y, 300, 32),
            name='quality',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 32
        self.ui['tx_frame'] = stat_view(
            relative_rect=pygame.Rect(0, y, 300, 32),
            name='tx_frame',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        self.ui['mode'] = stat_view(
            relative_rect=pygame.Rect(300, y, 300, 32),
            name='mode',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        y += 32
        self.ui['mycall'] = stat_view(
            relative_rect=pygame.Rect(0, y, 300, 32),
            name='mycall',
            manager=self.gui,
            split='lr',
            label_s=100
        )
        self.ui['tocall'] = stat_view(
            relative_rect=pygame.Rect(300, y, 300, 32),
            name='tocall',
            manager=self.gui,
            split='lr',
            label_s=100
        )

        y = bounds.y

        self.ui['state'] = stat_view(
            relative_rect=pygame.Rect(610, y, 190, 32),
            name='state',
            manager=self.gui,
            split='lr'
        )
        y += 32
        self.ui['protomode'] = stat_view(
            relative_rect=pygame.Rect(610, y, 190, 32),
            name='mode',
            manager=self.gui,
            split='lr'
        )
        y += 32
        self.ui['bandwidth'] = stat_view(
            relative_rect=pygame.Rect(610, y, 190, 32),
            name='bandwidth',
            manager=self.gui,
            split='lr'
        )

        y += 40

        self.ui['input_peaks'] = stat_display(
            relative_rect=pygame.Rect(0, y, bounds.w, 32),
            manager=self.gui,
            text="input_peaks"
        )

        y += 32
        self.ui['status'] = stat_view(
            relative_rect=pygame.Rect(0, y, bounds.w, 32),
            manager=self.gui,
            name="status",
            split='lr',
            label_s=100
        )
        y += 32

        terminal_bounds.top = y
        terminal_bounds.height = (bounds.h + bounds.y) - y - config.command_button_h
        self.terminal_view.set_bounds(terminal_bounds)

        self.data_updated = True
