import json
import datetime

from . import LogViewer

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
    
    def filter(self, text):
        log_msg = json.loads(text)

        timestamp = datetime.datetime.fromtimestamp(int(log_msg['__REALTIME_TIMESTAMP']) / 1000000)
        if timestamp.date() == datetime.date.today():
            date_fmt = timestamp.strftime("%H:%M:%S")
        else:
            date_fmt = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        if self.show_service_name:
            syslog_id = f" {log_msg['SYSLOG_IDENTIFIER']}[{log_msg['_PID']}]"
        else:
            syslog_id = ""


        out_msg = f"{date_fmt}{syslog_id}: {log_msg['MESSAGE']}\n"
        
        return super().filter(out_msg)

    def update(self, dt):
        return super().update(dt)

    def draw(self, screen):
        return super().draw(screen)

    def process_events(self, e):
        super().process_events(e)