import time
from importlib import import_module
from .consts import *
from .structs import *

class Engine:
    def __init__(self, module_pyr_path, module_com_path):
        module_pyr = import_module(module_pyr_path)
        module_com = import_module(module_com_path)
        self.objlist = [
            Object(100, 100, 180, Unit.PYR),
            Object(SIZE_X - 100, SIZE_Y - 100, 0, Unit.COM),
            Object(0, 0, 0, Unit.PMI),
            Object(0, 0, 0, Unit.CMI)
        ]
        self.objlist[2].deactivate()
        self.objlist[3].deactivate()

        class Core:
            def __init__(self_core, object):
                self_core.__object = object

            def sense(self_core):
                outputs = []
                for obj in self.objlist:
                    dist = self_core.__object.distance(obj)
                    if obj.is_active and obj.unit != self_core.__object.unit and dist < SENSOR_RANGE:
                        a = self_core.__object.angle(obj)
                        x = dist * math.sin(a - deg2rad(self_core.__object.direction))
                        y = dist * math.cos(a - deg2rad(self_core.__object.direction))
                        outputs.append(Output(x, y, decodeUnit(obj.unit, self_core.__object.unit)))
                return Position(self_core.__object.x, SIZE_Y - self_core.__object.y, self_core.__object.direction), outputs


        self.fighter_pyr = module_pyr.Fighter(Core(self.objlist[0]))
        self.fighter_com = module_com.Fighter(Core(self.objlist[1]))
        self.missile_pyr = module_pyr.Missile(Core(self.objlist[2]))
        self.missile_com = module_com.Missile(Core(self.objlist[3]))
        self.time_elapsed = 0
        self.pyr_wins = None

                    
    def update(self, i, f, a):
        f = max(-1, min(1, f))
        #angle = deg2rad(a + self.objlist[i].direction)
        #self.objlist[i].vx += (f * 100 * math.sin(angle) - K * self.objlist[i].vx) * DT
        #self.objlist[i].vy += (f * 100 * math.cos(angle) - K * self.objlist[i].vy) * DT
        dir_rad = deg2rad(self.objlist[i].direction)
        a_rad = deg2rad(a)
        fxy = f * 100 * math.cos(a_rad)
        fd = f * 100 * math.sin(a_rad)
        self.objlist[i].vx += (fxy * math.sin(dir_rad) - K * self.objlist[i].vx) * DT
        self.objlist[i].vy += (fxy * math.cos(dir_rad) - K * self.objlist[i].vy) * DT
        self.objlist[i].vd += (-fd - K * self.objlist[i].vd) * DT
        self.objlist[i].x += self.objlist[i].vx * DT
        self.objlist[i].y -= self.objlist[i].vy * DT
        #self.objlist[i].direction = rad2deg(math.atan2(self.objlist[i].vx, self.objlist[i].vy))
        self.objlist[i].direction += self.objlist[i].vd * DT

    def step(self):
        f, a = self.fighter_pyr.move()
        self.update(0, f, a)
        f, a = self.fighter_com.move()
        self.update(1, f, a)

        if self.fighter_pyr.launch() and not self.objlist[2].is_active:
            self.objlist[2].activate(self.objlist[0])
        if self.objlist[2].is_active:
            a = max(-45, min(45, self.missile_pyr.move()))
            self.update(2, 1, a)
            self.objlist[2].lifetime -= 1
            if self.objlist[2].lifetime <= 0:
                self.objlist[2].deactivate()

        if self.fighter_com.launch() and not self.objlist[3].is_active:
            self.objlist[3].activate(self.objlist[1])
        if self.objlist[3].is_active:
            a = self.missile_com.move()
            self.update(3, 1, a)
            self.objlist[3].lifetime -= 1
            if self.objlist[3].lifetime <= 0:
                self.objlist[3].deactivate()

        self.check_collisions()
        
        return {
            "fighters": [
                { "x": obj.x, "y": obj.y, "direction": deg2rad(obj.direction) } for obj in self.objlist[:2]
            ],
            "missiles": [
                { "x": obj.x, "y": obj.y, "direction": deg2rad(obj.direction) } for obj in self.objlist[2:] if obj.is_active
            ],
        }
    
    def check_collisions(self):
        dead = [False, False]
        for i in range(2):
            if self.objlist[i].x < 0 or self.objlist[i].x > SIZE_X or self.objlist[i].y < 0 or self.objlist[i].y > SIZE_Y:
                dead[i] = True
            for j in range(2, 4):
                if self.objlist[i].distance(self.objlist[j]) < COLLISION_SIZE:
                    dead[i] = True
        if dead[0]:
            if dead[1]:
                self.time_elapsed = TIME_LIMIT
            else:
                self.pyr_wins = False
        elif dead[1]:
            self.pyr_wins = True
        for i in range(2, 4):
            if self.objlist[i].x < 0 or self.objlist[i].x > SIZE_X or self.objlist[i].y < 0 or self.objlist[i].y > SIZE_Y:
                self.objlist[i].deactivate()

    def is_finished(self):
        self.time_elapsed += 1
        return self.pyr_wins is not None or self.time_elapsed >= TIME_LIMIT
    
    def get_result(self):
        return self.pyr_wins
    #def run_game(self):
    #    while self.time_elapsed < TIME_LIMIT and self.pyr_wins is None:
    #        yield self.step()
    #        self.time_elapsed += 1
    #        time.sleep(0.1)