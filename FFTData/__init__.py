from . import rtl
import pyfftw
import numpy as np

class FFTData(object):
    
    SampleProviders = {
        'rtlsdr': rtl.rtlsdr_samples
    }

    def __init__(self, provider, cfg):
        if not provider in self.SampleProviders:
            raise ValueError(f"unknown provider {provider}, supported providers are {self.SampleProviders.keys()}")

        self.provider = self.SampleProviders[provider](cfg)

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
        
        self.fft_input[:] = self.provider.get_samples(num_bins)
        self.fftw()
        fft = np.fft.fftshift(self.fft_output)
        fft = np.absolute(fft)
        return fft