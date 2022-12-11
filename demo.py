#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# File: demo.py
# Author: Irreq
# Date: 10/12-2022

import pygame

from liminal_engine import *

# initiate pygame and give permission
# to use pygame's functionality.
pygame.init()
pygame.font.init()

X, Y = 1000, 1000

BACKGROUND = (0, 0, 0)
TILE = (190, 190, 190)

TILE_SIZE = 50

window = pygame.display.set_mode((X, Y))
clock = pygame.time.Clock()

# Load modules
font = pygame.font.SysFont("Comic Sans MS", 50)

fog = pygame.image.load("darkness.png").convert_alpha()
img = pygame.transform.scale(fog, (X, Y))

rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
rect.center = window.get_rect().center

# Create 10 checkpoints
checkpoints = {i:None for i in range(0, 9+1)}

# Create a start position at liminal (0, 0)
start = Node(0, 0)

start.data = "This is start position"

engine = LiminalEngine(start.pointer())

run = True

dx, dy = 0, 0
while run:
    clock.tick(60)

    dx = int(dx)
    dy = int(dy)

    try:
        engine.traverse(dx, dy)
    except:
        pass

    engine.nearby = get_nearby(engine.node, DEPTH)
    px, py = engine.node.get_position()
    engine.rel_nearby = {(xi-px, yi-py):v for (xi, yi), v in engine.nearby.items()}


    dx, dy = 0, 0
    while -1<dx<1 and -1<dy<1:
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False

                elif event.key == pygame.K_SPACE:
                    engine.node = start.pointer()
                    print("Warped home!")

                num = event.key - 48

                if 0<=num<=9:

                    res = checkpoints[num]

                    if res == None:
                        checkpoints[num] = engine.node
                        print(f"Saved checkpoint: {num} at liminal {engine.node.get_position()}")
                    else:
                        engine.node = checkpoints[num]
                        print(f"Warped to checkpoint: {num} at liminal {engine.node.get_position()}")

        keys = pygame.key.get_pressed()

        dx += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])/10
        dy += (keys[pygame.K_DOWN] - keys[pygame.K_UP])/10

        for (x, y) in engine.rel_nearby:
            if engine.rel_nearby[(x, y)].data != []:
                color = (0, 255, 0)
            else:
                color = TILE
            
            nrect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
            nrect.center = window.get_rect().center
            nrect.x += (x-dx)*TILE_SIZE
            nrect.y += (y-dy)*TILE_SIZE
            pygame.draw.rect(window, color, nrect)

        nrect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        nrect.center = window.get_rect().center
        nrect.x -= (dx)*TILE_SIZE
        nrect.y -= (dy)*TILE_SIZE
        pygame.draw.rect(window, TILE, nrect)
        pygame.draw.circle(window,(255, 0, 0),(rect.center),TILE_SIZE/2)

        text_surface = font.render(f'Liminal: {engine.node.get_position()} ({int(clock.get_fps())}FPS)', False, (0, 255, 0))

        # This creates a new surface with text already drawn onto it. At the end you can just blit the text surface onto your main screen.
        window.blit(img, (0, 0))
        window.blit(text_surface, (0,0))

        pygame.display.flip()

pygame.quit()