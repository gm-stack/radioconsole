import json
import datetime
import select
from types import SimpleNamespace

from . import LogViewer

class SystemDLogViewer(LogViewer):
    default_config = {
        "port": 22,
        "username": "pi",
        "lookback": 100,
        "retry_seconds": 5,
        "max_scrollback": 50000,
        "command_button_h": 48,
        "command_buttons_x": 0,
        "command_button_margin": 2,
        "filter_lines": [],
        "commands": [],
        "show_service_name": None,
        "tail_from_start": False
    }

    def __init__(self, bounds, config, name):
        config.command = 'cat' # not actually used, see below

        # if show_service_name set, use it
        # else default to only showing service name if >1 service
        if config.show_service_name in (True, False):
            self.show_service_name = config.show_service_name
        else:
            self.show_service_name = (len(config.services) > 1)

        super().__init__(bounds, config, name)

    def run_tail_command(self, ts, command):
        self.status_message(f"tail systemd logs for {self.config.services}")

        start_timestamp = None
        service_flags = " ".join([f"-u {s}.service" for s in self.config.services])

        if self.config.tail_from_start:
            # for all the services see if they are running
            # if running, get the time they started
            start_timestamps = [
                self.run_command(ts,
                    f"systemctl is-active --quiet '{service}' &&" \
                    f"TZ=UTC systemctl show --property=ActiveEnterTimestamp --value '{service}'"
                )
                for service in self.config.services
            ]

            # Parse the timestamps and sort, earliest first.
            # Discard non-running services.
            start_timestamps_running = sorted([
                datetime.datetime.strptime(t, "%a %Y-%m-%d %H:%M:%S %Z")
                for t in start_timestamps if t != ''
            ])

            # if any service running, pick earliest start time to start tailing from
            if len(start_timestamps_running) != 0:
                start_timestamp = start_timestamps_running[0]

            # if service running, tail from start
        if start_timestamp:
            command = f"journalctl -f {service_flags} --since '{start_timestamp}' --output json"
        else:
            command = f"journalctl -f {service_flags} -n '{self.config.lookback}' --output json"

        self.status_message(f"\n---\n>>> {command}\n")

        ch = ts.open_session()
        ch.exec_command(command)
        stdout = ch.makefile()
        stderr = ch.makefile_stderr()

        buffers = {}
        buffers['stdout'] = bytes()
        buffers['stderr'] = bytes()

        def recv_for_and_parse_newlines(ch, buffer):
            if buffer == 'stdout':
                out = ch.recv(8192)
            else:
                out = ch.recv_stderr(8192)

            if not out:
                print("not out")
                return False

            buffers[buffer] += out
            ends_newline = (buffers[buffer][-1] == '\n')
            lines = buffers[buffer].splitlines()

            if ends_newline: # if it ended exacly in a newline, start again
                buffers[buffer] = bytes()
                all_lines = lines
            else: # otherwise keep the remaining bit of the last line
                buffers[buffer] = lines[-1]
                all_lines = lines[:-1]

            # now decode all the lines
            for line in all_lines:
                read_line = line.decode('UTF-8')
                self.console_message(read_line, is_stderr=(buffer == 'stderr'))
            return True

        buffer = bytes()
        while True:
            r,w,e = select.select([ch],[],[ch], 1.0)
            if ch in r:
                if ch.recv_ready():
                    if not recv_for_and_parse_newlines(ch, 'stdout'):
                        break
                if ch.recv_stderr_ready():
                    if not recv_for_and_parse_newlines(ch, 'stderr'):
                        break

                if ch in e:
                    self.error_message("fd entered error list")
                    ch.close()
                    return
                else:
                    ts.send_ignore()

        exit_status = ch.recv_exit_status()
        msg = f"\nCommand exited with status {exit_status}\n"
        msg += f"Retrying in {self.logviewer_config.retry_seconds}s\n"
        if exit_status == 0:
            self.status_message(msg)
        else:
            self.error_message(msg)

        self.data_updated = True

    def filter(self, json_text):
        out_msg = SystemDLogMessage(json_text, self.show_service_name)
        # don't return actual out_msg, we want the JSON version if unfiltered
        if super().filter(str(out_msg)):
            return out_msg

    def update(self, dt):
        return super().update(dt)

    def draw(self, screen):
        return super().draw(screen)

    def process_events(self, e):
        super().process_events(e)


class SystemDLogMessage(object):
    def __init__(self, msg, show_service_name):
        self.show_service_name = show_service_name
        self.msg_json = msg

        try:
            j = json.loads(self.msg_json).items()
        except json.JSONDecodeError as e:
            self.msg = SimpleNamespace(message=f"{str(e)}\n{self.msg_json}")
            self.timestamp = datetime.datetime.utcnow()
            self.timestamp_str = ""
            self.syslog_id = ""
            return

        def remove_prefix(text, prefix):
            if text.startswith(prefix):
                return text[len(prefix):]
            return text

        self.msg = SimpleNamespace(
            # remove __ from keys that start with it as it interfeces with SimpleNamespace
            **{remove_prefix(key, "__").lower(): value for key,value in j}
        )

        self.timestamp = datetime.datetime.fromtimestamp(int(self.msg.realtime_timestamp) / 1000000)

        if self.timestamp.date() == datetime.date.today():
            self.timestamp_str = self.timestamp.strftime("%H:%M:%S")
        else:
            self.timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        if self.show_service_name:
            self.syslog_id = f" {self.msg.syslog_identifier}[{self.msg._pid}]"
        else:
            self.syslog_id = ""

    # str version that ends up on terminal
    def __str__(self):
        return f"{self.timestamp_str}{self.syslog_id}: {self.msg.message}\n"