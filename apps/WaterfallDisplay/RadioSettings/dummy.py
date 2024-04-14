import threading
import time
import struct

import serial

class dummy(object):
    def __init__(self, config):
        pass
    
    def freq(self):
        return 7_100_000