import os

import pygame
import fonts

base_path = os.path.dirname(__file__)

class splash_screen():
    LOGO_OFFSET = (-5,-25)
    FONT = None


    def __init__(self, screen):
        self.screen = screen
        self.screen_size = screen.get_size()
        self.FONT = fonts.get_font("B612", "Regular", 14)

    def draw_splash(self):
        logo = pygame.image.load(os.path.join(base_path, "logo.png"))
        logo_size = logo.get_size()
        self.screen.blit(
            logo,
            ((self.screen_size[0] - logo_size[0])/2 + self.LOGO_OFFSET[0],
            (self.screen_size[1] - logo_size[1])/2 + self.LOGO_OFFSET[1])
        )
        pygame.display.update()

    def update_status(self, msg):
        text = self.FONT.render(msg, True, (255, 255, 255))
        text_size = text.get_size()
        pygame.draw.rect(self.screen, (0, 0, 0),
        (
            0, self.screen_size[1] - text_size[1],
            self.screen_size[0], text_size[1]
        ))

        self.screen.blit(
            text,
            ((self.screen_size[0] - text_size[0]) / 2,
            self.screen_size[1] - text_size[1])
        )
        pygame.display.update()