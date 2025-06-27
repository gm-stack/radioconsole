import pygame

def object_layout(height, min_width, screen_width, num_objects):
    # number of objects that could fit
    max_objects = screen_width // min_width

    # number of rows
    # minus signs used to do ceiling division
    rows = -(num_objects // -max_objects)

    # width of each
    object_width = screen_width // max_objects

    # centre the blocks of objects by dividing whitespace on either side
    x_offset = (screen_width - (max_objects * object_width)) // 2

    # Calculate the coordinates of each object
    objects = []
    for row in range(rows):
        for col in range(max_objects):
            # don't fill out full row if we have enough objects
            if len(objects) >= num_objects:
                return objects, rows
            x = (col * object_width) + x_offset
            y = row * height
            w = object_width
            h = height
            objects.append(pygame.Rect(x, y, w, h))

    return objects, rows
