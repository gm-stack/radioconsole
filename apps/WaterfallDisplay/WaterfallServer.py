import signal
signal.signal(signal.SIGHUP, lambda s, f: None)
# pylint: disable=wrong-import-position

import socket
from types import SimpleNamespace

import FFTData
import time
import struct
import rtlsdr

port = 45362


class FFTWaterfall(object):
    def __init__(self):
        self.config = SimpleNamespace(
            CURRENT_FREQ=7074000
        )
        self.rf = FFTData.FFTData(
            provider='rtlsdr',
            config=self.config
        )

        self.decimate_zoom = True
        self.num_fft_bins = None
        self.display_bandwidth = None
        self.absmode = False
        self.abs_freq_low = 7000000
        self.abs_freq_high = 7300000
        
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

            centre_freq = self.config.CURRENT_FREQ
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

                centre_freq = self.config.CURRENT_FREQ
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
    d = struct.unpack(
        '!BBHIIIBBxxxxxx',
        cmd_buffer
    )
    ver, msg, output_w, tune, sample_rate, relbw, absmode, decimate_zoom = d
    if ver != 0x00 or msg != 0x00:
        raise ValueError(f"invalid message: ver:{ver}, msg:{msg}")
    print(d)
    
    fft.tune = tune
    fft.sample_rate = sample_rate
    fft.retune(tune, sample_rate)
    
    fft.output_w = output_w
    fft.rel_bandwidth = relbw
    fft.absmode = bool(absmode)
    fft.decimate_zoom = bool(decimate_zoom)

HEADER = struct.pack('BB', 0x00, 0x01)

MAXRATE = 30
sample_every = 1.0 / MAXRATE
def handle_conn(conn, addr):
    conn.setblocking(0)
    prev_sampletime = 0
    cmd_buffer = bytes()
    got_initial_config = False
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
        
        if got_initial_config:
            conn.setblocking(0)
            timesince = time.monotonic() - prev_sampletime
            if timesince < sample_every:
                time.sleep(sample_every - timesince)
            
            fftd = fft.fft().astype('uint8').tobytes()
            
            try:
                conn.sendall(HEADER+fftd)
            except (BrokenPipeError, ConnectionResetError, BlockingIOError):
                return
            prev_sampletime = time.monotonic()

print("starting rtlsdr")

while True:
    try:
        fft = FFTWaterfall()
        break
    except rtlsdr.rtlsdr.LibUSBError:
        time.sleep(5)

print("rtlsdr started")

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
