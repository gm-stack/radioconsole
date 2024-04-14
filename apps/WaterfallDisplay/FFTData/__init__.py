import pyfftw
import numpy as np
import scipy.signal

from . import rtl
from . import random_s
from . import samplefile

class FFTData(object):

    SampleProviders = {
        'rtlsdr': rtl.rtlsdr_samples,
        'random': random_s.rand_samples,
        'file': samplefile.file_samples
    }

    def __init__(self, provider, config):
        if not provider in self.SampleProviders:
            raise ValueError(
                f"unknown provider {provider}, "
                f"supported providers are {self.SampleProviders.keys()}"
                )

        self.provider = self.SampleProviders[provider](config)

        self.last_fft_bins = None
        self.fft_input = None
        self.fft_output = None
        self.fftw = None

        self.last_window_size = None
        self.window = None

    def retune(self, *args, **kwargs):
        self.provider.retune(*args, **kwargs)

    def fft(self, num_bins, decimate=1):
        if self.last_fft_bins != num_bins:
            print(f"creating new FFTW object: {num_bins} bins")
            self.last_fft_bins = num_bins
            self.fft_input = pyfftw.empty_aligned(num_bins, dtype='complex128')
            self.fft_output = pyfftw.empty_aligned(num_bins, dtype='complex128')
            self.fftw = pyfftw.FFTW(self.fft_input, self.fft_output)

        num_samples = num_bins * decimate

        if self.last_window_size != num_bins:
            print(f"creating new window function: n={num_bins}")
            self.window = scipy.signal.windows.hann(num_bins, sym=False)
            self.last_window_size = num_bins

        signal = self.provider.get_samples(num_samples)
        if decimate == 1:
            signal *= self.window
            self.fft_input[:] = signal
        else:
            self.fft_input[:] = scipy.signal.decimate(signal, decimate, zero_phase=False) * self.window
        self.fftw()
        fft = np.fft.fftshift(self.fft_output)
        fft = np.absolute(fft)
        return fft
