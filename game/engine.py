import pygame
from .consts import *
from .structs import *

# test

def run_battle(module_pyr, module_com):
    pygame.init()
    screen = pygame.display.set_mode((sizeX, sizeY))
    clock = pygame.time.Clock()

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
        Object(100, 100, 0, (255, 0, 0), Unit.PYR),
        Object(600, 400, 0, (0, 0, 255), Unit.COM),
        Object(0, 0, 0, (0, 255, 0), Unit.PMI),
        Object(0, 0, 0, (0, 255, 0), Unit.CMI),
    ]

    fighter_pyr = module_pyr.Fighter(Core(objlist[0]))
    fighter_com = module_com.Fighter(Core(objlist[1]))
    missile_pyr = module_pyr.Missile(Core(objlist[2]))
    missile_com = module_com.Missile(Core(objlist[3]))

    objlist[2].deactivate()
    objlist[3].deactivate()

    def update(i, f, a):
        f = max(-1, min(1, f))
        angle = deg2rad(a + objlist[i].direction)
        objlist[i].vx += (f * 100 * math.sin(angle) - K * objlist[i].vx) * dt
        objlist[i].vy += (f * 100 * math.cos(angle) - K * objlist[i].vy) * dt
        objlist[i].x += objlist[i].vx * dt
        objlist[i].y -= objlist[i].vy * dt
        objlist[i].direction = rad2deg(math.atan2(objlist[i].vx, objlist[i].vy))
        objlist[i].draw(screen)

    pyr_wins = None
    c = 0
    while pyr_wins is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return pyr_wins

        screen.fill((0, 0, 0))

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
            pyr_wins = True
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    return pyr_wins