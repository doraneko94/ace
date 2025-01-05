import math

class Fighter:
    def __init__(self, core):
        self.core = core

    def move(self):
        return 0.5, 45
    
    def launch(self):
        return True
    
class Missile:
    def __init__(self, core):
        self.core = core

    def move(self):
        return 0