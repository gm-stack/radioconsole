import pygame

class status_icon(object):
    def __init__(self):
        self.surface = pygame.surface.Surface((60,60), pygame.SRCALPHA)
        self.bgcolour = (0,0,0,255)
        self.font = pygame.font.Font("ttf/B612-Regular.ttf", 12)
        self.clear()
        self.read_images()
        self.overlay_icon = None
    
    def clear(self):
        self.surface.fill(self.bgcolour)

    def read_images(self):
        self.images = {
            'warning': pygame.image.load("apps/common/warning.png")
        }
        
        self.images['redalert'] = self.images['warning'].copy()
        self.images['redalert'].fill((255,0,0,255), None, pygame.BLEND_MULT)

        self.images['orangealert'] = self.images['warning'].copy()
        self.images['orangealert'].fill((255,165,0,255), None, pygame.BLEND_MULT)
    
    def update(self):
        if self.overlay_icon and self.overlay_icon in self.images:
            self.surface.blit(self.images[self.overlay_icon], (0,0))