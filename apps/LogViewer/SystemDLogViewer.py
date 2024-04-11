import json
import datetime
from types import SimpleNamespace

from . import LogViewer

class SystemDLogMessage(object):
    def __init__(self, msg, show_service_name):
        self.show_service_name = show_service_name
        self.msg_json = msg
        self.msg = SimpleNamespace(
            # remove __ from keys that start with it as it interfeces with SimpleNamespace
            **{key.removeprefix("__").lower(): value for key,value in json.loads(self.msg_json).items()}
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
        config.command = "journalctl -f -n 100 --output json " \
            + " ".join([f"-u {s}.service" for s in config.services])

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