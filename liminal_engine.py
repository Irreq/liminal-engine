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


DEPTH = 10

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


def get_angle(x0: float, y0: float, x1: float, y1: float) -> float:
    """Get the angle between two points, starting from (x0, y0) at origo"""
    return (math.atan2(y0-y1, x0-x1) + math.pi) % (2*math.pi)


def in_view(x0: float, y0: float, x1: float, y1: float, lower: float, upper: float) -> bool:
    """Return True or False based on if point1 is in view from point0 or not"""
    return lower < get_angle(x0, y0, x1, y1) < upper


def is_close(node0: Node, node1: Node, distance=DEPTH) -> bool:
    """Only return True if node is in the viscinity of the target node"""

    x_0, y_0 = node0.get_position()
    x_1, y_1 = node1.get_position()

    return abs(x_1 - x_0) <= distance and abs(y_1 - y_0) <= distance


def get_nearby(node: Node, depth: int) -> dict:
    """Recursively go through nodes and add them to results
    if they can be considered neighbor to node"""

    def _rec(tmp_node: Node, times: int, result=None, visited={}) -> dict:
        """This function is only here to hide from the user."""
        
        if result is None:
            result = {}

        visited.update(tmp_node.get_node())

        neighbors = tmp_node.get_neighbors()

        allowed = {
            k: n_node for k, n_node in neighbors.items()
            if is_close(tmp_node, n_node) and k not in visited
        }
        
        if times < 1:
            if allowed != {}:
                result.update(allowed)
        
        else:
            if allowed != {}:
                result.update(allowed)

            for neighbor in allowed:
                _rec(neighbors[neighbor], times - 1, result, visited)

        return result

    return _rec(node, depth)


def get_visible_neighbors(node: Node, angle: float, spread=math.radians(45)) -> dict:
    """Raycast to find visible neighbors"""

    visited = {}

    lower = (angle-spread) % 2*math.pi
    upper = (angle+spread) % 2*math.pi

    x, y = node.get_position()

    def filter_spread(tmp_node):
        tx, ty = tmp_node.get_position()

        return angle-spread <= (math.atan2(y-ty, x-tx) + math.pi) <= angle+spread


    def _rec(tmp_node, result=None, visited={}):
        pass
    pass


class LiminalEngine:

    """Handle logic to travel inside liminal space"""

    running = True
    autogenerate = True

    lim_x, lim_y = 0, 0

    nearby = {}
    rel_nearby = {}

    def __init__(self, start_node: Node):
        self.node = start_node
    
    def traverse(self, dx, dy) -> bool:
        neighbors = self.node.get_neighbors()

        x, y = self.node.get_position()

        x += dx
        y += dy
        if (x, y) in neighbors:
            self.node = neighbors[(x, y)]
            return True

        else:
            if self.autogenerate:
                self.create_neighbor(dx, dy)
                for (px, py) in RELATIVE_NEIGHBORS[(dx, dy)]:
                    self.create_neighbor(px, py)

                try:
                    self.node = self.node.get_neighbors()[(x, y)]
                    return True
                except:
                    print("Error couldn't change position")
        
        return False

    def get_rel_nearby(self):
        # Turn it into relative position
        px, py = self.node.get_position()
        self.rel_nearby = {(xi-px, yi-py):v for (xi, yi), v in self.nearby.items()}
        return self.rel_nearby


    def create_neighbor(self, dx, dy):

        self.nearby = get_nearby(self.node, DEPTH)

        x, y = self.node.get_position()

        # self.rel_nearby = [(xi-x, yi-y) for (xi, yi) in self.nearby]
        self.rel_nearby = self.get_rel_nearby()

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

    def get_liminal_position(self) -> tuple:
        return (self.lim_x, self.lim_y)

    def move(self, dx, dy) -> tuple:
        tmp_x = self.lim_x + dx
        tmp_y = self.lim_y + dy

        # # No movement change
        # if int(tmp_x) == int(self.lim_x) and int(tmp_y) == int(self.lim_y):
        #     return (self.lim_x, self.lim_y, self.rel_nearby)
        
        old_node = self.node
        try:
            if not self.traverse(int(tmp_x), int(tmp_y)):
                return (self.lim_x, self.lim_y, self.rel_nearby)
        except:
            return (self.lim_x, self.lim_y, self.rel_nearby)
            
        
        self.lim_x = tmp_x
        self.lim_y = tmp_y

        if old_node == self.node: # Nothing happened no need to update
            return (self.lim_x, self.lim_y, self.rel_nearby)

        self.nearby = get_nearby(self.node, DEPTH)

        
        # self.rel_nearby = {(xi-px, yi-py):v for (xi, yi), v in self.nearby.items()}
        self.rel_nearby = self.get_rel_nearby()

        return (self.lim_x, self.lim_y, self.rel_nearby)



class AssociativeRayCaster:

    """This does not take into account for surfaces only points"""

    def __init__(self, spread=math.radians(45)):
        self.spread = spread


    def update(self, node, angle):
        self.node = node
        x, y = self.node.get_position()
        self.x = x
        self.y = y
        self.angle = angle

        self.allowed = {}
        self.visited = {}

        self.lower = self.angle - self.spread / 2
        self.upper = self.angle + self.spread / 2

        self.global_lower = self.angle
        self.global_upper = self.angle

        self.result = {}

    def _cast(self, node):
        """Cast the neighbors to find which neighbors who are in line of sight"""

        tmp_allowed = {}
        neighbors = node.get_neighbors()

        def filter_node(key, tmp_node):
            """Filter node based of location and previous existence"""

            if key in self.visited:
                return False

            else:
                self.visited.update({key: tmp_node})

            x1, y1 = tmp_node.get_position()

            # Is it behind parent, this is to filter out nodes that could be in a U-turn
            if not in_view(x0, y0, x1, y1, self.lower, self.upper):
                return False

            # The familiar line of sight from starting position
            if not in_view(self.x, self.y, x1, y1, self.lower, self.upper):
                return False

            return True

        # Create temporary angles, to reduce line of sight behind the void
        tmp_lower = self.angle
        tmp_upper = self.angle

        x0, y0 = node.get_position()

        # Parse each neighbor
        for k, n_node in node.get_neighbors().items():

            if filter_node(k, n_node):
                tmp_allowed[k] = n_node
                theta = get_angle(x0, y0, *n_node.get_position())

                # Update temporary angles
                if theta < tmp_lower:
                    tmp_lower = theta
                elif tmp_upper < theta:
                    tmp_upper = theta

        # Update the global angles, so that line of sight shrinks if the void is ini its way
        if self.global_upper < tmp_upper <= self.angle + self.spread/2:
            self.global_upper = tmp_upper

        if self.angle - self.spread / 2 <= tmp_lower <self.global_lower:
            self.global_lower = tmp_lower

        return tmp_allowed

    def cast(self):
        """Recursively go through neighbors by neighbors in a layering principle
        That is that each level neighbors are searched level vise"""

        def rec(allowed_neighbors, result={}):
            if allowed_neighbors != {}:

                allowed = {}

                for n_node in allowed_neighbors.values():
                    k = self._cast(n_node)
                    allowed.update(k)

                result.update(allowed)

                rec(allowed, result = result)
                
            return result

        self.result = rec(self.node.get_node())

        return self.result