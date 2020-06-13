import pygame

class TopBar(object):
    def __init__(self, bounds):
        self.X, self.Y, self.W, self.H = bounds

    def draw(self, screen):
        pygame.draw.rect(screen, (64, 64, 64), (self.X, self.Y, self.W, self.H))

    def keydown(self, k, m):
        return False