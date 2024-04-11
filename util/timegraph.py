import pygame
from pygame import surface

class timegraph(object):
    def __init__(self, rect, max_value=None, min_value=None):
        self.bounds = rect
        self.surface = surface.Surface((rect.width, rect.height))
        self.data = []
        self.min_value = max_value
        self.max_value = min_value
        self.redraw()

    def datapoint(self, data):
        d = float(data)
        self.data.append(d)
        if len(self.data) > self.bounds.width:
            del self.data[0]

        extents_updated = False

        if self.min_value is None or d < self.min_value:
            self.min_value = d
            extents_updated = True

        if self.max_value is None or d > self.max_value:
            self.max_value = d
            extents_updated = True

        #if extents_updated:
        self.redraw()

    def redraw(self):
        self.surface.fill((0x11,0x18,0x1d))
        if not self.max_value and not self.min_value:
            return

        if self.max_value == self.min_value:
            scale = self.min_value
            offset = 0
        else:
            scale = (self.max_value - self.min_value)
            offset = self.min_value

        for x, d in enumerate(self.data):
            h = ((d - offset) / scale) * (self.bounds.height - 2)
            startpos = (x, self.bounds.height - 1)
            endpos = (x, self.bounds.height - (int(h) - 2))
            pygame.draw.line(self.surface, (0, 255, 0), startpos, endpos)


    def draw(self, screen):
        screen.blit(self.surface, self.bounds.topleft)

