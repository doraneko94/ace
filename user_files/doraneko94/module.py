import math

class Fighter:
    def __init__(self, core):
        self.core = core

    def move(self):
        position, _ = self.core.sense()
        f, a = 1, 0
        if position.x < 100 or position.x > 700 or position.y < 100 or position.y > 500:
            a = 45
        return f, a
    
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
        return direction