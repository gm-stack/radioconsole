import json
import datetime
from types import SimpleNamespace

from . import LogViewer

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
        "show_service_name": None
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
        start_timestamp = None
        if len(start_timestamps_running) != 0:
            start_timestamp = start_timestamps_running[0]

        service_flags = " ".join([f"-u {s}.service" for s in self.config.services])

        # if service running, tail from start
        if start_timestamp:
            command = f"journalctl -f {service_flags} --since '{start_timestamp}' --output json"
        else:
            command = f"journalctl -f {service_flags} -n '{self.config.lookback}' --output json"

        self.status_message(f"\n---\n>>> {command}\n")

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