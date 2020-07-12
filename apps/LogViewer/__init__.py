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

class LogViewer(app):
    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)

        self.gui = pygame_gui.UIManager(cfg.display.size, cfg.theme_file)
        # todo: maybe use this in app class...

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

        self.logtext = ""
        self.log_updated = True

        self.log_view = pygame_gui.elements.UITextBox(
            html_text='',
            relative_rect=pygame.Rect(
                0, cfg.display.TOP_BAR_SIZE,
                cfg.display.DISPLAY_W,
                cfg.display.DISPLAY_H - cfg.display.TOP_BAR_SIZE - \
                    buttons_h - config.command_button_margin
            ),
            manager=self.gui
        )

        self.backend_thread = threading.Thread(
            target=self.backend_loop,
            daemon=True
        )
        self.backend_thread.start()


    @staticmethod
    def esc(text):
        return html.escape(text)\
            .replace("\r\n", "\n")\
            .replace("\r", "\n")\
            .replace("\n", "<br>")

    def clear_console(self):
        self.logtext = ""
        self.log_updated = True

    def trim_scrollback(self):
        if len(self.logtext) > self.config.max_scrollback:
            self.logtext = self.logtext[-self.config.max_scrollback:]
            self.logtext = self.logtext.split('<br>', 1)[-1]

    def status_message(self, text):
        self.logtext += f"<font color='#0077FF'><b>{self.esc(text)}</b></font><br>"
        self.trim_scrollback()
        self.log_updated = True

    def error_message(self, text):
        self.logtext += f"<font color='#FF0000'><b>{self.esc(text)}</b></font><br>"
        self.trim_scrollback()
        self.log_updated = True

    def console_message(self, text):
        self.logtext += self.esc(text)
        self.trim_scrollback()
        self.log_updated = True

    def console_message_onceonly(self, text):
        self.logtext += f"<font color='#FFFFFF'>{self.esc(text)}</font>"
        self.trim_scrollback()
        self.log_updated = True

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
                        out = stdout.channel.recv(1)
                        if not out:
                            break
                        else:
                            out_text = out.decode('UTF-8')
                            self.console_message_onceonly(out_text) if onceonly else self.console_message(out_text)

                    exit_status = stdout.channel.recv_exit_status()
                    msg = f"\nCommand exited with status {exit_status}"
                    if not onceonly:
                        msg += f", retrying in {self.config.retry_seconds}s"
                    if exit_status == 0:
                        self.status_message(msg)
                    else:
                        self.error_message(msg)

                    if onceonly:
                        return
            except OSError as e:
                self.error_message(f"\nConnection error: {str(e)}, "
                    + f"retrying in {self.config.retry_seconds}s" if onceonly else '')
            except paramiko.SSHException as e:
                self.error_message(f"\nSSH error: {str(e)}, "
                    + f"retrying in {self.config.retry_seconds}s" if onceonly else '')

            if onceonly:
                return
            time.sleep(self.config.retry_seconds)

    def draw(self, screen):
        self.gui.draw_ui(screen)

    def update(self, dt):
        if self.log_updated:
            self.log_updated = False
            sb = self.log_view.scroll_bar
            scrollAtBottom = (
                sb is None or sb.scroll_position == \
                        sb.bottom_limit - int(sb.scrollable_height * sb.visible_percentage)
            )
            scroll_position = 0 if sb is None else sb.scroll_position

            self.log_view.html_text = self.logtext
            self.log_view.rebuild()

            if self.log_view.scroll_bar:
                if scrollAtBottom:
                    self.log_view.scroll_bar.scroll_position = self.log_view.scroll_bar.bottom_limit
                else:
                    # FIXME: this isn't quite right
                    self.log_view.scroll_bar.scroll_position = scroll_position - 1
                self.log_view.scroll_bar.bottom_button.held = True
                self.log_view.scroll_bar.update(0)
                self.log_view.scroll_bar.bottom_button.held = False
                self.log_view.update(dt)
        self.gui.update(dt)

    def process_events(self, e):
        self.gui.process_events(e)
        if e.type == pygame.USEREVENT and e.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if e.ui_element in self.command_buttons.values():
                command = self.config.commands[e.ui_element.text]
                self.status_message(f">>> {command}")
                th = threading.Thread(
                    target=self.run_command_thread,
                    args=[command],
                    daemon=True
                )
                th.start()
