import threading
import pygame
import pygame_gui
import time
import gps
import gps.clienthelpers
import ctypes

import crash_handler
from config_reader import cfg
from AppManager.app import app
from .gps_satview import gps_satview
from util import timegraph, stat_display, stat_label, stat_view, stat_view_graph, extract_number
from .status_icon import gps_status_icon

class gps_status(app):

    def __init__(self, bounds, config, display, name):
        super().__init__(bounds, config, display, name)

        self.gps_data = {}
        self.tpv = {}

        self.gps_error = ''

        self.status_icon = gps_status_icon()
        self.status_icons = [self.status_icon.surface]
        self.status_icon.update(mode='-', sats='0/0', maidenhead='-', icon='redalert')
        self.status_icons_updated = True

        # actually, start it
        self.backend_thread = None
        self.restart_backend_thread()

        self.gps_satview = gps_satview((400, 400))

        y = display.TOP_BAR_SIZE

        self.ui_element_values = {}
        self.ui_element_graphs = {}

        self.ui_element_values['status'] = stat_label(
            object_id="#param_label_top",
            relative_rect=pygame.Rect(0, y, 800, 32),
            text=f"{self.config.host}:{self.config.port}", manager=self.gui
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

        self.ui_element_labels = {}

        self.satellite_rows = [{} for i in range(10)]
        for i, lbl in enumerate(['PRN', 'el', 'az', 'ss', 'used']):
            self.ui_element_labels[lbl] = stat_label(
                object_id="#param_label_vert",
                relative_rect=pygame.Rect(i*80, y, 80, 32),
                text=lbl, manager=self.gui
            )
            for j, row in enumerate(self.satellite_rows):
                row[lbl] = stat_display(
                    relative_rect=pygame.Rect(i*80, y + 32 + j*32, 80, 32),
                    text='',
                    manager=self.gui
                )
        self.data_good()

    def restart_backend_thread(self):
        if self.backend_thread:
            print("terminating existing gps backend thread")
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.backend_thread.ident), 
                ctypes.py_object(SystemExit)
            )

        self.backend_thread = threading.Thread(target=self.backend_loop, daemon=True)
        self.backend_thread.start()

    @crash_handler.monitor_thread
    def backend_loop(self):
        while True:
            try:
                gpsd = gps.gps(
                    mode=gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE,
                    host=self.config.host,
                    port=self.config.port
                )
                for report in gpsd:
                    self.gps_data[report['class']] = report
                    self.data_updated = True

                    self.tpv = self.gps_data.get('TPV',{})
                    self.skydata = self.gps_data.get('SKY',{}).get('satellites', [])
                    self.numsats = len(self.skydata)
                    self.numused = len([i for i in self.skydata if i['used']])
                    self.sats_text = f"{self.numused}/{self.numsats}"

                    lat = self.tpv.get('lat')
                    lon = self.tpv.get('lon')
                    if lat and lon:
                        mh = gps.clienthelpers.maidenhead(lat,lon)
                    else:
                        mh = '-'

                    self.status_icon.update(
                        mode=self.gps_mode(self.tpv.get('mode','')),
                        sats=self.sats_text,
                        maidenhead=mh,
                        icon=None
                    )
                    self.status_icons_updated = True
                    self.gps_data['status'] = ''
                    self.gps_error = ''
                    self.data_good()
            except OSError as e:
                self.gps_error = f'Connection error: {str(e)}'
                self.tpv = {}
                self.status_icon.update(mode='-', sats='0/0', maidenhead='-', icon='orangealert')
                self.status_icons_updated = True
                self.data_updated = True

            self.gps_error = f'Disconnected'
            self.tpv = {}
            self.status_icon.update(mode='-', sats='0/0', maidenhead='-', icon='orangealert')
            self.status_icons_updated = True
            self.data_updated = True
            time.sleep(1)

    def draw(self, screen):
        if super().draw(screen):
            self.gps_satview.draw(screen, (400, self.display.TOP_BAR_SIZE + 32))
            return True
        return False

    @staticmethod
    def gps_mode(m):
        return {
            0: 'UNK',
            1: 'NONE',
            2: '2D',
            3: '3D'
        }.get(m,'?')

    def update(self, dt):
        if self.data_updated:
            status_text = self.gps_data.get("status")
            error_text = self.gps_error
            if status_text or error_text:
                msg = [x for x in [status_text, error_text] if x]
                self.ui_element_values['status'].set_text(": ".join(msg))

            for v in ['lat', 'lon']:
                self.ui_element_values[v].set_text(f"{self.tpv.get(v,0):.6f}")
            self.ui_element_values['alt'].set_text(f"{self.tpv.get('alt',0):.1f}m")
            self.ui_element_values['trk'].set_text(f"{self.tpv.get('track',0):.0f}")

            v = self.tpv.get('speed', 0)
            self.ui_element_graphs['speed'].update(float(v)*3.6) # m/s -> km/h

            devices_list = self.gps_data.get('DEVICES',{}).get('devices',[])
            if len(devices_list) > 0:
                devices = devices_list[0]
                title = f"{devices.get('driver', '')} {devices.get('subtype','')} at {devices.get('path','')}:{devices.get('bps','')}:8{devices.get('parity','')}{devices.get('stopbits','')}"
                self.ui_element_values['status'].set_text(title)

            self.ui_element_values['mode_t'].set_text(self.gps_mode(self.tpv.get('mode')))

            sats_text = ""
            if 'SKY' in self.gps_data:
                self.skydata = self.gps_data['SKY'].get('satellites', [])
                self.gps_satview.update_data(self.skydata)
                self.skydata = sorted(list(self.skydata), key=lambda a: a['used'], reverse=True)
                for i in range(10):
                    for lbl in ['PRN', 'el', 'az', 'ss', 'used']:
                        satval = self.satellite_rows[i]
                        if i < len(self.skydata):
                            satval[lbl].set_text(str(self.skydata[i][lbl]))
                        else:
                            satval[lbl].set_text('')
                self.ui_element_values['sats'].set_text(self.sats_text)
            else:
                for i in range(10):
                    for lbl in ['PRN', 'el', 'az', 'ss', 'used']:
                        self.satellite_rows[i][lbl].set_text('')
                self.ui_element_values['sats'].set_text('')

        super().update(dt)

    def no_data_update_for(self, data_for, sec_since):
        self.gps_data = {
            'status': f"No GPS data received for {sec_since}s", 
            'error': self.gps_data.get('error')
        }
        self.tpv = {}
        self.status_icon.update(mode='-',sats='-', maidenhead='-', icon='redalert')
        self.status_icons_updated = True
        self.data_updated = True

        if sec_since > 1 and sec_since % 10 == 0:
            self.restart_backend_thread()