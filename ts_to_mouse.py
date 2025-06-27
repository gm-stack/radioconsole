import pygame

EVENT_MAPPINGS = {
    pygame.FINGERDOWN: pygame.MOUSEBUTTONDOWN,
    pygame.FINGERMOTION: pygame.MOUSEMOTION,
    pygame.FINGERUP: pygame.MOUSEBUTTONUP
}

class TouchEventAdaptor():
    def __init__(self, screen_dim, angle):
        self.screen_dim = screen_dim
        self.angle = angle

    def convert(self, e):
        if e.type not in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            return False

        x = e.x
        y = e.y

        # rotate touches if screen rotated
        if self.angle == -90:
            x,y = y,x
            y = 1.0 - y
        elif self.angle == 90:
            x,y = y,x
            x = 1.0 - x
        elif self.angle == 180:
            x = 1.0 - x
            y = 1.0 - y

        event = pygame.event.Event(
            EVENT_MAPPINGS[e.type],
            pos=(
                x * self.screen_dim[0],
                y * self.screen_dim[1]
            ),
            button=1
        )

        pygame.event.post(event)
        return True

