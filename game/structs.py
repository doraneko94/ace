from enum import IntEnum
from .consts import *
from .utils import *
import math, pygame

class Unit(IntEnum):
    PYR = 0
    COM = 1
    PMI = 2
    CMI = 3

class Position:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction

class Output:
    def __init__(self, x, y, unit):
        self.x = x
        self.y = y
        self.unit = unit

class Object:
    def __init__(self, x, y, direction, unit):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.vd = 0
        self.direction = direction
        self.unit = unit
        self.is_active = True
        self.lifetime = 0

    def distance(self, obj):
        return math.sqrt((self.x - obj.x)**2 + (self.y - obj.y)**2)
    
    def angle(self, obj):
        return math.atan2(obj.x - self.x, -obj.y + self.y)
    
    def deactivate(self):
        self.is_active = False
    
    def activate(self, obj, lifetime=500):
        self.x = obj.x + L1 * 1.1 * math.sin(deg2rad(obj.direction))
        self.y = obj.y - L1 * 1.1 * math.cos(deg2rad(obj.direction))
        self.vx = obj.vx
        self.vy = obj.vy
        self.vd = obj.vd
        self.lifetime = lifetime
        self.is_active = True