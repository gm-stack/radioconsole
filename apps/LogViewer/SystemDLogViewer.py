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

        self.msg = SimpleNamespace(
            # remove __ from keys that start with it as it interfeces with SimpleNamespace
            **{key.removeprefix("__").lower(): value for key,value in j}
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
    lookback = None

    def __init__(self, bounds, config, name):

        service_starts = "\n".join([f"$(service_start_time {s})" for s in config.services])
        service_flags = " ".join([f"-u {s}.service" for s in config.services])

        # get earliest start of any function called to get all logs since service start
        config.command = f"""bash -c 'function service_start_time() {{
    systemctl is-active --quiet "$1" && systemctl show --property=ActiveEnterTimestamp --value "$1" | cut -c 5-
}}
service_start_time="{service_starts}"
start_time="$(echo "$service_start_time" | grep -v -e ^$ | sort | head -n 1)"
journalctl -f {service_flags} --since "$start_time" --output json'
"""
        # if set, use it, else default to only showing service name if >1 service
        if config.show_service_name in (True, False):
            self.show_service_name = config.show_service_name
        else:
            self.show_service_name = (len(config.services) > 1)

        super().__init__(bounds, config, name)

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