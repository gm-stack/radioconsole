import signal
signal.signal(signal.SIGHUP, lambda s, f: None)
# pylint: disable=wrong-import-position

import socket
from types import SimpleNamespace
import sys

import FFTData
import RadioSettings
import time
import struct
import rtlsdr

import bands

sys.path.append('../..')
from config_reader import cfg

port = cfg.waterfall_server.listen_port

CURRENT_FREQ = 7100000

fft_via_udp = False

class FFTWaterfall(object):
    def __init__(self):
        self.config = cfg.waterfall_server
        self.rf = FFTData.FFTData(
            provider='rtlsdr',
            config=self.config
        )
        self.rs = RadioSettings.RadioSettings(
            provider='ci-v',
            config=self.config
        )

        self.decimate_zoom = True
        self.num_fft_bins = None
        self.display_bandwidth = None
        self.absmode = False
        self.abs_freq_low = 7000000
        self.abs_freq_high = 7300000
        self.rel_bandwidth = 1250000

        self.RF_MIN = 0
        self.RF_MAX = 127

    def retune(self, if_freq, sample_rate):
        self.rf.retune(if_freq, sample_rate)
        self.sample_rate = sample_rate

    def fft(self):
        total_fft_bw = self.sample_rate
        if self.absmode: # absolute frequency display
            self.display_bandwidth = self.abs_freq_high - self.abs_freq_low
            self.num_fft_bins = int((total_fft_bw / self.display_bandwidth) * self.output_w)

            centre_freq = CURRENT_FREQ
            centre_bin = self.num_fft_bins // 2
            hz_per_pixel = total_fft_bw / float(self.num_fft_bins)

            leftside_bin = centre_bin + int((self.abs_freq_low - centre_freq) / hz_per_pixel)

            fft = self.rf.fft(self.num_fft_bins)[::-1][leftside_bin:leftside_bin+self.output_w]
        else:
            self.display_bandwidth = self.rel_bandwidth
            if self.decimate_zoom:
                decimate_factor = int(self.sample_rate / self.rel_bandwidth)

                fft = self.rf.fft(self.output_w, decimate=decimate_factor)[::-1]
            else:
                self.num_fft_bins = int((total_fft_bw / self.display_bandwidth) * self.output_w)

                centre_freq = CURRENT_FREQ
                centre_bin = self.num_fft_bins // 2
                hz_per_pixel = total_fft_bw / float(self.num_fft_bins)

                leftside_bin = centre_bin + \
                    int((centre_freq - (self.rel_bandwidth / 2) - centre_freq) / hz_per_pixel)

                fft = self.rf.fft(self.num_fft_bins)[::-1][leftside_bin:leftside_bin+self.output_w]

        
        fft = (fft - self.RF_MIN) / (self.RF_MAX - self.RF_MIN)

        headroom = (0.5 - max(fft))
        change = headroom * self.RF_MAX * 0.1
        self.RF_MAX -= change

        return fft * 255

def parse_cmd_buffer(cmd_buffer):
    global fft_via_udp
    
    d = struct.unpack('!BBxxxxxxxxxxxxxxxxxxxxxx', cmd_buffer)
    ver, msg = d
    if ver != 0x00:
        raise ValueError(f"invalid message: ver:{ver}, msg:{msg}")
    
    if msg == 0x00:
        d = struct.unpack('!BBHIBBxxxxxxxxxxxxxx', cmd_buffer)
        _, _, output_w, relbw, absmode, decimate_zoom = d
    
        fft.output_w = output_w
        fft.rel_bandwidth = relbw
        fft.absmode = bool(absmode)
        fft.decimate_zoom = bool(decimate_zoom)
    elif msg == 0x01:
        d = struct.unpack('!BBHxxxxxxxxxxxxxxxxxxxx', cmd_buffer)
        _, _, port = d
        if port != 0:
            fft_via_udp = True
            print("Switching to UDP mode")
        else:
            fft_via_udp = False
            print("Stopping UDP mode")
    print(d)
    

def send_fft_line():
    global CURRENT_FREQ, fft_via_udp
    CURRENT_FREQ = fft.rs.freq()
    header = struct.pack('!BBI', 0x00, 0x01, CURRENT_FREQ)
    fftd = fft.fft().astype('uint8').tobytes()
    if fft_via_udp:
        s = u.sendto(header+fftd, (addr[0], 45362))
        if s != len(header+fftd):
            print(f"udp send failed, only {s} bytes sent")
    else:
        conn.sendall(header+fftd)

MAXRATE = 30
sample_every = 1.0 / MAXRATE
def handle_conn(conn, addr):
    global fft_via_udp
    conn.setblocking(0)
    prev_sampletime = 0
    cmd_buffer = bytes()
    got_initial_config = False
    fft_via_udp = False

    while True:
        try:
            if len(cmd_buffer) < 24:
                r = conn.recv(24 - len(cmd_buffer))
                if not r:
                    raise ConnectionResetError()
                cmd_buffer += r
            else:
                parse_cmd_buffer(cmd_buffer)
                got_initial_config = True
                cmd_buffer = bytes()
        except BlockingIOError:
            pass
        except ConnectionResetError:
            return

        if got_initial_config:
            conn.setblocking(0)
            timesince = time.monotonic() - prev_sampletime
            if timesince < sample_every:
                time.sleep(sample_every - timesince)
            
            try:
                send_fft_line()
            except (BrokenPipeError, ConnectionResetError, BlockingIOError):
                return
            prev_sampletime = time.monotonic()

print("starting rtlsdr")

while True:
    try:
        fft = FFTWaterfall()
        fft.tune = cfg.waterfall_server.if_freq
        fft.sample_rate = cfg.waterfall_server.sample_rate
        fft.retune(fft.tune, fft.sample_rate)
        break
    except rtlsdr.rtlsdr.LibUSBError as e:
        print(e)
        time.sleep(5)

print("rtlsdr started")

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as u:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        s.listen(1)
        print(f"Listening on {port}")

        while True:
            conn, addr = s.accept()
            print(f"{addr} connected")
            handle_conn(conn, addr)
            print(f"{addr} disconnected")
            conn.close()
