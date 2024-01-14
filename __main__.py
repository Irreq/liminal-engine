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
from pygame_textinput import TextInputManager, TextInputVisualizer

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


# initiate pygame and give permission
# to use pygame's functionality.
pygame.init()
pygame.font.init()
pygame.mixer.quit()

pygame.event.set_grab(True)  # Grab mouse
pygame.mouse.set_visible(False)

# ---- Settings ----
DEBUG: int = False

SCREEN_AUTO_RESOLUTION: bool = False


COLOR_PATH_HOME: Color = (0, 150, 255)
COLOR_CURSOR: Color = (50, 50, 50)


SCREEN_TILE_SIZE: int = 50  # Pixel width

FRAME_RATE: int = 60
SPEED: int = 10  # How many tiles per second to travel
START_DEPTH: int = 16
DEPTH_MAX: int = 20
DEPTH_MIN: int = 1
EPSILON: float = 1e-4  # Prevent DivisionByZeroError
DISTANCE_MAX: float = (2 * DEPTH_MAX**2) ** 0.5


MOUSE_SENSITIVITY: int = 20
TIME_OUT_DURATION: float = 0.2

INVERTED_SCROLL: bool = True

FIND_HOME: bool = False

MIN_SIZE: int = 10  # in pixels
MAX_SIZE: int = 200

WARP: bool = True
WARP_MAGIC_NUMBER: float = 1.0
DEPTH_WARP_RATIO: float = 0.9  # How much to use distance over depth when warping
TEXT_MAX_WIDTH: int = 20
TEXT_FONT_FAMILY: str = pygame.font.get_default_font()
TEXT_FONT_SIZE: int = 50

if DEBUG:
    X: int = 800
    Y: int = 800
elif SCREEN_AUTO_RESOLUTION:
    resolutions = pygame.display.get_desktop_sizes()
    X, Y = resolutions[0]  # Pick the first
else:
    X: int = 1920
    Y: int = 1080


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
font = pygame.font.SysFont(TEXT_FONT_FAMILY, TEXT_FONT_SIZE)
initial_key_repeat = pygame.key.get_repeat()
writing_key_repeat = (200, 25)
# Pygame now allows natively to enable key repeat:


manager = TextInputManager(validator=lambda input: len(input) <= TEXT_MAX_WIDTH)

editor = TextInputVisualizer(manager=manager, font_object=font)

colorManagerGrid = ColorManager(START_DEPTH)
colorManagerText = ColorManager(START_DEPTH, settings=randomColorSettings())


def engineToggleMode(engine: Engine, mode: EngineMode) -> None:
    if engine.getMode() == mode:
        mode = EngineMode.NORMAL

    engine.setMode(mode)


class Application:
    def __init__(self, engine: Engine):
        self.engine: Engine = engine
        self.running: bool = True
        self.find_home: bool = False
        self.size: int = SCREEN_TILE_SIZE

        self.x: float = 0.0
        self.y: float = 0.0
        self.can_draw: bool = True

        self.window = pygame.display.set_mode((X, Y))
        self.rect = pygame.Rect(0, 0, SCREEN_TILE_SIZE, SCREEN_TILE_SIZE)
        self.rect.center = self.window.get_rect().center
        self.middleX = self.rect.center[0]
        self.middleY = self.rect.center[1]
        # Load modules

        self.engine.setDrawer(self.draw)
        self.writer = False

    def changeDepth(self, depth: int):
        self.engine.setDepth(depth)
        self.can_draw = True
        n: int = self.engine.getDepth() + 3
        self.colors = colorManagerGrid.computeRange(n)
        self.colors2 = colorManagerText.computeRange(n)

    def handle_events(self) -> None:
        if self.writer:
            self.handle_events_editor()
        else:
            self.handle_events_app()

    def handle_events_editor(self) -> None:
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYUP and event.key in (
                pygame.K_RETURN,
                pygame.K_ESCAPE,
            ):
                pygame.key.set_repeat(*initial_key_repeat)
                self.writer = False

                if editor.value == "":
                    self.engine.getNode().setData(None)
                else:
                    self.engine.getNode().setData(editor.value)

                return

        editor.update(events)

        self.can_draw = True

    def handle_events_app(self) -> None:
        rotation: int = 0
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
                    editor.value = self.engine.getNode().getData() or ""
                    self.engine.getNode().setData(None)
                    self.writer = True
                    editor.font_color = self.colors2[-1]
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
                    colorManagerGrid.settings = randomColorSettings(n)
                    self.colors = colorManagerGrid.computeRange(n)

                    colorManagerText.settings = randomColorSettings(n)
                    self.colors2 = colorManagerText.computeRange(n)

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

            elif keys[pygame.K_LALT]:
                depth: int = self.engine.getDepth()

                depth += rotation

                if depth < DEPTH_MIN:
                    depth = DEPTH_MIN
                elif depth > DEPTH_MAX:
                    depth = DEPTH_MAX

                self.changeDepth(depth)

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
            self.changeDepth(amount)

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
        self.colors = colorManagerGrid.computeRange(n)
        self.colors2 = colorManagerText.computeRange(n)

    def draw(self):
        if self.find_home:
            path: List[Node] = self.engine.search(self.engine.start)
        else:
            path: List[Node] = []

        self.window.fill(self.colors[0])
        dx: float = self.x / 2
        dy: float = self.y / 2

        mode: EngineMode = self.engine.getMode()

        if mode != EngineMode.NORMAL:
            if mode == EngineMode.READ_ONLY:
                text = "Read Only!"
            elif mode == EngineMode.LIMINAL:
                text = "Liminal Mode!"
            else:
                raise ValueError("Invalid mode: ", mode)
            text_surface = font.render(text, False, self.colors[-1])  # TEXT_COLOR)
            self.window.blit(text_surface, (0, 0))

        depth: int = self.engine.getDepth()

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

            if WARP:
                distance: float = (
                    math.dist(ORIGO, (currentPosition[0] - dx, currentPosition[1] - dy))
                    / DISTANCE_MAX
                )

                diff = (
                    WARP_MAGIC_NUMBER
                    - DEPTH_WARP_RATIO * distance
                    - (1 - DEPTH_WARP_RATIO) * (1 - (depth - n) / DEPTH_MAX)
                )

                if diff < 0:  # Clamp negative
                    diff = 0
            else:
                diff = 1.0

            deltaSize: float = self.size * diff

            position: Position = (
                self.middleX + (currentPosition[0] - dx) * deltaSize,
                self.middleY - (currentPosition[1] - dy) * deltaSize,
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
                if node in path:
                    color: Color = self.colors2[n + 2]
                else:
                    color: Color = self.colors[n + 2]
                pygame.draw.line(
                    self.window,
                    color,
                    position,
                    previousPosition,
                    int(deltaSize / 3),
                )

            if node.isLocked():
                pygame.draw.circle(
                    self.window,
                    self.colors[0],
                    position,
                    deltaSize / 8,
                )

            data: Any = node.getData()
            if data is not None:
                self.window.blit(
                    font.render(
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
                editor.surface,
                (self.middleX - dx * self.size, self.middleY + dy * self.size),
            )

        pygame.draw.circle(
            self.window,
            COLOR_CURSOR,
            (self.middleX, self.middleY),
            self.size / 20,
        )
        pygame.display.flip()


if __name__ == "__main__":
    engine = Engine(EngineMode.NORMAL, START_DEPTH)
    app = Writer(engine)

    app.loop()
