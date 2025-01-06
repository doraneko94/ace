import math

def deg2rad(deg):
    return deg / 180 * math.pi
def rad2deg(rad):
    return rad * 180 / math.pi

def decodeUnit(unit, ref):
    dec = unit // 2 * 2
    if unit % 2 != ref % 2:
        dec += 1
    return dec