import threading
import pygame
import time
import gps
import gps.clienthelpers
import ctypes

import crash_handler
from AppManager.app import app
from .gps_satview import gps_satview, GNSS_IDS
from util import stat_display, stat_label
from .status_icon import gps_status_icon

class gps_status(app):
    default_config = {
        "port": 2947
    }

    def __init__(self, bounds, config, name):
        super().__init__(bounds, config, name)

        self.gps_data = {}
        self.tpv = {}

        self.gps_error = ''

        self.status_icon = gps_status_icon()
        self.status_icons = [self.status_icon.surface]
        self.mh = "-"
        self.status_icon.update(mode='-', sats='0/0', maidenhead=self.mh, icon='warning_red')
        self.status_icons_updated = True

        self.skydata = []

        # actually, start it
        self.backend_thread = None
        self.restart_backend_thread()

        # find biggest square for gps satview
        satview_size = self.bounds.h

        self.gps_satview = gps_satview(pygame.Rect(
            self.bounds.w - satview_size,
            self.bounds.y,
            satview_size, satview_size
        ))

        non_satview_size = self.bounds.w - satview_size

        y = bounds.y

        self.ui_element_values = {}
        self.ui_element_graphs = {}

        self.ui_element_values['status'] = stat_label(
            object_id="#param_label_top",
            relative_rect=pygame.Rect(0, y, non_satview_size, 32),
            text=f"{self.config.host}:{self.config.port}", manager=self.gui
        )
        y += 32

        self.ui_element_labels = {}

        for gnss_id, gnss in GNSS_IDS.items():
            # only used indoors in japan, don't bother
            if gnss['name'] == "IMES": continue

            self.ui_element_labels[f"gnss_{gnss_id}"] = stat_label(
                object_id=f"#gnss_label_{gnss['prefix']}",
                relative_rect=pygame.Rect(0, y, non_satview_size, 32),
                text=f"{gnss['prefix']}: {gnss['name']}",
                manager=self.gui
            )
            y += 32
            self.ui_element_values[f"gnss_{gnss_id}"] = []
            num_elements = 16
            for i in range(num_elements):
                elem_width = non_satview_size / num_elements
                self.ui_element_values[f"gnss_{gnss_id}"].append(stat_display(
                    relative_rect=pygame.Rect(i*elem_width, y, elem_width, 32),
                    text='',
                    manager=self.gui
                ))
            y += 32

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
                    if 'satellites' in self.gps_data.get('SKY',{}): # Some SKY messages do not include satellites field - this stops flicking by checking if the satellites key is avalaible
                        self.skydata = self.gps_data.get('SKY',{})['satellites']
                    self.numsats = len(self.skydata)
                    self.numused = len([i for i in self.skydata if i['used']])
                    self.sats_text = f"{self.numused}/{self.numsats}"

                    lat = self.tpv.get('lat')
                    lon = self.tpv.get('lon')
                    if lat and lon:
                        self.mh = gps.clienthelpers.maidenhead(lat,lon)
                    else:
                        self.mh = '-'

                    self.status_icon.update(
                        mode=self.gps_mode(self.tpv.get('mode','')),
                        sats=self.sats_text,
                        maidenhead=self.mh,
                        icon=None
                    )
                    self.status_icons_updated = True
                    self.gps_data['status'] = ''
                    self.gps_error = ''
                    self.data_good()
            except OSError as e:
                self.gps_error = f'Connection error: {str(e)}'
                self.tpv = {}
                self.status_icon.update(mode='-', sats='0/0', maidenhead='-', icon='warning_orange')
                self.status_icons_updated = True
                self.data_updated = True

            self.gps_error = f'Disconnected'
            self.tpv = {}
            self.status_icon.update(mode='-', sats='0/0', maidenhead='-', icon='warning_orange')
            self.status_icons_updated = True
            self.data_updated = True
            time.sleep(1)

    def draw(self, screen):
        if super().draw(screen):
            self.gps_satview.draw(screen)
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

    def sat_format_name(self, sat):
        prn = sat['PRN']
        status = " "
        if not sat['used']:
            status = "!"
        if 'health' in sat and sat['health'] != 1:
            status = "+"
        return f"{status}{prn}"

    def update(self, dt):
        if self.data_updated:
            status_text = self.gps_data.get("status")
            error_text = self.gps_error
            if status_text or error_text:
                msg = [x for x in [status_text, error_text] if x]
                self.ui_element_values['status'].set_text(": ".join(msg))

            devices_list = self.gps_data.get('DEVICES',{}).get('devices',[])
            if len(devices_list) > 0:
                devices = devices_list[0]
                title = f"{devices.get('driver', '')} {devices.get('subtype','')} at {devices.get('path','')}:{devices.get('bps','')}:8{devices.get('parity','')}{devices.get('stopbits','')}"
                self.ui_element_values['status'].set_text(title)

            sats_text = ""
            if 'SKY' in self.gps_data:
                if 'satellites' in self.gps_data['SKY']:
                    self.skydata = self.gps_data['SKY']['satellites']
                self.gps_satview.update_data(self.skydata, self.tpv, self.mh)
                for gnss_id, gnss in GNSS_IDS.items():
                    # not in ui
                    if gnss['name'] == "IMES": continue

                    sats = [s for s in self.skydata if s['gnssid'] == gnss_id]

                    numsats = len(sats)
                    numused = len([s for s in sats if s['used']])
                    used_label = f"{numused}/{numsats}"

                    label_text = f"{gnss['prefix']}: {gnss['name']}: {used_label}"
                    self.ui_element_labels[f"gnss_{gnss_id}"].set_text(label_text)

                    # todo: colour and place (don't remove existing from box)
                    ui_elements = self.ui_element_values[f"gnss_{gnss_id}"]
                    for i, e in enumerate(ui_elements):
                        if i < len(sats):
                            sat = sats[i]
                            e.set_text(str(sat['PRN'])[-2:])
                            if sat['used']:
                                signal = (sat['ss'] * 5) + 80
                                if signal > 255:
                                    signal = 255
                                if signal < 0:
                                    signal = 0
                                # TODO: multiply by colour for constellation
                                e.text_colour = (0x00,signal,0x00)
                            else:
                                e.text_colour = (0x66,0x66,0x66)
                            if 'health' in sat and sat['health'] != 1:
                                e.text_colour = (0xCC,0x00,0x00)
                            e.rebuild()
                        else:
                            e.set_text('')
            else:
                for gnss_id, gnss in GNSS_IDS.items():
                    # not in ui
                    if gnss['name'] == "IMES": continue

                    label_text = f"{gnss['prefix']}: {gnss['name']}: 0/0"
                    self.ui_element_labels[f"gnss_{gnss_id}"].set_text(label_text)
                    for e in self.ui_element_values[f"gnss_{gnss_id}"]:
                        e.set_text('')


        super().update(dt)

    def no_data_update_for(self, data_for, sec_since):
        self.gps_data = {
            'status': f"No GPS data received for {sec_since}s",
            'error': self.gps_data.get('error')
        }
        self.tpv = {}
        self.status_icon.update(mode='-',sats='-', maidenhead='-', icon='warning_red')
        self.status_icons_updated = True
        self.data_updated = True

        if sec_since > 1 and sec_since % 10 == 0:
            self.restart_backend_thread()
