import threading
import pygame
import pygame_gui
import gps

import crash_handler
from config_reader import cfg
from AppManager.app import app
from .gps_satview import gps_satview

class gps_status(app):
    gps_data = {}
    ui_element_labels = {}
    ui_element_values = {
        'TPV': {}
    }
    gps_satview = None

    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)

        self.backend_thread = threading.Thread(target=self.backend_loop, daemon=True)
        self.backend_thread.start()

        self.gps_satview = gps_satview((400, 400))

        y = display.TOP_BAR_SIZE

        self.ui_element_values['TPV']['lat'] = pygame_gui.elements.ui_label.UILabel(
            relative_rect=pygame.Rect(0, y, 128, 32),
            text='',
            manager=self.gui
        )
        self.ui_element_values['TPV']['lon'] = pygame_gui.elements.ui_label.UILabel(
            relative_rect=pygame.Rect(128, y, 128, 32),
            text='',
            manager=self.gui
        )

        self.ui_element_values['TPV']['alt'] = pygame_gui.elements.ui_label.UILabel(
            relative_rect=pygame.Rect(256, y, 128, 32),
            text='',
            manager=self.gui
        )

    @crash_handler.monitor_thread
    def backend_loop(self):
        gpsd = gps.gps(mode=gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE)
        while True:
            report = gpsd.next()
            self.gps_data[report['class']] = report
            self.data_updated = True

    def draw(self, screen):
        if super().draw(screen):
            self.gps_satview.draw(screen, (400, self.display.TOP_BAR_SIZE))
            return True
        return False

    def update(self, dt):
        if self.data_updated:
            for update_class, guis in self.ui_element_values.items():
                for key, gui in guis.items():
                    gui.set_text(str(self.gps_data.get(update_class, {}).get(key, '')))
            if 'SKY' in self.gps_data:
                self.gps_satview.update_data(self.gps_data['SKY'].get('satellites', []))
        super().update(dt)
