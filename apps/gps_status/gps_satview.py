import math

import pygame
import pygame.gfxdraw
from pygame import surface

class gps_satview(object):
    surf = None
    sky = None

    def __init__(self, size):
        self.surf = surface.Surface(size)

    def update_data(self, data):
        self.sky = data

        self.surf.fill((0, 0, 0))
        self.surf.lock()
        for i in range(1, 200, 45):
            pygame.gfxdraw.aacircle(self.surf, 200, 200, i, (0, 255, 0))
        for i in range(0, 359, 15):
            end_x = (200*math.cos(math.radians(i)))
            end_y = (200*math.sin(math.radians(i)))
            pygame.draw.aaline(self.surf, (0, 255, 0), (200, 200), (200 + end_x, 200 + end_y), 1)

        for sat in self.sky:
            sat_x = 200 + ((sat['el']*2) * math.cos(math.radians(sat['az'])))
            sat_y = 200 + ((sat['el']*2) * math.sin(math.radians(sat['az'])))
            pygame.gfxdraw.aacircle(self.surf, int(sat_x), int(sat_y), 20, (255, 0, 0))
        self.surf.unlock()

    def draw(self, screen, coords):
        screen.blit(self.surf, coords)
