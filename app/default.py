class Fighter:
    def __init__(self, core):
        self.core = core

    def move(self):
        position, outputs = self.core.sense()
        f, a = 0, 0
        return f, a
    
    def launch(self):
        position, outputs = self.core.sense()
        is_launch = False
        return is_launch
    
class Missile:
    def __init__(self, core):
        self.core = core

    def move(self):
        position, outputs = self.core.sense()
        direction = 0.0
        return direction