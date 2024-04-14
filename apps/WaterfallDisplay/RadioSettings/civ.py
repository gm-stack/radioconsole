import threading
import time
import struct

import serial

class civ(object):
    last_freq = 0
    backend_thread = None

    def __init__(self, config, callback):
        self.s = serial.Serial(config.icom_serial_port, int(config.icom_serial_baud))
        self.s.write(b"\xFE\xFE\x88\x00\x03\xFD") # 0x88 -> 0x00 - get frequency (0x03)

        self.callback = callback

        self.backend_thread = threading.Thread(target=self.backend_loop, daemon=True)
        self.backend_thread.start()


    def parse_packet(self, packet):
        def bcd(byte):
            return f"{(byte & 0xF0) >> 4}{byte & 0x0F}"

        print(f"{packet.hex()}")

        if not packet[0:2] == b'\xfe\xfe':
            print("invalid start")
            return
        dst = packet[2]
        src = packet[3]

        if src != 0x88:
            print(f"src is 0x{src:2x}, not 0x88")
            return

        cmd = packet[4]
        data = packet[5:-1]

        if not packet[-1] == 0xFD:
            print("invalid end")
            return

        try:
            if cmd == 0x00 or cmd == 0x03: # frequency
                self.last_freq = int("".join([bcd(b) for b in data[::-1]]))
                self.callback({'freq': self.last_freq})
            else:
                print(f"CI-V: unknown command 0x{cmd:x}")
        except Exception as e:
            print(f"exception {e} parsing packet")
            pass


    def backend_loop(self):
        while True:
            packet = bytes()
            while True:
                b = self.s.read(1)
                packet += b
                if b == b'\xfd':
                    self.parse_packet(packet)
                    packet = bytes()


    def freq(self):
        return self.last_freq

if __name__ == '__main__':
    c = civ(None)
    while True:
       time.sleep(1)
       print(c.freq())