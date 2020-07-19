import socket
from types import SimpleNamespace

import FFTData

port = 45362

config = SimpleNamespace(
    IF_FREQ=124488500,
    SAMPLE_RATE=1200000,
    RF_MIN=0,
    RF_MAX=200
)

class FFTWaterfall(object):
    def __init__(self):
        self.config = config
        self.rf = FFTData.FFTData(
            provider='rtlsdr',
            config=config
        )
    
        self.decimate_zoom = True
        self.num_fft_bins = None
        self.display_bandwidth = None
        self.absmode = False
        self.abs_freq_low = 7000000
        self.abs_freq_high = 7300000
        self.output_w = 800
        self.rel_bandwidth = 1200000
        self.RF_MAX = config.RF_MAX

    def fft(self):
        total_fft_bw = (self.config.SAMPLE_RATE)
        if self.absmode: # absolute frequency display
            self.display_bandwidth = self.abs_freq_high - self.abs_freq_low
            self.num_fft_bins = int((total_fft_bw / self.display_bandwidth) * self.output_w)

            centre_freq = self.config.CURRENT_FREQ
            centre_bin = self.num_fft_bins // 2
            hz_per_pixel = total_fft_bw / float(self.num_fft_bins)

            leftside_bin = centre_bin + int((self.abs_freq_low - centre_freq) / hz_per_pixel)

            fft = self.rf.fft(self.num_fft_bins)[::-1][leftside_bin:]
        else:
            self.display_bandwidth = self.rel_bandwidth
            if self.decimate_zoom:
                decimate_factor = int(self.config.SAMPLE_RATE / self.rel_bandwidth)

                fft = self.rf.fft(self.output_w, decimate=decimate_factor)[::-1]
            else:
                self.num_fft_bins = int((total_fft_bw / self.display_bandwidth) * self.output_w)

                centre_freq = self.config.CURRENT_FREQ
                centre_bin = self.num_fft_bins // 2
                hz_per_pixel = total_fft_bw / float(self.num_fft_bins)

                leftside_bin = centre_bin + \
                    int((centre_freq - (self.rel_bandwidth / 2) - centre_freq) / hz_per_pixel)

                fft = self.rf.fft(self.num_fft_bins)[::-1][leftside_bin:]

        fft = (fft - self.config.RF_MIN) / (self.RF_MAX - self.config.RF_MIN)

        headroom = (0.5 - max(fft))
        change = headroom * self.RF_MAX * 0.1
        self.RF_MAX -= change

        return fft * 256


def handle_conn(conn, addr):
    print(addr)
    conn.setblocking(0)
    while True:
        try:
            r = conn.recv(8)
            if not r:
                break # connection closed
            print(len(r))
        except BlockingIOError:
            pass
        
        fftd = fft.fft().astype('uint8').tobytes()
        sent = conn.send(fftd)
        if sent < 800:
            raise IOError()

fft = FFTWaterfall()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    print(f"Listening on {port}")

    conn, addr = s.accept()
    handle_conn(conn, addr)
    conn.close()
