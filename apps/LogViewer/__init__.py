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

    @crash_handler.monitor_thread
    def backend_loop(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('172.16.0.49', username='pi', port=22)

        #stdin, stdout, stderr = ssh.exec_command("journalctl -xf", get_pty=False)
        tran = ssh.get_transport()
        chan = tran.open_session()

        bufsize = -1
        stdin = chan.makefile('wb', bufsize)
        stdout = chan.makefile('rb', bufsize)
        stderr = chan.makefile_stderr('rb', bufsize)

        chan.exec_command('journalctl -xf')



        stdout_closed = False
        stderr_closed = False
        print(stdin)
        print(stdout)
        print(stderr)
        while not (stdout_closed and stderr_closed):
            r, _, _ = select.select([stdout.channel, stderr.channel], [], [])

            if stdout.channel in r:
                out = stdout.channel.recv(1)
                bytes_read = len(out)
                print(f"out {bytes_read}")
                self.logtext += f"<font color='#00FF00'>{self.escape_text(out.decode('UTF-8'))}</font>"
                self.log_updated = True
                if bytes_read == 0:
                    stdout_closed = True


            if stderr.channel in r:
                out = stderr.channel.recv(1)
                bytes_read = len(out)
                print(f"err {bytes_read}")
                self.logtext += f"<font color='#FF0000'>{self.escape_text(out.decode('UTF-8'))}</font>"
                self.log_updated = True
                if bytes_read == 0:
                    stderr_closed = True

        ss = stdout.channel.recv_exit_status()
        self.logtext += f"\n------\ndone {ss}"
        self.log_updated = True

        while True:
            time.sleep(30)

    @staticmethod
    def escape_text(text):
        return html.escape(text).replace("\r\n","\n").replace("\r","\n").replace("\n", "<br>")

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
