import rtlsdr
import pyfftw
import numpy as np

import config

class rtl_fft(object):
    def __init__(self):
        self.rtlsdr = rtlsdr.RtlSdr()
        centre_freq = config.IF_FREQ
        self.rtlsdr.set_center_freq(centre_freq)
        print(f"tuning to {centre_freq/1000}khz")
        self.rtlsdr.set_sample_rate(config.SAMPLE_RATE)
        self.rtlsdr.set_manual_gain_enabled(True)
        self.rtlsdr.set_gain(48.0)
        self.gain_pos = 0

        self.last_fft_bins = None
        self.fft_input = None
        self.fft_output = None
        self.fftw = None

    def fft(self, num_bins):
        if self.last_fft_bins != num_bins:
            print(f"creating new FFTW object: {num_bins} bins")
            self.last_fft_bins = num_bins
            self.fft_input = pyfftw.empty_aligned(num_bins, dtype='complex128')
            self.fft_output = pyfftw.empty_aligned(num_bins, dtype='complex128')
            self.fftw = pyfftw.FFTW(self.fft_input, self.fft_output)
        
        nsamples = 2**(num_bins - 1).bit_length()
        self.fft_input[:] = self.rtlsdr.read_samples(nsamples)[:num_bins]
        self.fftw()
        fft = np.fft.fftshift(self.fft_output)
        fft = np.absolute(fft)
        return fft
    
    def keydown(self, k, m):
        if k == '=':
            self.gain_pos += 1
            gain = self.rtlsdr.valid_gains_db[self.gain_pos]
            print(gain)
            self.rtlsdr.set_gain(gain)
            return True
        if k == '-':
            self.gain_pos -= 1
            gain = self.rtlsdr.valid_gains_db[self.gain_pos]
            print(gain)
            self.rtlsdr.set_gain(gain)
            return True
        return False
