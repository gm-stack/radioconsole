from ..common import SSHBackgroundThreadApp
from .USBBusView import usb_bus_view
import json

class USBStatus(SSHBackgroundThreadApp):
    def __init__(self, bounds, config, name):

        self.usb_bus_view = usb_bus_view(bounds)
        self.usb_bus_view.update_data(self.parse_lsusb_py())

        super().__init__(bounds, config, name)

    def update(self, dt):
        if super().update(dt):
            self.gui.update(dt)

    def draw(self, screen):
        if super().draw(screen):
            self.usb_bus_view.draw(screen)
            return True
        return False

    def parse_lsusb_py(self):
        d = open("usb/usb.py.txt", 'r').read()
        j = json.loads(d)
        return j

