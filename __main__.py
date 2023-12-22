#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# File: demo.py
# Author: Irreq
# Date: 10/12-2023
# Version: 2.0

try:
    import pygame
except ImportError:
    print("Could not resolve Pygame. Is it installed?")
    exit(1)

import time
import subprocess

from direction import MOVEMENT_MAP_INVERTED, Direction

from node import ORIGO, MAX_ORDER, Engine, EngineMode, Node, deltaPos

DEBUG = 0

# initiate pygame and give permission
# to use pygame's functionality.
pygame.init()
pygame.font.init()
pygame.mixer.quit()


# Colors
Color = tuple[int, int, int]

BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)
RED: Color = (255, 0, 0)

NEIGHBOR: Color = (200, 200, 200)
BACKGROUND: Color = BLACK

# Settings
if DEBUG:
    X: int = 1000
    Y: int = 1000
else:
    X: int = 1920
    Y: int = 1080

TILE_SIZE: int = 100

FRAME_RATE: int = 60
SPEED: int = 10  # How many tiles per second to travel
RANGE: int = 6  # How far to render

# Change this to get a cool effect ;)
inverted: bool = False


POS_X: int = 0
POS_Y: int = 0
EPSILON: float = 1e-4  # Prevent DivisionByZeroError

MOUSE_SENSITIVITY: int = 20


NODE_SPACING: float = 1 / 12

DELTA_MOVEMENT: float = SPEED / FRAME_RATE

DEBUG: int = 1


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


class Drawer:
    def __init__(self, pygame):
        self.pygame = pygame
        self.window = self.pygame.display.set_mode((X, Y))
        self.rect = self.pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        self.rect.center = self.window.get_rect().center
        self.middleX = self.rect.center[0]
        self.middleY = self.rect.center[1]
        # Load modules
        self.font = self.pygame.font.SysFont("Comic Sans MS", 50)

    def rec_draw(self, node, n, place, position, parent, visited):
        if position not in place or n > place[position][0]:
            place[position] = (n, node, parent)

        if n == 0:
            return

        for direction, neighbor in node.items():
            if neighbor not in visited:
                self.rec_draw(
                    neighbor,
                    n - 1,
                    place,
                    deltaPos(direction, position),
                    position,
                    [node] + visited,  # Maybe optimized for local search of recent?
                )

    def draw(self):
        path: list[Node] = []  # self.engine.search(self.engine.start)
        self.window.fill(BACKGROUND)
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
            text_surface = self.font.render(
                text,
                False,
                (255, 0, 0),
            )
            self.window.blit(text_surface, (0, 0))

        world = {}

        self.rec_draw(
            self.engine.getNode(), self.engine.getOrder(), world, ORIGO, ORIGO, []
        )

        locks = []
        for child, (n, node, parent) in world.items():
            (x, y) = child
            xc = x - kx
            yc = y - ky
            (x, y) = parent

            xp = x - kx
            yp = y - ky

            c = (n + 1) / 9 * 255
            color = (c, c, c)
            if node in path:
                color = (0, 0, 200)
            if child != parent:
                self.pygame.draw.line(
                    self.window,
                    color,
                    (self.middleX + xc * TILE_SIZE, self.middleY - yc * TILE_SIZE),
                    (self.middleX + xp * TILE_SIZE, self.middleY - yp * TILE_SIZE),
                    1 + (n * 2),
                )

            if node.isLocked():
                locks.append(
                    (
                        self.middleX + xc * TILE_SIZE,
                        self.middleY - yc * TILE_SIZE,
                    )
                )

        for pos in locks:
            self.pygame.draw.circle(
                self.window,
                (200, 0, 0),
                pos,
                8,
            )
        self.pygame.draw.circle(
            self.window,
            (50, 50, 50),
            (self.middleX - POS_X, self.middleY - POS_Y),
            TILE_SIZE / 20,
        )
        self.pygame.display.flip()

    # def olddraw(self):
    #     self.window.fill(BACKGROUND)
    #     neighbors = list(self.engine.node.values())
    #     kx = self.x / 2
    #     ky = self.y / 2
    #     grid = self.engine.getGrid()
    #     # max_priority = self.engine.getOrder()
    #     path = self.engine.getPath()
    #
    #     pd = math.dist(ORIGO, (kx, ky))
    #
    #     priorities = sorted(grid.keys())
    #     highest = priorities[-1]
    #
    #     alpha = 0.5
    #
    #     for priority in priorities:
    #         # break
    #         for pos, node in grid[priority]:
    #             (x, y) = pos
    #             xt = x - kx
    #             yt = y - ky
    #             d = math.dist(ORIGO, (xt, yt))
    #
    #             # d = (highest - priority + d) / 2
    #             diff = abs(-NODE_SPACING * d + 1)
    #
    #             # if priority != highest:
    #             # diff *= (alpha * (priority) + (1 - alpha) * pd) / (priority + EPSILON)
    #             #
    #             # if priority == highest:
    #             #     diff *= (priority - 1 + (pd - int(pd))) / (highest)
    #             # else:
    #             #     s = (priority + 1 * (pd - int(pd))) / (highest)
    #             #     print(s)
    #             #     diff *= s
    #
    #             c = 255 * diff
    #             color = (c, c, c)
    #
    #             color = node.getColor()
    #             if node == self.engine.previous:
    #                 color = (0, 200, 0)
    #
    #             # if node in path:
    #             #     color = (200, 100, 100)
    #
    #             px = (xt) * (diff - NODE_SPACING + 1) * TILE_SIZE
    #             py = -((yt) * (diff - NODE_SPACING + 1)) * TILE_SIZE
    #
    #             # px = xt * (diff + NODE_SPACING) * TILE_SIZE
    #             # py = -yt * (diff + NODE_SPACING) * TILE_SIZE
    #             #
    #             size = TILE_SIZE * diff  # * o
    #
    #             self.pygame.draw.circle(
    #                 self.window,
    #                 color,
    #                 (
    #                     self.middleX + px,
    #                     self.middleY + py,
    #                 ),
    #                 size,
    #             )
    #
    #             if node in path:
    #                 color = (255, 255, 0)
    #                 self.pygame.draw.circle(
    #                     self.window,
    #                     color,
    #                     (
    #                         self.middleX + px,
    #                         self.middleY + py,
    #                     ),
    #                     size / 8,
    #                 )
    #
    #             if DEBUG:
    #                 if node in neighbors:
    #                     color = (0, 0, 255)
    #                     self.pygame.draw.circle(
    #                         self.window,
    #                         color,
    #                         (
    #                             self.middleX + px,
    #                             self.middleY + py,
    #                         ),
    #                         size / 8,
    #                     )
    #
    #                 text_surface = self.font.render(
    #                     f"{node.getId()}",
    #                     # f"Liminal: {get_position(engine.node)} ({int(clock.get_fps())}FPS)",
    #                     False,
    #                     (255, 0, 0),
    #                 )
    #                 self.window.blit(
    #                     text_surface, (self.middleX + px, self.middleY + py)
    #                 )
    #     self.pygame.draw.circle(
    #         self.window,
    #         (255, 0, 0),
    #         (self.middleX - POS_X, self.middleY - POS_Y),
    #         TILE_SIZE / 20,
    #     )
    #
    #     if 1:
    #         text = "" + "Read Only! " * self.read_only + "Liminal!" * self.liminal
    #         text_surface = self.font.render(
    #             text,
    #             # f"Liminal: {get_position(engine.node)} ({int(clock.get_fps())}FPS)",
    #             False,
    #             (255, 0, 0),
    #         )
    #         self.window.blit(text_surface, (0, 0))
    #
    #     # world = {}
    #     #
    #     # self.rec_draw(self.engine.node, 8, world, ORIGO, ORIGO, [])
    #     #
    #     # locks = []
    #     # for child, (n, node, parent) in world.items():
    #     #     (x, y) = child
    #     #     xc = x - kx
    #     #     yc = y - ky
    #     #     (x, y) = parent
    #     #
    #     #     xp = x - kx
    #     #     yp = y - ky
    #     #
    #     #     c = (n + 1) / 9 * 255
    #     #     color = (c, c, c)
    #     #     if child != parent:
    #     #         self.pygame.draw.line(
    #     #             self.window,
    #     #             color,
    #     #             (self.middleX + xc * TILE_SIZE, self.middleY - yc * TILE_SIZE),
    #     #             (self.middleX + xp * TILE_SIZE, self.middleY - yp * TILE_SIZE),
    #     #             10,
    #     #         )
    #     #
    #     #     if node.isLocked():
    #     #         locks.append(
    #     #             (
    #     #                 self.middleX + xc * TILE_SIZE,
    #     #                 self.middleY - yc * TILE_SIZE,
    #     #             )
    #     #         )
    #     #
    #     # for pos in locks:
    #     #     self.pygame.draw.circle(
    #     #         self.window,
    #     #         (200, 0, 0),
    #     #         pos,
    #     #         8,
    #     #     )
    #
    #     self.pygame.display.flip()


def engineToggleMode(engine: Engine, mode: EngineMode):
    if engine.getMode() == mode:
        mode = EngineMode.NORMAL

    engine.setMode(mode)


class Application(Drawer):
    def __init__(self, engine: Engine):
        super().__init__(pygame)
        self.pygame.event.set_grab(True)  # Grab mouse
        self.pygame.mouse.set_visible(False)
        self.engine: Engine = engine
        self.running: bool = True

        self.x: float = 0.0
        self.y: float = 0.0
        self.can_draw: bool = True

    def handle_events(self) -> None:
        for event in self.pygame.event.get():
            if event.type == pygame.QUIT:
                self.pygame.quit()
                self.running = False

            elif event.type == pygame.MOUSEWHEEL:  # Rotate
                rotation: int = -event.y
                if self.engine.tryRotate(rotation):
                    self.can_draw = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:  # Left click
                    # print("Left mouse button pressed!")
                    if self.engine.getMode() != EngineMode.READ_ONLY:
                        self.engine.getNode().toggleLock()
                    # engineToggleMode(self.engine, EngineMode.READ_ONLY)
                elif pygame.mouse.get_pressed()[2]:  # Right click
                    # print("Right mouse button pressed!")
                    engineToggleMode(self.engine, EngineMode.LIMINAL)

                self.can_draw = True

            elif event.type == pygame.KEYUP:
                draw = True
                if event.key == pygame.K_r:  # Toggle Read-Only Mode
                    engineToggleMode(self.engine, EngineMode.READ_ONLY)
                elif event.key == pygame.K_l:  # Toggle Liminal Mode
                    engineToggleMode(self.engine, EngineMode.LIMINAL)

                elif event.key == pygame.K_n:  # Toggle Normal Mode
                    self.engine.setMode(EngineMode.NORMAL)
                elif event.key == pygame.K_SPACE:  # Lock current Node
                    if self.engine.getMode() != EngineMode.READ_ONLY:
                        self.engine.getNode().toggleLock()
                elif event.key == pygame.K_ESCAPE:  # Stop program
                    self.running = False
                    return
                elif event.key == pygame.K_i:  # Lock current Node
                    self.engine.insert()

                elif event.key == pygame.K_b:  # Lock current Node
                    self.engine.getNode().setData(self.engine.getNode().getId())

                elif event.key == pygame.K_y:  # serialize program
                    path = create_file()
                    if path != None:
                        Engine.serialize(self.engine, path)
                    return

                elif event.key == pygame.K_u:  # serialize program
                    path = browse_file()
                    if path != None:
                        self.engine = Engine.deserialize(path)

                elif event.key == pygame.K_t:  # serialize program
                    self.engine.optimize()
                else:
                    draw = False

                if draw:
                    self.can_draw = True

        keys = pygame.key.get_pressed()

        moveable: bool = keys[pygame.K_LCTRL] or True

        if moveable:
            rotation: int = 1 * (keys[pygame.K_p] or keys[pygame.K_e]) - 1 * (
                keys[pygame.K_o] or keys[pygame.K_q]
            )
            if rotation:
                if self.engine.tryRotate(rotation):
                    self.can_draw = True
                    time.sleep(0.3)

        if keys[pygame.K_BACKSPACE]:
            if self.engine.remove():
                self.can_draw = True
                time.sleep(0.1)
                self.x = 0
                self.y = 0
                return

        # amount: int = (
        #     0
        #     or 1 * keys[pygame.K_1]
        #     or 2 * keys[pygame.K_2]
        #     or 3 * keys[pygame.K_3]
        #     or 4 * keys[pygame.K_4]
        #     or 5 * keys[pygame.K_5]
        #     or 6 * keys[pygame.K_6]
        #     or 7 * keys[pygame.K_7]
        #     or 8 * keys[pygame.K_8]
        #     or 9 * keys[pygame.K_9]
        # )
        amount = 0

        if amount != 0:
            self.engine.setOrder(amount)
            self.can_draw = True
        up: bool = keys[pygame.K_UP] or keys[pygame.K_w]
        down: bool = keys[pygame.K_DOWN] or keys[pygame.K_s]
        left: bool = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right: bool = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        Mx, My = pygame.mouse.get_rel()

        if moveable:
            self.pygame.mouse.set_visible(False)
            self.dy = (
                DELTA_MOVEMENT * up - DELTA_MOVEMENT * down + -My / MOUSE_SENSITIVITY
            )
            self.dx = (
                DELTA_MOVEMENT * right - DELTA_MOVEMENT * left + Mx / MOUSE_SENSITIVITY
            )
        else:
            self.pygame.mouse.set_visible(True)
            self.dx = 0
            self.dy = 0

    def handle_movements(self):
        if not self.dy and not self.dx:
            return

        self.x += self.dx
        self.y += self.dy

        diffX: int = -1 * (self.x < -1) + 1 * (self.x > 1)
        diffY: int = -1 * (self.y < -1) + 1 * (self.y > 1)
        newPos: Position = (diffX, diffY)
        if newPos in MOVEMENT_MAP_INVERTED:
            direction: Direction = MOVEMENT_MAP_INVERTED[newPos]
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
        clock = pygame.time.Clock()
        while self.running:
            clock.tick(60)
            self.can_draw = False
            self.handle_events()
            self.handle_movements()
            if self.can_draw:
                self.draw()

        self.pygame.quit()


class Writer(Application):
    def __init__(self, engine: Engine, width=100, height=10, fontname=None):
        super().__init__(engine)

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
        path: list[Node] = []  # self.engine.search(self.engine.start)
        self.window.fill(BACKGROUND)
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
            text_surface = self.font.render(
                text,
                False,
                (255, 0, 0),
            )
            self.window.blit(text_surface, (0, 0))

        world = {}

        self.rec_draw(
            self.engine.getNode(), self.engine.getOrder(), world, ORIGO, ORIGO, []
        )

        locks = []
        text = []
        for child, (n, node, parent) in world.items():
            (x, y) = child
            xc = x - kx
            yc = y - ky
            (x, y) = parent

            xp = x - kx
            yp = y - ky

            c = (n + 1) / (MAX_ORDER + 1) * 255
            color = (c, c, c)
            if node in path:
                color = (0, 0, 200)
            if child != parent:
                self.pygame.draw.line(
                    self.window,
                    color,
                    (self.middleX + xc * TILE_SIZE, self.middleY - yc * TILE_SIZE),
                    (self.middleX + xp * TILE_SIZE, self.middleY - yp * TILE_SIZE),
                    1 + (n * 2),
                )

            if node.isLocked():
                locks.append(
                    (
                        self.middleX + xc * TILE_SIZE,
                        self.middleY - yc * TILE_SIZE,
                    )
                )

            data = node.getData()
            if data != None:
                # text_surface = self.font.render(
                #     str(data),
                #     False,
                #     (255, 0, 0),
                # )

                text.append(
                    (
                        str(data),
                        self.middleX + xc * TILE_SIZE - 0.1 * TILE_SIZE,
                        self.middleY - yc * TILE_SIZE - 0.2 * TILE_SIZE,
                    )
                )
                # self.window.blit(
                #     text_surface,
                #     (
                #         self.middleX + xc * TILE_SIZE,
                #         self.middleY - yc * TILE_SIZE - 0.2 * TILE_SIZE,
                #     ),
                # )

        for pos in locks:
            self.pygame.draw.circle(
                self.window,
                (200, 0, 0),
                pos,
                8,
            )
        for c, xo, yo in text:
            text_surface = self.font.render(
                c,
                False,
                (255, 0, 0),
            )
            self.window.blit(
                text_surface,
                (xo, yo),
            )

        self.pygame.draw.circle(
            self.window,
            (50, 50, 50),
            (self.middleX - POS_X, self.middleY - POS_Y),
            TILE_SIZE / 20,
        )
        self.pygame.display.flip()

    def loop(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            clock.tick(60)
            self.can_draw = False
            self.handle_events()
            self.handle_movements()
            if self.can_draw:
                self.draw()

        self.pygame.quit()


if __name__ == "__main__":
    engine = Engine()
    app = Writer(engine)  # Application(engine)

    app.loop()
