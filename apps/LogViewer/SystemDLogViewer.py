from . import LogViewer

class SystemDLogViewer(LogViewer):
    def __init__(self, bounds, config, display, name):
        super().__init__(bounds, config, display, name)
    
    def display_filter():
        return ""

    def update(self, dt):
        return super().update(dt)

    def draw(self, screen):
        return super().draw(screen)

    def process_events(self, e):
        super().process_events(e)