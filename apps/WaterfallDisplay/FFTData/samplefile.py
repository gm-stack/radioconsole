import os
import numpy as np

class file_samples(object):
    def __init__(self, cfg):
        iqfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rtl_test.iq')
        self.f = open(iqfile, 'rb')

    # pylint: disable=no-self-use
    def get_samples(self, n_samples):
        samples = self.f.read(n_samples * 2)
        if len(samples) < (n_samples * 2):
            print("restarting file")
            self.f.seek(0)
            return self.get_samples(n_samples)
        #print(samples)
        #rtlsdr.RtlSdr.packed_bytes_to_iq(None, samples)

        s = np.frombuffer(samples, dtype='uint8')
        iq = s.astype('float64').view('complex128')
        iq /= 127.5
        iq -= (1 + 1j)

        return iq
