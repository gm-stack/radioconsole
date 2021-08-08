import threading
import pygame
import pygame_gui
import time
import gps

import crash_handler
from config_reader import cfg
from AppManager.app import app
from .gps_satview import gps_satview
from util import timegraph, stat_display, stat_label, stat_view, stat_view_graph, extract_number

class gps_status(app):
    gps_data = {}
    ui_element_labels = {}
    ui_element_values = {}
    ui_element_graphs = {}
    gps_satview = None

    def __init__(self, bounds, config, display):
        super().__init__(bounds, config, display)

        self.backend_thread = threading.Thread(target=self.backend_loop, daemon=True)
        self.backend_thread.start()

        self.gps_satview = gps_satview((400, 400))

        y = display.TOP_BAR_SIZE


        self.ui_element_values['status'] = stat_label(
            relative_rect=pygame.Rect(0, y, 800, 32),
            text='gps name goes here', manager=self.gui
        )
        y += 32

        self.ui_element_values['lat'] = stat_view(
            relative_rect=pygame.Rect(0, y, 96, 64),
            name='lat',
            manager=self.gui,
            split='tb'
        )
        self.ui_element_values['lon'] = stat_view(
            relative_rect=pygame.Rect(96, y, 96, 64),
            name='lon',
            manager=self.gui,
            split='tb'
        )
        self.ui_element_values['alt'] = stat_view(
            relative_rect=pygame.Rect(192, y, 64, 64),
            name='alt',
            manager=self.gui,
            split='tb'
        )
        self.ui_element_values['trk'] = stat_view(
            relative_rect=pygame.Rect(256, y, 48, 64),
            split='tb',
            name='trk',
            manager=self.gui
        )
        self.ui_element_values['mode_t'] = stat_view(
            relative_rect=pygame.Rect(304, y, 48, 64),
            split='tb',
            name='mode',
            manager=self.gui,
            colourmap_mode='equals',
            colourmap={
                    '3D': (0, 255, 0, 255),
                    '2D': (255, 255, 0, 255),
                    None: (255, 0, 0, 255)
            }
        )
        self.ui_element_values['sats'] = stat_view(
            relative_rect=pygame.Rect(352, y, 48, 64),
            split='tb',
            name='sats',
            manager=self.gui
        )
        y += 64

        self.ui_element_graphs['speed'] = stat_view_graph(
            relative_rect=pygame.Rect(0, y, 384, 32),
            text_w=128,
            label_s=40,
            name='spd',
            manager=self.gui,
            unit='km/h'
        )
        y += 32

        self.satellite_rows = [{} for i in range(10)]
        for i, lbl in enumerate(['PRN', 'el', 'az', 'ss', 'used']):
            self.ui_element_labels[lbl] = stat_label(
                relative_rect=pygame.Rect(i*80, y, 80, 32),
                text=lbl, manager=self.gui
            )
            for j, row in enumerate(self.satellite_rows):
                row[lbl] = stat_display(
                    relative_rect=pygame.Rect(i*80, y + 32 + j*32, 80, 32),
                    text='',
                    manager=self.gui
                )

    @crash_handler.monitor_thread
    def backend_loop(self):
        while True:
            try:
                gpsd = gps.gps(
                    mode=gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE,
                    host=self.config.host,
                    port=self.config.port
                )
                while True:
                    report = gpsd.next()
                    self.gps_data[report['class']] = report
                    self.data_updated = True
            except OSError as e:
                self.gps_data = {'status': f'Connection error: {str(e)}'}
                self.data_updated = True
            time.sleep(5)

    def draw(self, screen):
        if super().draw(screen):
            self.gps_satview.draw(screen, (400, self.display.TOP_BAR_SIZE + 32))
            return True
        return False

    def update(self, dt):
        if self.data_updated:
            tpv = self.gps_data.get('TPV',{})
            for v in ['lat', 'lon']:
                self.ui_element_values[v].set_text(f"{tpv.get(v,0):.6f}")
            self.ui_element_values['alt'].set_text(f"{tpv.get('alt',0):.1f}m")
            self.ui_element_values['trk'].set_text(f"1{tpv.get('track',0):.0f}")

            v = tpv.get('speed', 0)
            self.ui_element_graphs['speed'].update(float(v)*3.6) # m/s -> km/h

            devices = self.gps_data.get('DEVICES',{}).get('devices',[])[0]
            title = f"{devices.get('driver', '')} {devices.get('subtype','')} at {devices.get('path','')}:{devices.get('bps','')}:8{devices.get('parity','')}{devices.get('stopbits','')}"
            self.ui_element_values['status'].set_text(title)

            gps_mode = {
                0: 'UNK',
                1: 'NONE',
                2: '2D',
                3: '3D'
            }.get(tpv.get('mode'),'?')
            self.ui_element_values['mode_t'].set_text(gps_mode)

            if 'SKY' in self.gps_data:
                skydata = self.gps_data['SKY'].get('satellites', [])
                self.gps_satview.update_data(skydata)
                skydata = sorted(list(skydata), key=lambda a: a['used'], reverse=True)
                for i in range(10):
                    for lbl in ['PRN', 'el', 'az', 'ss', 'used']:
                        satval = self.satellite_rows[i]
                        if i < len(skydata):
                            satval[lbl].set_text(str(skydata[i][lbl]))
                        else:
                            satval[lbl].set_text('')
                numsats = len(skydata)
                numused = len([i for i in skydata if i['used']])
                self.ui_element_values['sats'].set_text(f"{numused}/{numsats}")
            else:
                for i in range(10):
                    for lbl in ['PRN', 'el', 'az', 'ss', 'used']:
                        self.satellite_rows[i][lbl].set_text('')
                self.ui_element_values['sats'].set_text('')

        super().update(dt)
