import re
import math

import pygame
import pygame_gui

from ..LogViewer import SystemDLogViewer
from util import stat_view, stat_label, stat_display

class LogViewerStatusApp(SystemDLogViewer):
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

    process_messages = []
    ui = {}

    def __init__(self, bounds, config, name):
        self.LogViewerStatusConfig = config

        config.services = self.services
        config.commands = {}
        config.show_service_name = False
        config.retry_seconds = 5
        config.max_scrollback = 50000
        config.command_button_h = 48
        config.command_buttons_x = 1
        config.command_button_margin = 2
        config.lookback = 1000

        super().__init__(bounds, config, "LogViewerStatus")

        self.process_messages = [{"regex": re.compile(p['r']), **p} for p in self.process_messages]
        self.ui = {}
        self.data_updated = True


    def filter(self, text):
        # see if it's str, if not, make it one
        filtered_msg = super().filter(text)
        if type(filtered_msg) is str:
            msg_text = filtered_msg
        else:
            msg_text = str(filtered_msg.msg.message)

        hide_message = False
        for m in self.process_messages:
            matches = m['regex'].search(msg_text)
            if matches:
                if 'ui' in m:
                    for i, ui_element in enumerate(m['ui']):
                        self.ui[ui_element].set_text(matches.group(i+1))
                if 'func' in m:
                    m['func'](filtered_msg, matches)
                if not m.get('passthrough', False):
                    hide_message = True

        # if our filter matched a log message
        # unless that regex has passthrough=True
        # don't write to screen
        if hide_message:
            return

        #print(msg_text)

        self.data_updated = True
        return filtered_msg