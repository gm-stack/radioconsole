import math
import html
import threading
import time
import socket
import select

import pygame
import pygame_gui
import paramiko

import crash_handler
from AppManager.app import app
from config_reader import cfg

from .TerminalView import TerminalView

class LogViewer(app):
    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)

        self.command_buttons = {}

        def createCommandButton(command_name):
            total_padding = (config.command_buttons_x + 1) * config.command_button_margin
            button_w = (cfg.display.DISPLAY_W - total_padding) // config.command_buttons_x
            button_num = len(self.command_buttons)
            button_col = button_num % config.command_buttons_x
            button_row = button_num // config.command_buttons_x

            self.command_buttons[command_name] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    config.command_button_margin + ((button_w + config.command_button_margin) * button_col),
                    cfg.display.DISPLAY_H - config.command_button_margin -
                        ((config.command_button_h + config.command_button_margin) * (button_row + 1)),
                    button_w,
                    config.command_button_h
                ),
                text=command_name,
                manager=self.gui
            )

        for command_name in config.commands:
            createCommandButton(command_name)

        buttons_h = (config.command_button_h + config.command_button_margin) * \
            int(math.ceil(len(config.commands) / config.command_buttons_x))

        self.terminal_view = TerminalView(
            x=0,
            y=cfg.display.TOP_BAR_SIZE,
            width=cfg.display.DISPLAY_W,
            height=cfg.display.DISPLAY_H - cfg.display.TOP_BAR_SIZE - buttons_h - config.command_button_margin
        )

        self.backend_thread = threading.Thread(
            target=self.backend_loop,
            daemon=True
        )
        self.backend_thread.start()


    def status_message(self, text):
        self.terminal_view.write(text, colour='cyan')
        self.data_updated = True

    def error_message(self, text):
        self.terminal_view.write(text, colour='red')
        self.data_updated = True

    def console_message(self, text):
        self.terminal_view.write(text, colour='white')
        self.data_updated = True

    def console_message_onceonly(self, text):
        self.terminal_view.write(text, colour='brightwhite')
        self.data_updated = True

    @crash_handler.monitor_thread
    def backend_loop(self):
        self.run_command(cmd=self.config.command, onceonly=False)

    @crash_handler.monitor_thread_exception
    def run_command_thread(self, cmd):
        self.run_command(cmd=cmd, onceonly=True)

    def run_command(self, cmd='', onceonly=False):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        while True:
            try:
                self.status_message(f"ssh {self.config.username}@{self.config.host}:{self.config.port}")
                ssh.connect(
                    self.config.host,
                    username=self.config.username,
                    port=self.config.port,
                    timeout=5,
                    banner_timeout=10
                )

                ts = ssh.get_transport()

                while True:
                    ch = ts.open_session()
                    ch.set_combine_stderr(True)
                    stdout = ch.makefile('rb', -1)

                    self.status_message(f"$ {cmd}\n")
                    ch.exec_command(cmd)

                    while True:
                        out = stdout.channel.recv(1024)
                        if not out:
                            break
                        else:
                            out_text = out.decode('UTF-8')
                            self.console_message_onceonly(out_text) if onceonly else self.console_message(out_text)

                    exit_status = stdout.channel.recv_exit_status()
                    msg = f"\nCommand exited with status {exit_status}\n"
                    if not onceonly:
                        msg += f"Retrying in {self.config.retry_seconds}s\n"
                    if exit_status == 0:
                        self.status_message(msg)
                    else:
                        self.error_message(msg)

                    if onceonly:
                        return
            except OSError as e:
                self.error_message(f"\nConnection error: {str(e)}\n"
                    + f"retrying in {self.config.retry_seconds}s\n" if onceonly else '')
            except paramiko.SSHException as e:
                self.error_message(f"\nSSH error: {str(e)}\n"
                    + f"retrying in {self.config.retry_seconds}s\n" if onceonly else '')

            if onceonly:
                return
            time.sleep(self.config.retry_seconds)

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
                command = self.config.commands[e.ui_element.text]
                self.status_message(f"\n---\n>>> {command}\n")
                th = threading.Thread(
                    target=self.run_command_thread,
                    args=[command],
                    daemon=True
                )
                th.start()
