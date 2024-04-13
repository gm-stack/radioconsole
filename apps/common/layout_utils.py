import pygame

def split_rect_horz(rect, num):
    total_w = rect.w
    x_offset = rect.x
    x_coords = [int(float(rect.w) / num * i) for i in range(num)] + [total_w]
    x1_x2 = list(zip(x_coords, x_coords[1:]))
    x_w = [(x_offset+x1, x2-x1) for x1, x2 in x1_x2]
    return [pygame.Rect(x, rect.y, w, rect.h) for x, w in x_w]