import rtlsdr

class rtlsdr_samples(object):
    def __init__(self, cfg):
        print(f"opening rtlsdr serial number {cfg.device_serial}")
        self.rtlsdr = rtlsdr.RtlSdr(serial_number=cfg.device_serial)
        
    def retune(self, if_freq, sample_rate):
        self.rtlsdr.set_center_freq(if_freq)
        print(f"tuning to {if_freq/1000}khz")
        self.rtlsdr.set_sample_rate(sample_rate)
        self.rtlsdr.set_manual_gain_enabled(True)
        self.rtlsdr.set_gain(48.0)

    def get_samples(self, n_samples):
        nsamples_pwr2 = 2**(n_samples - 1).bit_length()
        # smallest power of 2 > num_samples, as sample reads can only be a power of 2
        # read power of 2 and throw away everything after requested length
        return self.rtlsdr.read_samples(nsamples_pwr2)[:n_samples]