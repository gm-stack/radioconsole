import json
from . import LogViewer

class SystemDLogViewer(LogViewer):
    default_config = {
        "retry_seconds": 5,
        "max_scrollback": 50000,
        "command_button_h": 48,
        "command_buttons_x": 0,
        "command_button_margin": 2,
        "filter_lines": [],
        "commands": []
    }

    def __init__(self, bounds, config, name):
        
        config.command = "journalctl -f -n 100 --output json " \
            + " ".join([f"-u {s}.service" for s in config.services])
        
        super().__init__(bounds, config, name)
    
    def filter(self, text):
        log_msg = json.loads(text)
        out_msg = log_msg['MESSAGE'] + "\n"
        return super().filter(out_msg)

    def update(self, dt):
        return super().update(dt)

    def draw(self, screen):
        return super().draw(screen)

    def process_events(self, e):
        super().process_events(e)