#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# File: demo.py
# Author: Irreq
# Date: 10/12-2022
# Version: 2.0

import pygame

from liminal_engine import *

import numpy as np
import cv2
import math

# initiate pygame and give permission
# to use pygame's functionality.
pygame.init()
pygame.font.init()

X, Y = 1000, 1000

# Colors
BACKGROUND = (10, 0, 10)
TILE = (255, 255, 255)
BLUR = (20, 20, 0)
NEIGHBOR = (200, 200, 200)

# Settings
TILE_SIZE = 130

FRAME_RATE = 200 # 60 #240

SPEED = 5 # How many tiles per second to travel
RANGE = 6 # How far to render

# Change this to get a cool effect ;)
inverted = False


POS_X = 0
POS_Y = 0
EPSILON = 0.001 # Prevent DivisionByZeroError

def create_hole(width: int, height: int, color: tuple[3]=(0, 0, 0)) -> str:

    grid = np.zeros((X, Y, 4), dtype = int)

    half_x = int(X / 2)
    half_y = int(Y / 2)

    radius = (X + Y ) / 2 / 2

    for x in range(X):
        for y in range(Y):
            d = math.dist((half_x, half_y), (x, y))

            d /= radius

            if d > 1:
                grid[x][y][3] = 255

            else:
                grid[x][y][3] = int(d**0.8 * 255)

    # Must reverse due to BGR-RGBa
    for i, c in enumerate(color[::-1]):

        grid[:,:,i] = c

    file = "darkness.png"
    cv2.imwrite(file, grid.astype(int))

    return file



window = pygame.display.set_mode((X, Y))
clock = pygame.time.Clock()

# Load modules
font = pygame.font.SysFont("Comic Sans MS", 50)

clock = pygame.time.Clock()

dark_mask = create_hole(X, Y, BLUR)

fog = pygame.image.load(dark_mask).convert_alpha()

img = pygame.transform.scale(fog, (X, Y))


def draw(engine: Engine, dx: int, dy: int):
    window.fill(BACKGROUND)
    xt, yt = get_position(engine.node)

    for tmp_node in engine.nearby_norm.values():
        x, y = get_position(tmp_node)

        if len(get_neighbors(tmp_node)) > 9:
            print("Panic")

        color = TILE
        if tmp_node.data != {}:
            color = (56, 64, 54)

        d = math.dist((0, 0), (x-xt-dx, y-yt+dy))

        a = 1 / 15

        if inverted:
            a *= -1

        diff = -a * d + 1

        nrect = pygame.Rect(0, 0, TILE_SIZE * diff, TILE_SIZE * diff)
        nrect.center = window.get_rect().center
        nrect.x += (x-xt-dx)*TILE_SIZE*(diff+a) - POS_X
        nrect.y += (y-yt+dy)*TILE_SIZE*(diff+a) - POS_Y
        pygame.draw.rect(window, color, nrect)

    pygame.draw.circle(
        window,
        (255, 0, 0),
        (rect.center[0] - POS_X, rect.center[1] - POS_Y),
        TILE_SIZE / 20
    )

    
    window.blit(img, (0-POS_X, 0-POS_Y))

    text_surface = font.render(f'Liminal: {get_position(engine.node)} ({int(clock.get_fps())}FPS)', False, (0, 255, 0))
    window.blit(text_surface, (0,0))
    pygame.display.flip()


grid = create_empty_grid((0, 0), 30, 20)

# grid = {(0, 0):create_node((0, 0))}

# Initiate the engine on starting position
engine = Engine(grid[(0, 0)], RANGE-EPSILON)

rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
rect.center = window.get_rect().center


# Temporary values, do not edit
running = True
y, x = 0, 0
change = 0.2
last_x = 0
last_y = 0
draw_now = True

while running:
    clock.tick(FRAME_RATE)

    change = SPEED / (clock.get_fps() + EPSILON)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            running = False
            break
    keys = pygame.key.get_pressed()

    if keys[pygame.K_ESCAPE]:
        running = False
        pygame.quit()

    up = (keys[pygame.K_UP] or keys[pygame.K_w])
    down = (keys[pygame.K_DOWN] or keys[pygame.K_s])
    left = (keys[pygame.K_LEFT] or keys[pygame.K_a])
    right = (keys[pygame.K_RIGHT] or keys[pygame.K_d])

    dy = change * up - change * down
    dx = change * right - change * left

    if dy or dx:
        draw_now = True

    x += dx
    y += dy

    if not last_x - 1 < x < last_x + 1 or \
       not last_y - 1 < y < last_y + 1:

        angle = get_angle(0, 0, (x - last_x), (y - last_y))

        engine.traverse(angle)

        last_x = round(x, 0)
        last_y = round(y, 0)

    if draw_now:
        draw(engine, x - last_x, y - last_y)
        draw_now = False

pygame.quit()