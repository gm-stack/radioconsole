import math
import datetime

def since(ts):
    if ts:
        return (datetime.datetime.now() - ts).total_seconds()

def hh_mm_ss_since(ts):
    return hh_mm_ss(since(ts))

def mm_ss_since(ts):
    return mm_ss(since(ts))

def hh_mm_ss(timer):
    if timer:
        hh = math.floor(timer // 3600)
        timer = timer % 3600.0
        mm = math.floor(timer // 60.0)
        ss = math.floor(timer % 60.0)
        return f"{hh}:{mm:02}:{ss:02}"
    else:
        return "--:--"

def mm_ss(timer):
    if timer:
        mm = math.floor(timer // 60.0)
        ss = math.floor(timer % 60.0)
        return f"{mm:02}:{ss:02}"
    else:
        return "--:--"

def mm_ss_fff(timer):
    mm = math.floor(timer // 60.0)
    ss = timer % 60.0
    return f"{mm:02}:{ss:06.3f}"