import math

def mm_ss(timer):
    if timer >= 0:
        mm = math.floor(timer // 60.0)
        ss = math.floor(timer % 60.0)
        return f"{mm:02}:{ss:02}"
    else:
        return "--:--"

def mm_ss_fff(timer):
    mm = math.floor(timer // 60.0)
    ss = timer % 60.0
    return f"{mm:02}:{ss:06.3f}"