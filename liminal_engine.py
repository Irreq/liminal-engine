#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# File: liminal_engine.py
# Author: Irreq
# Date: 09/12-2022

import math

"""
DOCUMENTATION:

See `README.md`

TODO:

* Improve Documentation
* Add angle steering (steer_direction is not used at the moment)

"""



DEPTH = 5

RELATIVE_NEIGHBORS = {
    (-1, -1): ((-1, -2), (-2, -1), (-2, -2)),
    (-1, 0): ((-1, -1), (-1, 1), (-2, -1), (-2, 0), (-2, 1)),
    (-1, 1): ((-1, 2), (-2, 1), (-2, 2)),
    (1, -1): ((1, -2), (2, -1), (2, -2)),
    (1, 0): ((1, -1), (1, 1), (2, -1), (2, 0), (2, 1)),
    (1, 1): ((1, 2), (2, 1), (2, 2)),
    (0, -1): ((-1, -1), (1, -1), (-1, -2), (0, -2), (1, -2)),
    (0, 1): ((-1, 1), (1, 1), (-1, 2), (0, 2), (1, 2))
}

MIN_ANGLE = math.radians(5)


def steer_direction(agent, target, angle):
    """Calculate steering direction for agent according to a
    point in coordinal system where y is inverted.
    
    Angle is based to start at 0 in the first quadrant on the X-axis

    If the returned value is positive, the agent needs to turn left
    and if its negative it must turn right.

    Input:
        agent       tuple() coordinates for the agent (y-axis is inverted)

        target      tuple() coordinates to the target (y-axis is inverted)

        angle       float() angle for the agent: [-pi, 0]^[0, pi]
                    where 0 is along the X-axis in the first quadrant

    Returns:
        float()     Angle needed to rotate to face the target: [-pi, pi]
    
    """
    assert -math.pi <= angle <= math.pi, __doc__

    x1, y1 = agent
    x2, y2 = target

    dx = x2 - x1
    dy = y2 - y1

    rads = math.atan2(-dy,dx)

    if angle <= 0 <= rads and math.pi <= rads - angle:
        return -2*math.pi + (rads - angle)

    elif rads <= 0 <= angle and rads - angle <= -math.pi:
        return 2*math.pi + (rads - angle)

    else:
        return rads - angle


class Node:
    """
    A linked network where each node is unique, but you can still
    traverse to yourself again, even though that makes no sense

    TODO:

    Use hashtable instead of dictionary
    """
    def __init__(self, x, y, neighbors: list = [], data: list = [], node_type=0):
        self.x = x
        self.y = y
        self.neighbors = {}
        
        for neighbor in neighbors:
            self.connect(neighbor)

        self.data = data
        self.node_type = node_type

    def connect(self, neighbor):
         # Unidirectional by adding this node to the neighbor
        neighbor.neighbors.update(self.get_node())

        self.neighbors.update(neighbor.get_node())

    def disconnect(self, neighbor):
        self.neighbors.pop(neighbor.get_position(), None)

    def get_node(self):
        return {self.get_position():self.pointer()}

    def pointer(self):
        return self

    def get_position(self):
        return (self.x, self.y)

    def get_neighbors(self):
        return self.neighbors

    def exists(self, position):
        return position in self.neighbors



def is_close(node0: Node, node1: Node, distance=DEPTH) -> bool:
    """Only return True if node is in the viscinity of the target node"""

    x_0, y_0 = node0.get_position()
    x_1, y_1 = node1.get_position()

    return abs(x_1 - x_0) <= distance and abs(y_1 - y_0) <= distance


def get_nearby(node: Node, depth: int) -> dict:
    """Recursively go through nodes and add them to results
    if they can be considered neighbor to node"""

    def _rec(tmp_node: Node, times: int, result=None, visited={}) -> dict:
        

        if result is None:
            result = {}

        visited.update(tmp_node.get_node())

        neighbors = tmp_node.get_neighbors()

        allowed = {
            k: n_node for k, n_node in neighbors.items()
            if is_close(tmp_node, n_node) and k not in visited
        }
        
        if times == 1:
            if allowed != {}:
                result.update(allowed)
        
        else:
            if allowed != {}:
                result.update(allowed)

            for neighbor in allowed:
                _rec(neighbors[neighbor], times - 1, result, visited)

        return result

    return _rec(node, depth)



class LiminalEngine:

    """Handle logic to travel inside liminal space"""

    running = True
    autogenerate = True

    def __init__(self, start_node: Node):
        self.node = start_node
    
    def traverse(self, dx, dy):
        neighbors = self.node.get_neighbors()

        x, y = self.node.get_position()

        x += dx
        y += dy
        if (x, y) in neighbors:
            self.node = neighbors[(x, y)]
            return

        else:
            if self.autogenerate:
                self.create_neighbor(dx, dy)
                for (px, py) in RELATIVE_NEIGHBORS[(dx, dy)]:
                    self.create_neighbor(px, py)

                try:
                    self.node = self.node.get_neighbors()[(x, y)]
                except:
                    print("Error couldn't change position")

    def create_neighbor(self, dx, dy):

        self.nearby = get_nearby(self.node, DEPTH)

        x, y = self.node.get_position()

        self.rel_nearby = [(xi-x, yi-y) for (xi, yi) in self.nearby]

        x += dx
        y += dy

        # It already exists
        if (x, y) in self.nearby:
            return

        new = Node(x, y)

        self.node.connect(new)

        for neighbor in self.nearby:
            if not new.exists(neighbor):
                if is_close(new, self.nearby[neighbor], distance=1):
                    new.connect(self.nearby[neighbor])



def test_engine():

    import pygame

    # initiate pygame and give permission
    # to use pygame's functionality.
    pygame.init()

    # Create a start position at liminal (0, 0)
    start = Node(0, 0)

    start.data = "This is start position"

    engine = LiminalEngine(start.pointer()) #, debug=True, mem=start)

    pygame.init()
    window = pygame.display.set_mode((1000, 800))
    clock = pygame.time.Clock()

    pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
    my_font = pygame.font.SysFont('Comic Sans MS', 30)

    size = 30

    rect = pygame.Rect(0, 0, size, size)
    rect.center = window.get_rect().center
    vel = size

    # Create 10 checkpoints
    checkpoints = {i:None for i in range(0, 9+1)}

    run = True
    while run:
        clock.tick(10)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False

                elif event.key == pygame.K_SPACE:
                    engine.node = start.pointer()
                    print("Warped home!")
                    continue

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

        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP])

        direction = (dx, dy)
        
        if direction != (0, 0):
            engine.traverse(dx, dy)
            window.fill(0)
            engine.nearby = get_nearby(engine.node, DEPTH)
            px, py = engine.node.get_position()
            engine.rel_nearby = [(xi-px, yi-py) for (xi, yi) in engine.nearby]

            for x, y in engine.rel_nearby:
                nrect = pygame.Rect(0, 0, 20, 20)
                nrect.center = window.get_rect().center
                nrect.x += x*vel
                nrect.y += y*vel
                pygame.draw.rect(window, (190, 190, 190), nrect)

            pygame.draw.circle(window,(255, 0, 0),(rect.center),size/2)

            text_surface = my_font.render(f'Liminal: {engine.node.get_position()}', False, (0, 255, 0))

            # This creates a new surface with text already drawn onto it. At the end you can just blit the text surface onto your main screen.

            window.blit(text_surface, (0,0))

            pygame.display.flip()

    pygame.quit()
    exit()


if __name__ == "__main__":

    test_engine()