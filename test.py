from enum import IntEnum

class Unit(IntEnum):
    PYR = 0
    COM = 1
    PMI = 2
    CMI = 3

# S 0
# E 1
# SMI 2
# EMI 3

def decodeUnit(unit, ref):
    dec = unit // 2 * 2
    if unit % 2 != ref % 2:
        dec += 1
    return dec

print(decodeUnit(Unit.PYR, Unit.PMI))