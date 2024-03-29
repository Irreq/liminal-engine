#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# File: demo.py
# Author: Irreq
# Date: 10/12-2023
# Version: 2.0
from __future__ import annotations
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
DEBUG: int = 0

COLOR_CURSOR: Color = (50, 50, 50)

SCREEN_AUTO_RESOLUTION: bool = False
SCREEN_FRAME_RATE: int = 60  # How often to render the scene
SCREEN_TILE_SIZE: int = 50  # Pixel width during start

TIME_OUT_DURATION: float = 0.2  # Time waiting between events

DEPTH_MAX: int = 20  # Max Manhattan distance
DEPTH_MIN: int = 1  # Min Manhattan distance
EPSILON: float = 1e-4  # Prevent DivisionByZeroError
DISTANCE_MAX: float = (2 * DEPTH_MAX**2) ** 0.5  # Hypothenuse length


MOUSE_SENSITIVITY: int = 20  # Increment on each mouse movement
MOUSE_INVERTED_SCROLL: bool = True  # If scroll wheel should invert

TILE_SPEED: int = 10  # How many tiles per second to travel
TILE_SIZE_MIN: int = 10  # How small a single tile may be
TILE_SIZE_MAX: int = 200  # How large a single tile may be

WARP: bool = True  # Warp 3D effect
WARP_MAGIC_NUMBER: float = 1.0
WARP_DEPTH_RATIO: float = 0.9  # How much to use distance over depth when warping

TEXT_MAX_WIDTH: int = 20  # Number of character that a single tile may hold
TEXT_FONT_FAMILY: str = pygame.font.get_default_font()
TEXT_FONT_SIZE: int = 50  # Size of text

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

# Set up font from constants
font = pygame.font.SysFont(TEXT_FONT_FAMILY, TEXT_FONT_SIZE)

# Text input for demo application
manager = TextInputManager(validator=lambda inputText: len(inputText) <= TEXT_MAX_WIDTH)
editor = TextInputVisualizer(manager=manager, font_object=font)

# Set up color-ranges for smooth transitions
colorManagerGrid = ColorManager(DEPTH_MIN)
colorManagerText = ColorManager(DEPTH_MIN, settings=randomColorSettings())

# Helper function for clamping a value
clamp = lambda value, lower, upper: max(lower, min(value, upper))


def toggleEngineMode(engine: Engine, mode: EngineMode) -> None:
    """Toggles mode for Engine between Normal and 'mode'

    :param engine: Engine instance
    :param mode: EngineMode
    """
    if engine.getMode() == mode:
        mode = EngineMode.NORMAL

    engine.setMode(mode)


class Application:
    """Demo application for testing the capabillities of the engine and how the
    nodes interact.
    """

    def __init__(self, engine: Engine):
        """Initiate an instance of the application (no more than one)

        :param engine: your engine instance
        """
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

        self.engine.setDrawer(self.render)
        self.writer = False

        self.clock = pygame.time.Clock()

        n: int = self.engine.getDepth() + 3
        self.colors = colorManagerGrid.computeRange(n)
        self.colors2 = colorManagerText.computeRange(n)

        self.initial_key_repeat = pygame.key.get_repeat()
        self.writing_key_repeat = (200, 25)

    def changeDepth(self, depth: int) -> None:
        """Wrapper function to update the state of the app while updating the
        engine aswell.

        :param depth: a value between DEPTH_MIN and DEPTH_MAX
        """
        self.engine.setDepth(depth)
        self.can_draw = True
        n: int = self.engine.getDepth() + 3
        self.colors = colorManagerGrid.computeRange(n)
        self.colors2 = colorManagerText.computeRange(n)

    def handle_events(self) -> None:
        """Application-mode event distributor"""
        if self.writer:
            self.handle_events_editor()
        else:
            self.handle_events_app()

    def handle_events_editor(self) -> None:
        """Event handler for text input"""
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYUP and event.key in (
                pygame.K_RETURN,
                pygame.K_ESCAPE,
            ):
                pygame.key.set_repeat(*self.initial_key_repeat)
                self.writer = False

                if editor.value == "":
                    self.engine.getNode().setData(None)
                else:
                    self.engine.getNode().setData(editor.value)

                return

        editor.update(events)

        self.can_draw = True

    def handle_events_app(self) -> None:
        """General application event handling"""
        rotation: int = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEWHEEL:  # Rotate
                rotation: int = event.y

            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:  # Left click
                    if self.engine.getMode() != EngineMode.READ_ONLY:
                        self.engine.getNode().toggleLock()

                elif pygame.mouse.get_pressed()[2]:  # Right click
                    toggleEngineMode(self.engine, EngineMode.LIMINAL)

                self.can_draw = True

            elif event.type == pygame.KEYUP:
                draw = True
                if event.key == pygame.K_r:  # Toggle Read-Only Mode
                    toggleEngineMode(self.engine, EngineMode.READ_ONLY)
                elif event.key == pygame.K_l:  # Toggle Liminal Mode
                    toggleEngineMode(self.engine, EngineMode.LIMINAL)
                elif event.key == pygame.K_n:  # Toggle Normal Mode
                    toggleEngineMode(self.engine, EngineMode.NORMAL)
                elif event.key == pygame.K_RETURN:
                    editor.value = self.engine.getNode().getData() or ""
                    self.engine.getNode().setData(None)
                    self.writer = True
                    editor.font_color = self.colors2[-1]
                    pygame.key.set_repeat(*self.writing_key_repeat)
                    return

                elif event.key == pygame.K_SPACE:  # Lock current Node
                    if self.engine.getMode() != EngineMode.READ_ONLY:
                        self.engine.getNode().toggleLock()
                elif event.key == pygame.K_ESCAPE:  # Stop program
                    self.running = False
                    return
                elif event.key == pygame.K_h:
                    self.find_home = not self.find_home
                elif event.key == pygame.K_i:  # Insert new Node
                    self.engine.insert()
                elif event.key == pygame.K_v:  # Untangle graph (best effort)
                    self.engine.untangle()
                elif event.key == pygame.K_p:  # Prune
                    self.engine.prune()
                elif event.key == pygame.K_c:  # Random color-theme
                    n: int = self.engine.getDepth() + 3
                    colorManagerGrid.settings = randomColorSettings(n)
                    self.colors = colorManagerGrid.computeRange(n)

                    colorManagerText.settings = randomColorSettings(n)
                    self.colors2 = colorManagerText.computeRange(n)

                elif event.key == pygame.K_y:  # serialize program
                    path: str | None = create_file()
                    if path is not None:
                        Engine.serialize(self.engine, path)

                elif event.key == pygame.K_u:  # serialize program
                    path: str | None = browse_file()
                    if path is not None:
                        self.engine = Engine.deserialize(path)

                elif event.key == pygame.K_t:  # Straighten out graph optimization
                    self.engine.optimize()

                # elif event.key == pygame.K_b:  # Debugging purposes
                #     self.engine.getNode().setData(self.engine.getNode().getId())
                else:
                    draw = False

                if draw:
                    self.can_draw = True

        keys = pygame.key.get_pressed()

        moveable: bool = keys[pygame.K_LCTRL] or True

        if rotation:
            if keys[pygame.K_LCTRL]:
                self.size = clamp(
                    self.size + MOUSE_SENSITIVITY * rotation,
                    TILE_SIZE_MIN,
                    TILE_SIZE_MAX,
                )

            elif keys[pygame.K_LALT]:
                depth: int = self.engine.getDepth()

                depth = clamp(depth + rotation, DEPTH_MIN, DEPTH_MAX)

                self.changeDepth(depth)

            else:
                if MOUSE_INVERTED_SCROLL:
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

        if amount != 0:
            self.changeDepth(amount)

        up: bool = keys[pygame.K_UP] or keys[pygame.K_w]
        down: bool = keys[pygame.K_DOWN] or keys[pygame.K_s]
        left: bool = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right: bool = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        mouseX, mouseY = pygame.mouse.get_rel()

        if MOUSE_INVERTED_SCROLL:
            mouseY = -mouseY

        if moveable:
            pygame.mouse.set_visible(False)
            self.dy = 2 * (
                self.delta_movement * up
                - self.delta_movement * down
                + mouseY / MOUSE_SENSITIVITY
            )
            self.dx = 2 * (
                self.delta_movement * right
                - self.delta_movement * left
                + mouseX / MOUSE_SENSITIVITY
            )
        else:
            pygame.mouse.set_visible(True)
            self.dx = 0
            self.dy = 0

    def handle_movements(self):
        """Movement logic above engine the engine is discrete so fluid motion is
        translated to discrete steps."""
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
        """Main program loop"""
        while self.running:
            self.clock.tick(SCREEN_FRAME_RATE)
            self.delta_movement = TILE_SPEED / (self.clock.get_fps() + EPSILON)
            self.handle_events()
            self.handle_movements()
            if self.can_draw:
                self.render()
                self.can_draw = False

        pygame.quit()

    def render(self) -> None:
        """Render the scene and items on the grid

        The cost of this function is vast as it traverses the network on each
        redraw.
        """
        if self.find_home:
            path: List[Node] = self.engine.search(self.engine.start)
        else:
            path: List[Node] = []

        self.window.fill(self.colors[0])
        dx: float = self.x / 2
        dy: float = self.y / 2

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
                    - WARP_DEPTH_RATIO * distance
                    - (1 - WARP_DEPTH_RATIO) * (1 - (depth - n) / DEPTH_MAX)
                )

                diff = clamp(diff, 0, diff)

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

        pygame.display.flip()


if __name__ == "__main__":
    depthStart: int = 15
    engine = Engine(EngineMode.NORMAL, depthStart)
    app = Application(engine)

    app.loop()
