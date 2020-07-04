import rtlsdr

class rtlsdr_samples(object):
    def __init__(self, cfg):
        self.rtlsdr = rtlsdr.RtlSdr()
        centre_freq = cfg.IF_FREQ
        self.rtlsdr.set_center_freq(centre_freq)
        print(f"tuning to {centre_freq/1000}khz")
        self.rtlsdr.set_sample_rate(cfg.SAMPLE_RATE)
        self.rtlsdr.set_manual_gain_enabled(True)
        self.rtlsdr.set_gain(48.0)
        self.gain_pos = 0

        print(f"tuner is {self.rtlsdr.get_tuner_type()}")
    
    def get_samples(self, n_samples):
        nsamples_pwr2 = 2**(n_samples - 1).bit_length() 
        # smallest power of 2 > num_samples, as sample reads can only be a power of 2
        # read power of 2 and throw away everything after requested length
        return self.rtlsdr.read_samples(nsamples_pwr2)[:n_samples]

