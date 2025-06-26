import pygame

class RotationAdaptor():
    def __init__(self, screen_dim, direction):
        self.screen_dim = screen_dim
        self.surf = pygame.surface.Surface(self.screen_dim)
        self.display = None

        self.direction = direction
        if self.direction == 'left':
            self.angle = 90
        elif self.direction == 'right':
            self.angle = -90
        elif self.direction == 'upside_down':
            self.angle = 180
        else:
            self.angle = 0

    def get_display_size(self):
        if self.direction in ('left', 'right'):
            return (self.screen_dim[1], self.screen_dim[0])
        else:
            return self.screen_dim

    def get_size(self):
        return self.screen_dim

    def set_display(self, display):
        self.display = display

    def update(self):
        rotated = pygame.transform.rotate(self.surf, self.angle)
        self.display.blit(rotated, (0,0))
        return pygame.display.update()

# 90 - left
# -90 = right
