import math

import random
import pygame
import pygame.gfxdraw
import pygame.math
from pygame import surface
from ..common.IconManager import radioconsole_icons
import fonts
from collections import defaultdict

class usb_bus_view(object):
    surf = None

    box_w = 180
    box_h = 56

    box_margin_h = 12
    box_total_h = box_h + box_margin_h

    box_margin_w = 40
    box_total_w = box_w + box_margin_w


    def __init__(self, bounds):
        self.font = fonts.get_font("B612", "Regular", 14)
        self.bigfont = fonts.get_font("B612", "Regular", 24)
        self.bounds = bounds
        self.surf = surface.Surface(self.bounds.size)
        self.data = {}

    def update_data(self, data):
        self.data = data

    def draw_data(self):
        xloc = self.box_margin_w // 2
        yloc = self.box_margin_h

        column_bottom = defaultdict(lambda: int(self.box_margin_h))

        def draw_box(data, xloc, yloc, parent_bounds=None):
            product_text = self.font.render(data['product'], True, (0x00, 0xFF, 0x00))


            second_line = data['serial'] if data['serial'] else data['manufacturer']
            serial_text = self.font.render(second_line, True, (0x00, 0xFF, 0x00))

            vid_pid = self.font.render(f"{data['vid']}:{data['pid']}", True, (0x00, 0xFF, 0x00))

            bounds = pygame.Rect(xloc, yloc, max(self.box_w, product_text.get_width() + self.box_margin_w), self.box_h)

            loc = product_text.get_rect(midtop=bounds.midtop)
            self.surf.blit(product_text, loc.topleft)

            loc = serial_text.get_rect(midtop=(bounds.move(0,16).midtop))
            self.surf.blit(serial_text, loc.topleft)

            loc = vid_pid.get_rect(bottomleft=bounds.bottomleft)
            self.surf.blit(vid_pid, loc.topleft)

            pygame.gfxdraw.aapolygon(
                self.surf,
                (
                    bounds.topleft,
                    bounds.topright,
                    bounds.bottomright,
                    bounds.bottomleft
                ),
                (0x00, 0xFF, 0x00)
            )

            if parent_bounds:
                if bounds.x == parent_bounds.x:
                    pygame.draw.aaline(self.surf, (0x00, 0xFF, 0x00), parent_bounds.midbottom, bounds.midtop)
                else:
                    left_point = parent_bounds.midright
                    right_point = bounds.midleft
                    mid_x = (left_point[0] + right_point[0]) // 2
                    pygame.draw.aalines(
                        self.surf,
                        (0x00, 0xFF, 0x00),
                        False,
                        (
                            left_point,
                            (mid_x, left_point[1]),
                            (mid_x, right_point[1]),
                            right_point)
                    )

            num_children = len(data['children'])
            if num_children == 1:
                column_bottom[xloc] += self.box_total_h
                draw_box(data['children'][0], xloc, column_bottom[xloc], bounds)
                return 0

            elif num_children > 0:
                xloc += self.box_total_w
                if column_bottom[xloc] == 0:
                    column_bottom[xloc] = self.box_margin_h
                #    #column_bottom[xloc] = yloc - self.box_total_h # start tree one box up

                for child in data['children']:
                    column_bottom[xloc] += draw_box(child, xloc, column_bottom[xloc], bounds)
                    column_bottom[xloc] += self.box_total_h

                return (self.box_total_h) * (len(data['children']) - 2)
                #column_bottom[xloc] += self.box_total_h

            return 0



        def do_draw(data):
            nonlocal xloc, yloc
            draw_box(data, xloc, yloc)

        do_draw(self.data)


    def draw(self, screen):
        self.surf.fill((0x00, 0x00, 0x00))
        self.draw_data()
        screen.blit(self.surf, self.bounds.topleft)