class app(object):
    config = None
    bounds = None
    display = None

    def __init__(self, bounds, config, display):
        self.config = config
        self.bounds = bounds
        self.display = display

    def draw(self, screen):
        raise NotImplementedError()

    def update(self, dt):
        raise NotImplementedError()

    def process_events(self, e):
        raise NotImplementedError()
