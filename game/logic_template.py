from ..user_files.doraneko94.module import Fighter as PlayerFighter, Missile as PlayerMissile
from ..user_files.shuntaro94.module import Fighter as ComputerFighter, Missile as ComputerMissile
from .consts import *
from .structs import *

class Core:
    def __init__(self, object):
        self.__object = object

    def sense(self):
        outputs = []
        for obj in objlist:
            dist = self.__object.distance(obj)
            if obj.is_active and obj.unit != self.__object.unit and dist < sensor_range:
                a = self.__object.angle(obj)
                x = dist * math.sin(a - deg2rad(self.__object.direction))
                y = dist * math.cos(a - deg2rad(self.__object.direction))
                outputs.append(Output(x, y, decodeUnit(obj.unit, self.__object.unit)))
        return Position(self.__object.x, self.__object.y, self.__object.direction), outputs
    
objlist = [
    Object(100, 100, 180, Unit.PYR),
    Object(sizeX - 100, sizeY - 100, 0, Unit.COM),
    Object(0, 0, 0, Unit.PMI),
    Object(0, 0, 0, Unit.CMI)
]

fighter_pyr = PlayerFighter(Core(objlist[0]))
fighter_com = ComputerFighter(Core(objlist[1]))
missile_pyr = PlayerMissile(Core(objlist[2]))
missile_com = ComputerFighter(Core(objlist[3]))

objlist[2].deactivate()
objlist[3].deactivate()

c = 0

def update(i, f, a):
    f = max(-1, min(1, f))
    angle = deg2rad(a + objlist[i].direction)
    objlist[i].vx += (f * 100 * math.sin(angle) - K * objlist[i].vx) * dt
    objlist[i].vy += (f * 100 * math.cos(angle) - K * objlist[i].vy) * dt
    objlist[i].x += objlist[i].vx * dt
    objlist[i].y -= objlist[i].vy * dt
    objlist[i].direction = rad2deg(math.atan2(objlist[i].vx, objlist[i].vy))

def initialize_state():
    state = {
        "fighters": [
            (100.0, 100.0, math.pi), (sizeX - 100.0, sizeY - 100.0, 0)
        ],
        "missiles": [],
        "pyr_wins": None
    }
    return state

def step(state):
    if state["pyr_wins"] is not None:
        return state
    f, a = fighter_pyr.move()
    update(0, f, a)
    f, a = fighter_com.move()
    update(1, f, a)

    if fighter_pyr.launch() and not objlist[2].is_active:
        objlist[2].activate(objlist[0])
    if objlist[2].is_active:
        a = max(-45, min(45, missile_pyr.move()))
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

    c += 1
    if c >= 1000:
        return {
            "fighters": [], "missiles": [],
            "pyr_wins": True
        }
    else:
        return {
            "fighters": [
                (objlist[0].x, objlist[0].y, deg2rad(objlist[0].direction)),
                (objlist[1].x, objlist[1].y, deg2rad(objlist[1].direction))
            ],
            "missiles": [
                (objlist[2].x, objlist[2].y, deg2rad(objlist[2].direction)),
                (objlist[3].x, objlist[3].y, deg2rad(objlist[3].direction))
            ],
            "pyr_wins": None
        }