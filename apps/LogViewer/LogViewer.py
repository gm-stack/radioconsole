import math
import html
import threading
import time
import socket
import select
import ctypes
import re

import pygame
import pygame_gui
import paramiko

import crash_handler
from AppManager.app import app
from config_reader import cfg

from ..common import TerminalView, SSHBackgroundThreadApp

class LogViewer(SSHBackgroundThreadApp):

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
        "command": None
    }

    def __init__(self, bounds, config, name):
        super().__init__(bounds, config, name)

        # store this elsewhere as we may be subclassed and configured differently
        self.logviewer_config = config

        self.command_buttons = {}

        if config.command_buttons_x == 0:
            config.command_buttons_x = len(self.config.commands)

        def createCommandButton(command_name):
            total_padding = (config.command_buttons_x + 1) * config.command_button_margin
            button_w = (bounds.w - total_padding) // config.command_buttons_x
            button_num = len(self.command_buttons)
            button_col = button_num % config.command_buttons_x
            button_row = button_num // config.command_buttons_x

            self.command_buttons[command_name] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    bounds.x + config.command_button_margin + ((button_w + config.command_button_margin) * button_col),
                    (bounds.y + bounds.h) - config.command_button_margin -
                        ((config.command_button_h + config.command_button_margin) * (button_row + 1)),
                    button_w,
                    config.command_button_h
                ),
                text=command_name,
                manager=self.gui
            )

        if config.commands:
            for command_name in config.commands:
                createCommandButton(command_name)

            buttons_h = (config.command_button_h + config.command_button_margin) * \
                int(math.ceil(len(config.commands) / config.command_buttons_x))
        else:
            buttons_h = 0

        self.terminal_view = TerminalView(
            pygame.Rect(
                bounds.x,
                bounds.y,
                bounds.w,
                bounds.h - buttons_h - config.command_button_margin,
            ),
            name=self.name
        )

        self.regex_list = []
        for f in self.config.filter_lines:
            try:
                self.regex_list.append(re.compile(f))
            except re.error as e:
                print(f"Error compiling regex: '{f}'")
                raise e

        self.prev_tail_command = None

        if self.logviewer_config.command:
            self.status_message(f"ssh {self.logviewer_config.username}@{self.logviewer_config.host}:{self.logviewer_config.port}\n")
            self.set_tail_command(self.logviewer_config.command)

    def filter(self, msg):
        for r in self.regex_list:
            if r.search(msg):
                print(f"filtering line '{msg}' due to '{r}'")
                return
        return msg

    def status_message(self, text):
        self.terminal_view.write(text, colour='cyan')
        self.data_updated = True

    def error_message(self, text):
        self.terminal_view.write(text, colour='red')
        self.data_updated = True

    def console_message(self, text):
        text = self.filter(text)
        if text:
            self.terminal_view.write(text, colour='white')
            self.data_updated = True

    def console_message_onceonly(self, text):
        self.terminal_view.write(text, colour='brightwhite')
        self.data_updated = True
    
    def set_tail_command(self, command):
        if command == self.prev_tail_command:
            return
        self.prev_tail_command = command

        print(f"set tail command to {command}")

        def run_tail_command(ts, command):
            self.status_message(f"$ {command}\n")
            
            ch = ts.open_session()
            ch.set_combine_stderr(True)
            stdout = ch.makefile('rb', -1)
            ch.exec_command(command)

            while True:
                out = stdout.readline()
                if not out:
                    break
                else:
                    out_text = out.decode('UTF-8')
                    self.console_message(out_text)

            exit_status = stdout.channel.recv_exit_status()
            msg = f"\nCommand exited with status {exit_status}\n"
            msg += f"Retrying in {self.logviewer_config.retry_seconds}s\n"
            if exit_status == 0:
                self.status_message(msg)
            else:
                self.error_message(msg)

            self.data_updated = True

        self.run_ssh_func_persistent(self.config, "tail", run_tail_command, command)
    
    def run_button_command(self, command):
        self.status_message(f"\n---\n>>> {command}\n")

        def run_cmd(ts, command):
            res = self.run_command(ts, command)
            self.console_message_onceonly(res)

        self.run_ssh_func_single(self.config, run_cmd, command=command)

    def update(self, dt):
        if super().update(dt):
            self.gui.update(dt)

    def draw(self, screen):
        if super().draw(screen):
            self.terminal_view.draw(screen)
            return True
        return False

    def process_events(self, e):
        super().process_events(e)
        if e.type == pygame.USEREVENT and e.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if e.ui_element in self.command_buttons.values():
                command = self.logviewer_config.commands[e.ui_element.text]
                self.run_button_command(command)