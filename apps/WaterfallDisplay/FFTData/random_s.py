import numpy

class rand_samples(object):
    def __init__(self, cfg):
        pass

    # pylint: disable=no-self-use
    def get_samples(self, n_samples):
        return ((numpy.random.random(n_samples)*8)-4) + ((numpy.random.random(n_samples)*8)-4)*1j
