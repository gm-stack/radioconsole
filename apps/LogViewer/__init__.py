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

        self.logtext = ""
        self.log_updated = True

        self.log_view = pygame_gui.elements.UITextBox(
            html_text='',
            relative_rect=pygame.Rect(
                0, cfg.display.TOP_BAR_SIZE,
                cfg.display.DISPLAY_W,
                cfg.display.DISPLAY_H - cfg.display.TOP_BAR_SIZE
            ),
            manager=self.gui
        )

        self.backend_thread = threading.Thread(target=self.backend_loop, daemon=True)
        self.backend_thread.start()

    @staticmethod
    def esc(text):
        return html.escape(text).replace("\r\n","\n").replace("\r","\n").replace("\n", "<br>")

    def clear_console(self):
        self.logtext = ""
        self.log_updated = True

    def status_message(self, text):
        self.logtext += f"<font color='#0077FF'><b>{self.esc(text)}</b></font><br>"
        self.logtext = self.logtext[-self.config.max_scrollback:]
        self.log_updated = True

    def error_message(self, text):
        self.logtext += f"<font color='#FF0000'><b>{self.esc(text)}</b></font><br>"
        self.logtext = self.logtext[-self.config.max_scrollback:]
        self.log_updated = True

    def console_message(self, text):
        self.logtext += self.esc(text)
        self.logtext = self.logtext[-self.config.max_scrollback:]
        self.log_updated = True

    @crash_handler.monitor_thread
    def backend_loop(self):
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

                    self.status_message(f"$ {self.config.command}\n")
                    ch.exec_command(self.config.command)

                    while True:
                        out = stdout.channel.recv(1)
                        if not out:
                            break
                        else:
                            self.console_message(out.decode('UTF-8'))

                    exit_status = stdout.channel.recv_exit_status()
                    msg = f"\nCommand exited with status {exit_status}, "\
                        f"retrying in {self.config.retry_seconds}s"
                    if exit_status == 0:
                        self.status_message(msg)
                    else:
                        self.error_message(msg)

                    time.sleep(self.config.retry_seconds)
            except OSError as e:
                self.error_message(f"\nConnection error: {str(e)}, " \
                    f"retrying in {self.config.retry_seconds}s")
            except paramiko.SSHException as e:
                self.error_message(f"\nSSH error: {str(e)}, " \
                    f"retrying in {self.config.retry_seconds}s")

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
