#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# File: demo.py
# Author: Irreq
# Date: 10/12-2023
# Version: 2.0
from __future__ import annotations
from abc import abstractmethod
from typing import Generator, Callable, Dict, Tuple, Any, List, Set


import pygame

import math
import time
import subprocess

from direction import MOVEMENT_MAP_INVERTED, Direction, Position, deltaPosition

from node import ORIGO, Engine, EngineMode, Node, DFSWithPath
from color import (
    Color,
    ColorManager,
    randomColorSettings,
)

settings2 = randomColorSettings()

gridColorManager = ColorManager(10)
textColorManager = ColorManager(10, settings=randomColorSettings())
# initiate pygame and give permission
# to use pygame's functionality.
pygame.init()
pygame.font.init()
pygame.mixer.quit()

pygame.event.set_grab(True)

DEBUG: int = 1


PATH_HOME_COLOR: Color = (0, 150, 255)
CURSOR_COLOR: Color = (50, 50, 50)


# Settings
if DEBUG:
    X: int = 800
    Y: int = 800
else:
    a = pygame.display.get_desktop_sizes()
    X, Y = a[0]
    # X: int = 1920
    # Y: int = 1080

TILE_SIZE: int = 50  # Pixel width

FRAME_RATE: int = 60
SPEED: int = 10  # How many tiles per second to travel

POS_X: int = 0
POS_Y: int = 0
EPSILON: float = 1e-4  # Prevent DivisionByZeroError

MOUSE_SENSITIVITY: int = 20
TIME_OUT_DURATION: float = 0.2

INVERTED_SCROLL: bool = True

FIND_HOME: bool = False

MIN_SIZE: int = 10
MAX_SIZE: int = 200


def browse_file():
    command = "zenity --file-selection"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    output, _ = process.communicate()
    selected_file = output.decode("utf-8").strip()
    return selected_file if selected_file else None


def create_file():
    cmd = 'zenity --entry --title "Create New File" --text "Enter the new name:" --entry-text ""'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output, _ = process.communicate()
    selected_file = output.decode("utf-8").strip()
    return selected_file if selected_file else None


# selected_file = browse_file()
#
# if selected_file:
#     print("Selected file:", selected_file)
# else:
#     print("No file selected.")
#
# import time
#
# time.sleep(3)
# exit()
font = pygame.font.SysFont("Comic Sans MS", 50)
initial_key_repeat = pygame.key.get_repeat()
writing_key_repeat = (200, 25)
# Pygame now allows natively to enable key repeat:

from pygame_textinput import TextInputManager, TextInputVisualizer

manager = TextInputManager(validator=lambda input: len(input) <= 20)


def engineToggleMode(engine: Engine, mode: EngineMode) -> None:
    if engine.getMode() == mode:
        mode = EngineMode.NORMAL

    engine.setMode(mode)


class Application:
    def __init__(self, engine: Engine):
        # pygame = pygame
        pygame.event.set_grab(True)  # Grab mouse
        pygame.mouse.set_visible(False)
        self.engine: Engine = engine
        self.running: bool = True
        self.find_home: bool = False
        self.size: int = TILE_SIZE

        self.x: float = 0.0
        self.y: float = 0.0
        self.can_draw: bool = True

        self.window = pygame.display.set_mode((X, Y))
        self.rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        self.rect.center = self.window.get_rect().center
        self.middleX = self.rect.center[0]
        self.middleY = self.rect.center[1]
        # Load modules
        self.font = font

        self.engine.setDrawer(self.draw)
        self.writer = False
        self.ed = TextInputVisualizer(manager=manager, font_object=self.font)

    def handle_events(self) -> None:
        if self.writer:
            self.handle_events_editor()
        else:
            self.handle_events_app()

    def handle_events_editor(self) -> None:
        events = pygame.event.get()

        self.ed.update(events)
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                pygame.key.set_repeat(*initial_key_repeat)
                self.writer = False

                if self.ed.value == "":
                    self.engine.getNode().setData(None)
                else:
                    self.engine.getNode().setData(self.ed.value)

        self.can_draw = True

    def handle_events_app(self) -> None:
        rotation: int = 0
        # print(pygame.event.get())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                self.running = False

            elif event.type == pygame.MOUSEWHEEL:  # Rotate
                rotation: int = event.y

            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:  # Left click
                    if self.engine.getMode() != EngineMode.READ_ONLY:
                        self.engine.getNode().toggleLock()

                elif pygame.mouse.get_pressed()[2]:  # Right click
                    engineToggleMode(self.engine, EngineMode.LIMINAL)

                self.can_draw = True

            elif event.type == pygame.KEYUP:
                draw = True
                if event.key == pygame.K_r:  # Toggle Read-Only Mode
                    engineToggleMode(self.engine, EngineMode.READ_ONLY)
                elif event.key == pygame.K_l:  # Toggle Liminal Mode
                    engineToggleMode(self.engine, EngineMode.LIMINAL)
                elif event.key == pygame.K_n:  # Toggle Normal Mode
                    engineToggleMode(self.engine, EngineMode.NORMAL)
                elif event.key == pygame.K_RETURN:
                    self.ed.value = self.engine.getNode().getData() or ""
                    self.engine.getNode().setData(None)
                    self.writer = True
                    self.ed.font_color = self.colors2[-1]
                    pygame.key.set_repeat(*writing_key_repeat)
                    print("Change to write")
                    return

                elif event.key == pygame.K_SPACE:  # Lock current Node
                    if self.engine.getMode() != EngineMode.READ_ONLY:
                        self.engine.getNode().toggleLock()
                elif event.key == pygame.K_ESCAPE:  # Stop program
                    self.running = False
                    return
                elif event.key == pygame.K_h:
                    self.find_home = not self.find_home
                elif event.key == pygame.K_i:  # Lock current Node
                    self.engine.insert()
                elif event.key == pygame.K_v:  # Lock current Node
                    self.engine.untangle()
                elif event.key == pygame.K_p:  # Prune
                    self.engine.prune()
                elif event.key == pygame.K_c:
                    n: int = self.engine.getDepth() + 3
                    gridColorManager.settings = randomColorSettings(n)
                    self.colors = gridColorManager.computeRange(n)

                    textColorManager.settings = randomColorSettings(n)
                    self.colors2 = textColorManager.computeRange(n)

                elif event.key == pygame.K_b:  # Lock current Node
                    self.engine.getNode().setData(self.engine.getNode().getId())

                elif event.key == pygame.K_y:  # serialize program
                    path: str | None = create_file()
                    if path is not None:
                        Engine.serialize(self.engine, path)
                    return

                elif event.key == pygame.K_u:  # serialize program
                    path: str | None = browse_file()
                    if path is not None:
                        self.engine = Engine.deserialize(path)

                elif event.key == pygame.K_t:  # serialize program
                    self.engine.optimize()
                else:
                    draw = False

                if draw:
                    self.can_draw = True

        keys = pygame.key.get_pressed()

        moveable: bool = keys[pygame.K_LCTRL] or True

        if rotation:
            if keys[pygame.K_LCTRL]:
                self.size += MOUSE_SENSITIVITY * rotation

                if self.size < MIN_SIZE:
                    self.size = MIN_SIZE
                elif self.size > MAX_SIZE:
                    self.size = MAX_SIZE
            else:
                if INVERTED_SCROLL:
                    rotation = -rotation
                if self.engine.tryRotate(rotation):
                    self.can_draw = True

        if moveable:
            rotation: int = 1 * (keys[pygame.K_e]) - 1 * (keys[pygame.K_q])
            if rotation:
                if self.engine.tryRotate(rotation):
                    self.can_draw = True
                    time.sleep(TIME_OUT_DURATION)

        if keys[pygame.K_BACKSPACE]:
            if self.engine.remove():
                self.can_draw = True
                time.sleep(TIME_OUT_DURATION)
                self.x = 0
                self.y = 0
                return

        amount: int = (
            0
            or 1 * keys[pygame.K_1]
            or 2 * keys[pygame.K_2]
            or 3 * keys[pygame.K_3]
            or 4 * keys[pygame.K_4]
            or 5 * keys[pygame.K_5]
            or 6 * keys[pygame.K_6]
            or 7 * keys[pygame.K_7]
            or 8 * keys[pygame.K_8]
            or 9 * keys[pygame.K_9]
        )
        # amount = 0

        if amount != 0:
            self.engine.setDepth(amount)
            self.can_draw = True
            n: int = self.engine.getDepth() + 3
            self.colors = gridColorManager.computeRange(n)
            self.colors2 = textColorManager.computeRange(n)

        up: bool = keys[pygame.K_UP] or keys[pygame.K_w]
        down: bool = keys[pygame.K_DOWN] or keys[pygame.K_s]
        left: bool = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right: bool = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        mx, my = pygame.mouse.get_rel()

        if INVERTED_SCROLL:
            my = -my

        if moveable:
            pygame.mouse.set_visible(False)
            self.dy = 2 * (
                self.delta_movement * up
                - self.delta_movement * down
                + my / MOUSE_SENSITIVITY
            )
            self.dx = 2 * (
                self.delta_movement * right
                - self.delta_movement * left
                + mx / MOUSE_SENSITIVITY
            )
        else:
            pygame.mouse.set_visible(True)
            self.dx = 0
            self.dy = 0

    def handle_movements(self):
        if not self.dy and not self.dx:
            return

        self.x += self.dx
        self.y += self.dy

        diffX: int = -1 * (self.x < -1) + 1 * (self.x > 1)
        diffY: int = -1 * (self.y < -1) + 1 * (self.y > 1)
        newPosition: Position = (diffX, diffY)
        if newPosition in MOVEMENT_MAP_INVERTED:
            direction: Direction = MOVEMENT_MAP_INVERTED[newPosition]
            moved: bool = self.engine.move(direction)

            if not moved:
                self.x -= self.dx
                self.y -= self.dy

                return

        # Maybe undo movement
        if diffX != 0:
            self.x = -diffX
        if diffY != 0:
            self.y = -diffY

        self.can_draw = True

    def loop(self) -> None:
        self.clock = pygame.time.Clock()
        self.draw()
        while self.running:
            self.clock.tick(FRAME_RATE)
            self.delta_movement = SPEED / (self.clock.get_fps() + EPSILON)
            self.can_draw = False  # Reset
            self.handle_events()
            self.handle_movements()
            if self.can_draw:
                self.draw()

        pygame.quit()

    @abstractmethod
    def draw(self) -> None:
        pass


class Writer(Application):
    def __init__(self, engine: Engine, width=100, height=10, fontname=None):
        super().__init__(engine)

        n: int = self.engine.getDepth() + 3
        self.colors = gridColorManager.computeRange(n)
        self.colors2 = textColorManager.computeRange(n)

        # self.width = width
        # self.height = height
        # self.font = pygame.font.Font(
        #     fontname, Writer.getMaxFontSize(fontname, lineheight=height)
        # )

    @staticmethod
    def getMaxFontSize(fontname, width=None, lineheight=None, line=None):
        def font(size):
            return pygame.font.Font(fontname, size)

        fontsize = float("inf")  # inf

        if width:
            aproxsize = width * 1000 // font(1000).size(line)[0]
            while font(aproxsize).size(line)[0] < width:
                aproxsize += 1
            while font(aproxsize).size(line)[0] > width:
                aproxsize -= 1
            fontsize = min(aproxsize, fontsize)

        if lineheight:
            aproxsize = lineheight * 4 // 3
            while font(aproxsize).get_linesize() < lineheight:
                aproxsize += 1
            while font(aproxsize).get_linesize() > lineheight:
                aproxsize -= 1
            fontsize = min(aproxsize, fontsize)
        return fontsize

    def draw(self):
        if self.find_home:
            path: List[Node] = self.engine.search(self.engine.start)
        else:
            path: List[Node] = []
        # self.window.fill(BACKGROUND)
        self.window.fill(self.colors[1])
        kx: float = self.x / 2
        ky: float = self.y / 2

        mode: EngineMode = self.engine.getMode()

        if mode != EngineMode.NORMAL:
            if mode == EngineMode.READ_ONLY:
                text = "Read Only!"
            elif mode == EngineMode.LIMINAL:
                text = "Liminal Mode!"
            else:
                raise ValueError("Invalid mode: ", mode)
            text_surface = self.font.render(text, False, self.colors[-1])  # TEXT_COLOR)
            self.window.blit(text_surface, (0, 0))

        # text_surface = self.font.render(
        #     f"{round(self.clock.get_fps())}fps", False, self.colors[-1]
        # )  # TEXT_COLOR)
        # self.window.blit(text_surface, (X - 150, 0))

        world: Dict[Position, Tuple[int, Node, Position]] = {}

        depth: int = self.engine.getDepth()
        size: int = self.size

        maxDistance: float = (2 * depth**2) ** 0.5

        def BFSDraw(start: Node):
            to_visit: List[Tuple[Node, Position]] = [(start, ORIGO)]

            visited = []

            for i in range(depth):
                nextVisit = []

                for node, position in to_visit:
                    visited.append(node)
                    for neighborDirection, neighbor in node.items():
                        if neighbor not in visited:
                            nextVisit.append(
                                (neighbor, deltaPosition(neighborDirection, position))
                            )

                to_visit = nextVisit

        def recDraw(
            node: Node,
            parent: Node,
            n: int,
            previousPosition: Position,
            currentPosition: Position,
            visited: List[Node],
        ):
            if n < 0:
                return

            # position: Position = (
            #     self.middleX + (currentPosition[0] - kx) * size,
            #     self.middleY - (currentPosition[1] - ky) * size,
            # )

            if 1:
                distance: float = (
                    math.dist(ORIGO, (currentPosition[0] - kx, currentPosition[1] - ky))
                    / maxDistance
                )

                ratio = 0.9

                diff = 1 - ratio * distance - (1 - ratio) * (1 - n / depth)

                # diff = ratio * (1 - distance - n / depth) + n / depth

                if diff < 0:
                    diff = 0
            else:
                diff = 1.0

            deltaSize: float = size * diff

            position: Position = (
                self.middleX + (currentPosition[0] - kx) * deltaSize,
                self.middleY - (currentPosition[1] - ky) * deltaSize,
            )
            for direction, neighbor in node.items():
                if neighbor not in visited:
                    recDraw(
                        neighbor,
                        node,
                        n - 1,
                        position,
                        deltaPosition(direction, currentPosition),
                        [node] + visited,
                    )

            if node != parent:
                pygame.draw.line(
                    self.window,
                    self.colors[n + 2],  # color,
                    position,
                    previousPosition,
                    int(deltaSize / 3),  # size // 8,
                )

            if node.isLocked():
                pygame.draw.circle(
                    self.window,
                    self.colors[0],  # LOCKED_COLOR,
                    position,
                    deltaSize / 8,
                )

            data: Any = node.getData()
            if data is not None:
                self.window.blit(
                    self.font.render(
                        data,
                        False,
                        self.colors2[n + 2],
                    ),
                    position,
                )

        startNode: Node = self.engine.getNode()

        recDraw(startNode, startNode, depth, ORIGO, ORIGO, [])
        if self.writer:
            self.window.blit(
                self.ed.surface,
                (self.middleX - kx * size, self.middleY + ky * (size)),
            )

        pygame.draw.circle(
            self.window,
            CURSOR_COLOR,
            (self.middleX - POS_X, self.middleY - POS_Y),
            size / 20,
        )
        pygame.display.flip()


if __name__ == "__main__":
    engine = Engine(EngineMode.NORMAL, 16)
    app = Writer(engine)

    app.loop()
