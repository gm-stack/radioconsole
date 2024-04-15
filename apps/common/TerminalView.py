from pygame import surface

import fonts

FONT_CACHE=None

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

    def __init__(self, bounds, name=""):
        self.name = name
        self.default_colour = 'white'
        self.precache_font()
        self.set_bounds(bounds)
        self.delayed_newline = False

    def set_bounds(self, bounds):
        self.bounds = bounds

        self.terminal_x = 0
        self.terminal_y = 0

        self.text_surf = surface.Surface(self.bounds.size)
        self.text_surf.fill((0, 0, 0))

        self.current_colour = self.default_colour

        self.terminal_w = int(self.bounds.w / self.char_w)
        self.terminal_h = int(self.bounds.h / self.char_h)


    def render_char(self, char, colour):
        font = fonts.get_font("B612Mono", "Regular", 14)
        text = font.render(char, True, colour)
        return text

    def render_char_colours(self, char):
        return {cname : self.render_char(char, cval) for cname, cval in self.COLOURS.items()}

    def precache_font(self):
        global FONT_CACHE
        if not FONT_CACHE:
            charlist = [chr(x) for x in range(32,128)]
            self.precache_list = {x : self.render_char_colours(x) for x in charlist}

            self.char_w = max([x[self.default_colour].get_width() for x in self.precache_list.values()])
            self.char_h = max([x[self.default_colour].get_height() for x in self.precache_list.values()])
            FONT_CACHE = (self.precache_list, self.char_w, self.char_h)
        else:
            self.precache_list, self.char_w, self.char_h = FONT_CACHE


    def write(self, text, colour=None):
        def newline():
            self.terminal_x = 0
            self.terminal_y += 1

            if self.terminal_y == self.terminal_h: # we just newlined off the bottom, scroll the screen
                self.terminal_y -= 1
                self.text_surf.scroll(0,-self.char_h)
                self.text_surf.fill((0, 0, 0), rect=(0, (self.terminal_h - 1) * self.char_h, self.bounds.w, self.char_h))

        if colour:
            self.current_colour = colour
        for char in text:
            if self.delayed_newline:
                newline()
                self.delayed_newline = False
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
                # if another newline pending, do one now
                if self.delayed_newline:
                    newline()
                # set delayed_newline - don't actually newline until there's something on that line
                # otherwise the bottom line is just always wasted.
                self.delayed_newline = True
            else:
                print(f"{self.name}: unknown control char {a}")



    def draw(self, display):
        # todo: work out actual dirty rect
        display.blit(self.text_surf, (self.bounds.x, self.bounds.y), area=(0, 0, self.bounds.w, self.bounds.h))