import math, random

class Fighter:
    def __init__(self, core):
        self.core = core
        self.target = None

    def move(self):
        position, outputs = self.core.sense()
        x, y = 0, 0
        if position.x < 100:
            x += 1
        if position.x > 700:
            x -= 1
        if position.y < 100:
            y += 1
        if position.y > 500:
            y -= 1
        for output in outputs:
            if output.unit >= 2:
                a = math.atan2(output.x, output.y)
                angle = a + position.direction * math.pi / 180
                x -= 0.5 * math.sin(angle)
                y -= 0.5 * math.cos(angle)
        target = 0
        if x != 0 or y != 0:
            self.target = None
            target = math.atan2(x, y) * 180 / math.pi
        else:
            if self.target is None:
                self.target = (random.random() - 0.5) * 360
            target = self.target
        return 1, -max(-90, min(90, target - position.direction))
    
    def launch(self):
        _, outputs = self.core.sense()
        for output in outputs:
            if output.unit == 1:
                return True
        return False
    
class Missile:
    def __init__(self, core):
        self.core = core

    def move(self):
        position, outputs = self.core.sense()
        direction = 0.0
        for output in outputs:
            if output.unit == 1:
                direction = math.atan2(output.x, output.y) * 180 / math.pi
        return -direction