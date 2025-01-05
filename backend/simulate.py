import pygame
import math, random
from enum import Enum
from doraneko94 import Fighter as FighterPlayer
from doraneko94 import Missile as MissilePlayer
from computer import Fighter as FighterComputer
from computer import Missile as MissileComputer

L1, L2 = 20, 10
A = 120
sensor_range = 200
K, dt = 1, 0.01

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

def deg2rad(deg):
    return deg / 180 * math.pi
def rad2deg(rad):
    return rad * 180 / math.pi

class Unit(Enum):
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
        self.unit = 0
        if unit == Unit.PMI or unit == Unit.CMI:
            self.unit = 1

class Core:
    def __init__(self, object):
        self.__object = object

    def sense(self):
        outputs = []
        for obj in objlist:
            if obj.is_active and obj.unit != self.__object.unit and self.__object.distance(obj) < sensor_range:
                a = self.__object.angle(obj)
                x = math.sin(a - self.__object.direction)
                y = math.cos(a - self.__object.direction)
                outputs.append(Output(x, y, obj.unit))
        return Position(self.__object.x, self.__object.y, self.__object.direction), outputs

class Object:
    def __init__(self, x, y, direction, color, unit):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.direction = direction
        self.color = color
        self.unit = unit
        self.is_active = True
        self.lifetime = 0

    def distance(self, obj):
        return math.sqrt((self.x - obj.x)**2 + (self.y - obj.y)**2)
    
    def angle(self, obj):
        return math.atan2(obj.x - self.x, obj.y - self.y)
    
    def deactivate(self):
        self.is_active = False
    
    def activate(self, obj, lifetime=500):
        self.x = obj.x + L1 * 1.1 * math.sin(deg2rad(obj.direction))
        self.y = obj.y - L1 * 1.1 * math.cos(deg2rad(obj.direction))
        self.vx = obj.vx
        self.vy = obj.vy
        self.lifetime = lifetime
        self.is_active = True
    
    def draw(self):
        pygame.draw.polygon(screen, self.color, [
            (self.x + L1 * math.sin(deg2rad(self.direction)), self.y - L1 * math.cos(deg2rad(self.direction))),
            (self.x + L2 * math.sin(deg2rad(A + self.direction)), self.y - L2 * math.cos(deg2rad(A + self.direction))),
            (self.x - L2 * math.sin(deg2rad(A - self.direction)), self.y - L2 * math.cos(deg2rad(A - self.direction))),
        ])

objlist = [
    Object(100, 100, 0, (255, 0, 0), Unit.PYR),
    Object(600, 400, 0, (0, 0, 255), Unit.COM),
    Object(0, 0, 0, (0, 255, 0), Unit.PMI),
    Object(0, 0, 0, (0, 255, 0), Unit.CMI),
]

fighter_pyr = FighterPlayer(Core(objlist[0]))
fighter_com = FighterComputer(Core(objlist[1]))
missile_pyr = MissilePlayer(Core(objlist[2]))
missile_com = MissileComputer(Core(objlist[3]))

def update(i, f, a):
    f = max(-1, min(1, f))
    angle = deg2rad(a + objlist[i].direction)
    objlist[i].vx += (f * 100 * math.sin(angle) - K * objlist[i].vx) * dt
    objlist[i].vy += (f * 100 * math.cos(angle) - K * objlist[i].vy) * dt
    objlist[i].x += objlist[i].vx * dt
    objlist[i].y -= objlist[i].vy * dt
    objlist[i].direction = rad2deg(math.atan2(objlist[i].vx, objlist[i].vy))
    objlist[i].draw()

running = True
while running:
    screen.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    f, a = fighter_pyr.move()
    update(0, f, a)
    f, a = fighter_com.move()
    update(1, f, a)

    if fighter_pyr.launch() and not objlist[2].is_active:
        objlist[2].activate(objlist[0])
    if objlist[2].is_active:
        a = missile_pyr.move()
        update(2, 1, a)
        objlist[2].lifetime -= 1
        if objlist[2].lifetime <= 0:
            objlist[2].deactivate()

    if fighter_com.launch() and not objlist[3].is_active:
        objlist[3].activate(objlist[1])
    if objlist[3].is_active:
        a = missile_com.move()
        update(3, 1, a)
        objlist[3].lifetime -= 1
        if objlist[3].lifetime <= 0:
            objlist[3].deactivate()

    pygame.display.flip()
    clock.tick(30)

pygame.quit()