import re
import types
import queue

from ..LogViewer import SystemDLogViewer, DockerLogViewer

class LogViewerStatusApp():
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
        "show_service_name": None,
        "shutdown_time": 300
    }

    process_messages = []
    ui = {}

    def __init__(self, bounds, config, name):
        self.msgActionQueueFunc = queue.Queue()
        self.msgActionQueueUI = queue.Queue()

        self.LogViewerStatusConfig = config

        config.services = self.services
        config.show_service_name = False
        config.retry_seconds = 5
        config.max_scrollback = 50000
        config.command_button_h = 48
        config.command_button_margin = 2
        config.lookback = 100
        config.tail_from_start = True

        super().__init__(bounds, config, "LogViewerStatus")

        self.process_messages = [{"regex": re.compile(p['r']), **p} for p in self.process_messages]
        self.ui = {}
        self.data_updated = True


    def filter(self, text):
        # see if it's str, if not, make it one
        filtered_msgs = super().filter(text)

        out = []

        # TODO: fix where this where it gets passed to us, not where it crashes
        if type(filtered_msgs) == types.SimpleNamespace:
            filtered_msgs = [filtered_msgs]

        for filtered_msg in filtered_msgs:
            if type(filtered_msg) is str:
                msg_text = filtered_msg
            else:
                msg_text = str(filtered_msg.msg.message)

            hide_message = False

            for m in self.process_messages:
                matches = m['regex'].search(msg_text)
                if matches:
                    if 'ui' in m:
                        for i, ui_element in enumerate(m['ui']):
                            self.msgActionQueueUI.put((ui_element, matches.group(i+1)))
                    if 'func' in m:
                        self.msgActionQueueFunc.put((m['func'],filtered_msg, matches))
                    if not m.get('passthrough', False):
                        hide_message = True

            # if our filter matched a log message
            # unless that regex has passthrough=True
            # don't write to screen
            if hide_message:
                continue

            self.data_updated = True
            out.append(str(filtered_msg))

        return "\n".join(out)

    def update(self, dt):
        # run these in main thread so PyGame_Gui objects are not being altered from threads
        # as pygame's text handling doesn't seem 100% thread safe
        try:
            while True:
                ui_element, new_text = self.msgActionQueueUI.get(block=False)
                self.ui[ui_element].set_text(new_text)
        except queue.Empty:
            pass

        try:
            while True:
                func, msg, matches = self.msgActionQueueFunc.get(block=False)
                func(msg, matches)
        except queue.Empty:
            pass

        super().update(dt)


class DockerLogViewerStatusApp(LogViewerStatusApp, DockerLogViewer):
    pass

class SystemDLogViewerStatusApp(LogViewerStatusApp, SystemDLogViewer):
    pass
