import math
import re
import select
import multiprocessing
import queue
import time

import pygame
import pygame_gui

from ..common import TerminalView, SSHBackgroundThreadApp
from util import rc_button

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

        self.additional_command_queue = multiprocessing.Queue()

        self.command_buttons = {}

        if config.command_buttons_x == 0:
            config.command_buttons_x = len(self.config.commands)

        def createCommandButton(command_name):
            total_padding = (config.command_buttons_x + 1) * config.command_button_margin
            button_w = (bounds.w - total_padding) // config.command_buttons_x
            button_num = len(self.command_buttons)
            button_col = button_num % config.command_buttons_x
            button_row = button_num // config.command_buttons_x

            self.command_buttons[command_name] = rc_button(
                relative_rect=pygame.Rect(
                    bounds.x + config.command_button_margin + ((button_w + config.command_button_margin) * button_col),
                    (bounds.y + bounds.h) - config.command_button_margin -
                        ((config.command_button_h + config.command_button_margin) * (button_row + 1)),
                    button_w,
                    config.command_button_h
                ),
                text=command_name,
                manager=self.gui,
                object_id="#command_button_grey"
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
                return
        return msg

    def status_message(self, text):
        self.terminal_view.write(text, colour='cyan')
        self.data_updated = True

    def handle_error(self, host, text):
        self.error_message(text)

    def error_message(self, text):
        self.terminal_view.write(text + "\n", colour='red')
        self.data_updated = True

    def console_message(self, text, is_stderr=False):

        def do_console_write(filtered, is_stderr):
            if is_stderr:
                colour = 'red'
            else:
                colour = 'white'

            if filtered:
                self.terminal_view.write(str(filtered), colour=colour)
                self.data_updated = True

        filtered = self.filter(text)
        if type(filtered) is list:
            for msg in filtered:
                do_console_write(msg, is_stderr)
            return
        do_console_write(filtered, is_stderr)



    def console_message_onceonly(self, text):
        self.terminal_view.write(text, colour='brightwhite')
        self.data_updated = True

    def set_tail_command(self, command):
        if command == self.prev_tail_command:
            return
        self.prev_tail_command = command

        self.run_ssh_func_persistent(
            self.config,
            "tail",
            self.run_tail_command,
            self.handle_error,
            command
        )


    def run_tail_command(self, ts, command):
        self.status_message(f"\n---\n>>> {command}\n")

        main_channel = ts.open_session()
        main_channel.exec_command(command)

        more_cmd = self.additional_command_queue._reader
        extra_channel_fds = []
        extra_channel_ui_name = {}

        buffers = {}
        buffers['stdout'] = bytes()
        buffers['stderr'] = bytes()

        def recv_for_and_parse_newlines(channel, buffer, readStdErr=False, isConsole=True):

            if readStdErr:
                out = channel.recv_stderr(8192)
            else:
                out = channel.recv(8192)

            input_closed = False
            if not out:
                input_closed = True

            buffers[buffer] += out

            all_lines = []
            while True:
                newline_pos = buffers[buffer].find(b'\n')
                if newline_pos == -1:
                    break
                all_lines.append(buffers[buffer][:newline_pos + 1])
                buffers[buffer] = buffers[buffer][newline_pos + 1:]

            if input_closed:
                # if that's all, include what remains
                all_lines += [buffers[buffer]]

            # now decode all the lines
            for line in all_lines:
                read_line = line.decode('UTF-8')
                if isConsole:
                    self.console_message(read_line, is_stderr=(buffer == 'stderr'))
                else:
                    self.console_message_onceonly(read_line)

            if input_closed:
                if channel.exit_status_ready():
                    exit_status = channel.recv_exit_status()
                    msg = f"\nCommand exited with status {exit_status}\n"
                    if exit_status == 0:
                        self.console_message_onceonly(msg)
                    else:
                        self.error_message(msg)
                else:
                    return True # try again to get input status
                return False
            return True

        while True:
            select_array = [main_channel, more_cmd] + extra_channel_fds
            r,_,e = select.select(select_array,[],select_array, 15.0)

            if not ts.is_active():
                self.error_message("SSH connection closed\n")
                self.ssh_connection_issue = True
                self.data_updated = True
                return

            if main_channel in r:
                if main_channel.recv_ready():
                    if not recv_for_and_parse_newlines(main_channel, 'stdout', readStdErr=False):
                        break
                if main_channel.recv_stderr_ready():
                    if not recv_for_and_parse_newlines(main_channel, 'stderr', readStdErr=True):
                        break

            for cmd_fd in extra_channel_fds:
                if cmd_fd.recv_ready() or cmd_fd.exit_status_ready():
                    if not recv_for_and_parse_newlines(cmd_fd, f"cmd_{cmd_fd.fileno()}", isConsole=False):
                        cmd_fd.close()
                        del buffers[command_name]
                        extra_channel_fds.remove(cmd_fd)
                        [ button.set_id("#command_button_grey")
                            for button in self.command_buttons.values()
                            if button.text == extra_channel_ui_name[cmd_fd] ]
                        del extra_channel_ui_name[cmd_fd]

            if e:
                print(f"fd {e} entered error list")
                self.error_message(f"fd {e} entered error list")
                main_channel.close()
                return

            if more_cmd in r:
                while True:
                    try:
                        extra_command, ui_element_name = self.additional_command_queue.get_nowait()
                        ch2 = ts.open_session()
                        ch2.set_combine_stderr(True)
                        ch2.exec_command(extra_command)
                        extra_channel_fds += [ch2]
                        extra_channel_ui_name[ch2] = ui_element_name
                        command_name = f"cmd_{ch2.fileno()}"
                        buffers[command_name] = bytes()
                    except queue.Empty:
                        print("queue read, continuing")
                        break

            if not r and not e:
                # nothing to select()
                # send some data to check connection's alive
                ts.send_ignore()

        self.status_msg(f"Retrying in {self.logviewer_config.retry_seconds}s\n")

        self.data_updated = True

    def run_button_command(self, command, ui_element):
        ui_element.set_id("#command_button_selected")
        self.status_message(f"\n---\n>>> {command}\n")
        self.additional_command_queue.put((command, ui_element.text))

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
                self.run_button_command(command, e.ui_element)