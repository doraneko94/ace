import pygame
import importlib, math, sys
from game.engine import Engine
from game.consts import *

args = sys.argv
if len(args) != 3:
    raise ValueError
module_pyr_path = "user_files." + args[1] + ".module"
module_com_path = "user_files." + args[2] + ".module"

pygame.init()
screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
clock = pygame.time.Clock()

engine = Engine(module_pyr_path, module_com_path)

running = True
while running:
    if engine.is_finished():
        running = False
        break

    screen.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    data = engine.step()

    for fighter, color in zip(data["fighters"], [(0, 0, 255), (255, 0, 0)]):
        pygame.draw.polygon(screen, color, [
            (fighter["x"] + L1 * math.sin(fighter["direction"]), fighter["y"] - L1 * math.cos(fighter["direction"])),
            (fighter["x"] + L2 * math.sin(4 / 3 * math.pi + fighter["direction"]), fighter["y"] - L2 * math.cos(4 / 3 * math.pi + fighter["direction"])),
            (fighter["x"] - L2 * math.sin(4 / 3 * math.pi - fighter["direction"]), fighter["y"] - L2 * math.cos(4 / 3 * math.pi - fighter["direction"])),
        ])

    for fighter in data["missiles"]:
        pygame.draw.polygon(screen, (0, 255, 0), [
            (fighter["x"] + L1 * math.sin(fighter["direction"]), fighter["y"] - L1 * math.cos(fighter["direction"])),
            (fighter["x"] + L2 * math.sin(4 / 3 * math.pi + fighter["direction"]), fighter["y"] - L2 * math.cos(4 / 3 * math.pi + fighter["direction"])),
            (fighter["x"] - L2 * math.sin(4 / 3 * math.pi - fighter["direction"]), fighter["y"] - L2 * math.cos(4 / 3 * math.pi - fighter["direction"])),
        ])

    pygame.display.flip()
    clock.tick(30)

pygame.quit()