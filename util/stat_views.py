import pygame_gui
import pygame

from . import timegraph

class stat_display(pygame_gui.elements.ui_label.UILabel):
    def __init__(self, *args, **kwargs):
        kwargs['object_id'] = '#param_value'
        super().__init__(*args, **kwargs)

class stat_label(pygame_gui.elements.ui_label.UILabel):
    def __init__(self, *args, **kwargs):
        kwargs['object_id'] = '#param_label'
        super().__init__(*args, **kwargs)

class stat_view(object):
    def __init__(self, relative_rect, name, manager, label_s=None, split='lr', colourmap={}, colourmap_mode=None, unit=''):
        self.colourmap = colourmap
        self.colourmap_mode = colourmap_mode
        
        if colourmap_mode == 'gt':
            self.colourmap_list = [k for k in list(colourmap.keys()) if k is not None]
            self.colourmap_list.sort(reverse=True)

        self.unit = unit

        rr = relative_rect
        self.has_label = True
        if split == 'lr':
            hw = label_s if label_s else int(rr.width / 2)
            label_rect = pygame.Rect(rr.x, rr.y, hw, rr.height)
            value_rect = pygame.Rect(rr.x + hw, rr.y, rr.width - hw, rr.height)
        elif split == 'tb':
            hh = label_s if label_s else int(rr.height / 2)
            label_rect = pygame.Rect(rr.x, rr.y, rr.width, hh)
            value_rect = pygame.Rect(rr.x, rr.y + hh, rr.width, rr.height - hh)
        elif split == 'no_label':
            value_rect = pygame.Rect(rr.x, rr.y, rr.width, rr.height)
            self.has_label = False
        else:
            raise ValueError("split must be 'lr', 'tb' or 'no_label'")

        if self.has_label:
            self.label = stat_label(
                relative_rect=label_rect,
                text=name,
                manager=manager
            )
        self.value = stat_display(
            relative_rect=value_rect,
            text='',
            manager=manager
        )

    def set_text(self, text):
        self.value.set_text(text)
        if self.colourmap_mode == 'equals':
            if text in self.colourmap:
                self.set_text_colour(self.colourmap[text])
            elif None in self.colourmap:
                self.set_text_colour(self.colourmap[None])

    def update(self, value):
        if isinstance(value, int):
            self.set_text(f"{value:d}{self.unit}")
        if isinstance(value, float):
            self.text_colour_from_colourmap(value)
            self.set_text(f"{value:.1f}{self.unit}")
        if isinstance(value, str):
            self.set_text(value)
    
    def text_colour_from_colourmap(self, value):
        if self.colourmap_mode == 'gt':
            cmaps = [x for x in self.colourmap_list if value > x]
            if cmaps:
                self.set_text_colour(self.colourmap[cmaps[0]])
            elif None in self.colourmap:
                self.set_text_colour(self.colourmap[None])

    def set_text_colour(self, colour):
        if self.value.text_colour != colour:
            self.value.text_colour = colour
            self.value.rebuild()

class stat_view_graph(object):
    def __init__(self, relative_rect, text_w, name, manager, colourmap={}, colourmap_mode=None, unit='', min_value=None, max_value=None, label_s=None):
        rr = relative_rect
        stat_view_rect = pygame.Rect(rr.x, rr.y, text_w, rr.height)
        graph_rect = pygame.Rect(rr.x + text_w, rr.y, rr.width - text_w, rr.height)

        self.stat_view = stat_view(
            relative_rect=stat_view_rect,
            name=name,
            manager=manager,
            split='lr',
            colourmap=colourmap,
            colourmap_mode=colourmap_mode,
            unit=unit,
            label_s=label_s
        )

        self.graph = timegraph(
            rect=graph_rect,
            min_value=min_value,
            max_value=max_value
        )

    def update(self, value, display_value=None):
        if display_value is not None:
            self.stat_view.update(display_value)
        else:
            self.stat_view.update(value)

        if isinstance(value, float) or isinstance(value, int):
            self.graph.datapoint(value)

    def draw(self, screen):
        return self.graph.draw(screen)