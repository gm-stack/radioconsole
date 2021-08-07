import pygame
from pygame import surface
import pygame_gui

class TerminalView():
    COLOURS = {
        'black': (0, 0, 0),
        'red': (205, 0, 0),
        'green': (0, 205, 0),
        'yellow': (205, 205, 0),
        'blue': (0, 0, 238),
        'magenta': (205, 0, 205),
        'cyan': (0, 205, 205),
        'white': (229, 229, 229),
        'grey': (127, 127, 127),
        'brightred': (255, 0, 0),
        'brightgreen': (0, 255, 0),
        'brightyellow': (255, 255, 0),
        'brightblue': (92, 92, 255),
        'brightmagenta': (255, 0, 255),
        'brightcyan': (0, 255, 255),
        'brightwhite': (255, 255, 255)
    }

    def __init__(self, width, height, x, y):
        self.W = width
        self.H = height
        self.X = x
        self.Y = y

        self.terminal_x = 0
        self.terminal_y = 0

        self.text_surf = surface.Surface((self.W, self.H))
        self.text_surf.fill((0, 0, 0))

        self.default_colour = 'white'
        self.current_colour = self.default_colour
        self.precache_font()

        self.terminal_w = int(self.W / self.char_w)
        self.terminal_h = int(self.H / self.char_h)
        print(f"term init as {self.terminal_w}x{self.terminal_h}, {self.char_w}x{self.char_h} font")

    def render_char(self, char, colour):
        font = pygame.font.Font("ttf/FiraCode-Regular.ttf", 14)
        text = font.render(char, True, colour)
        return text

    def render_char_colours(self, char):
        return {cname : self.render_char(char, cval) for cname, cval in self.COLOURS.items()}

    def precache_font(self):
        charlist = [chr(x) for x in range(32,128)]
        self.precache_list = {x : self.render_char_colours(x) for x in charlist}


        self.char_w = max([x[self.default_colour].get_width() for x in self.precache_list.values()])
        self.char_h = max([x[self.default_colour].get_height() for x in self.precache_list.values()])

    def write(self, text, colour=None):
        def newline():
            self.terminal_x = 0
            self.terminal_y += 1

            if self.terminal_y == self.terminal_h: # we just newlined off the bottom, scroll the screen
                self.terminal_y -= 1
                self.text_surf.scroll(0,-self.char_h)
                self.text_surf.fill((0, 0, 0), rect=(0, (self.terminal_h - 1) * self.char_h, self.W, self.char_h))

        if colour:
            self.current_colour = colour
        for char in text:
            a = ord(char)
            if a >= 32 and a < 128: # text char
                glyph = self.precache_list[char][self.current_colour]
                self.text_surf.blit(glyph, (self.terminal_x * self.char_w, self.terminal_y * self.char_h))
                self.terminal_x += 1
                if self.terminal_x == self.terminal_w:
                    newline()
            elif a == 9: # \t
                self.terminal_x += 2
            elif a == 10: # \n
                newline()
            else:
                print(f"unknown control char {a}")



    def draw(self, display):
        display.blit(self.text_surf, (self.X, self.Y), area=(0, 0, self.W, self.H))