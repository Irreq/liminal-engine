#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# File: liminal_engine.py
# Author: Irreq
# Date: 09/12-2022

import numpy as np # To get the distance between nodes

class Node:
    """Node that consist of position and other data"""
    def __init__(self, position: tuple[int, int], data={}):
        self.position = position
        self.data = data

        self.neighbors = {}


# ---- Node information ----
def get_position(node: Node) -> tuple[int, int]:
    """Retrieve reference to node"""
    return node.position

def get_reference(node: Node) -> dict:
    """Retrieve reference to node"""
    return {get_position(node): node}

def get_neighbors(node: Node) -> dict:
    """Retrieve neigbors from node"""
    return node.neighbors

def get_data(node: Node) -> dict:
    """Retrieve data from node"""
    return node.data

def is_neighbor(node: Node, position: tuple[int, int]) -> bool:
    """Find out if position is occupied or not"""
    return position in get_neighbors(node)

def is_close(node0: Node, node1: Node, distance: float=2.0**0.5) -> bool:
    """Only return True if node is in the viscinity of the target node"""
    a = np.array(get_position(node0))
    b = np.array(get_position(node1))

    return np.linalg.norm(a - b) <= distance


# ---- Node operations ----
def connect(node0: Node, node1: Node) -> None:
    """Connect two nodes by their liminal space position"""
    node0.neighbors.update(get_reference(node1))
    node1.neighbors.update(get_reference(node0))

def disconnect(node0: Node, node1: Node) -> None:
    """Disconnect two nodes by their liminal space position"""
    node0.neighbors.pop(get_position(node1), None)
    node1.neighbors.pop(get_position(node0), None)

def replace(node0: Node, node1: Node) -> None:
    """Destructive replace of node0 with node1"""
    for neighbor in get_neighbors(node0):
        disconnect(node0, neighbor)
        connect(node1, neighbor)

    del node0

def set_data(node: Node, new_data: dict) -> None:
    """Assign data to node"""
    node.data.update(new_data)

def set_neighbors(node: Node, neighbors: dict) -> None:
    """Assign neighbors to node"""
    node.neighbors = neighbors

def create_node(position: tuple[int, int], data=None) -> Node:
    """Create a node at the specific position"""
    if data is None:
        data = {}
    return Node(position, data=data)

def remove_node(node: Node) -> None:
    """Removes all reference to node naively"""
    neighbors = get_neighbors(node)

    while neighbors != {}:
        position, neighbor = neighbors.popitem()
        disconnect(node, neighbor)

    del node


# ---- Angles ----
def get_angle_inverted_y(x0: float, y0: float, x1: float, y1: float) -> float:
    """Get the angle between two points, starting from (x0, y0) at origo"""
    return (2*np.pi - ((np.atan2((y0-y1), x0-x1)) + np.pi)) % (2*np.pi)

def get_angle(x0: float, y0: float, x1: float, y1: float) -> float:
    """Get the angle between two points, starting from (x0, y0) at origo"""
    return (2*np.pi - ((np.arctan2((y0-y1), x0-x1)) + np.pi)) % (2*np.pi)

def is_in_range(lower: float, alpha: float, upper: float) -> bool:
    """Determine if angle is within two other angles"""
    return (alpha - lower) % (2*np.pi) <= (upper - lower) % (2*np.pi)

def is_in_view(node: Node, target_node: Node, angle: float, view: float) -> bool:
    """Return True if target_node is in view from node"""
    lower = angle - (view / 2)
    if lower < 0:
        lower = 2*np.pi + lower # Will always be negative

    upper = angle + (view / 2)
    if upper > 2*np.pi:
        upper -= 2*np.pi

    node_x, node_y = get_position(node)
    target_x, target_y = get_position(target_node)

    alpha = get_angle_inverted_y(
        node_x,
        node_y,
        target_x,
        target_y
    )

    return is_in_range(lower, alpha, upper)


# ---- To be implemented ----
def unravel(node: Node):
    """Unravels entire network to eucleidian space"""
    pass

def strip_node(node: Node) -> tuple[Node, dict, list]:
    """Remove everything from node"""
    pass


# ---- Higher logical backend functions ----
def get_nearby_it(node: Node, distance: float) -> list[Node]:
    """Get all nodes within a set radius (`distance`) from `node`"""

    visited = []
    allowed = [node]
    while allowed != []:

        tmp = []

        for neighbor in allowed:
            if neighbor not in visited and is_close(node, neighbor, distance):
                # tmp += get_neighbors(neighbor).values()
                tmp.extend(get_neighbors(neighbor).values())
                visited.append(neighbor)

        allowed = tmp

    return visited

def create_empty_grid(position: tuple[int, int], width: int, height: int) -> dict:
    """A grid of connected nodes will be created where position is bottom left corner"""

    x, y = position

    import time

    created = {}

    start = create_node(position)

    created.update(get_reference(start))

    previous_node = start

    for i in range(1, height):
        new = create_node((x, y + i))

        created.update(get_reference(new))

        connect(previous_node, new)

        previous_node = new

    previous_node = start
    previous_neighbor_node = previous_node

    for j in range(1, width):
        tmp_x = x + j
        for i in range(0, height):
            tmp_y = y + i

            to_connect = {
                (nx, ny): node for (nx, ny), node in get_neighbors(previous_neighbor_node).items()
                if nx == tmp_x-1 and tmp_y-1 <= ny <= tmp_y+1
            }

            # Add neighbor
            to_connect.update(get_reference(previous_neighbor_node))

            # Add below
            to_connect.update(get_reference(previous_node))

            new = create_node((tmp_x, tmp_y))

            if np.random.random() > 0.9:
                new.data[1] = [1] # Just add some identifiable information

            previous_node = new

            created.update(get_reference(new))

            for node in to_connect.values():
                connect(new, node)

            if i == 0:
                last = new

            if i == height-1:
                continue
            
            previous_neighbor_node = to_connect[(tmp_x-1, tmp_y+1)]

        previous_neighbor_node = last

    return created


def recompiler(ocean: list[Node]):

    grid = {}

    conflicts = {}

    for node in ocean:
        position = get_position(node)

        if position in grid:
            if position in conflicts:
                conflicts[position].append(node)
            else:
                conflicts[position] = [node]
        else:
            grid[position] = node

    
    for position in conflicts:

        new_neighbors = {}
        first = grid[position]
        data = {}
        while get_neighbors(first) != {}:
            neighbor_position, neighbor_node = get_neighbors(first).popitem()

            if not neighbor_position in grid and not neighbor_position in conflicts:
                new_neighbors[neighbor_position] = neighbor_node
            
            disconnect(first, neighbor_node)


        for first in conflicts[position]:
            data.update(get_data(first))

            while get_neighbors(first) != {}:
                neighbor_position, neighbor_node = get_neighbors(first).popitem()
                if not neighbor_position in grid and not neighbor_position in conflicts:
                    new_neighbors[neighbor_position] = neighbor_node
                
                disconnect(first, neighbor_node)

        new = grid[position]

        set_neighbors(new, new_neighbors)

        set_data(new, data)

        grid[position] = new

    
    grid_copy = grid.copy()

    items = grid.values()

    while grid_copy != {}:
        position, node = grid_copy.popitem()

        new_neighbors = {pos:neighbor for pos, neighbor in get_neighbors(node).items() if neighbor not in items}

        node.neighbors = new_neighbors

    grid_copy = grid.copy()

    tmp = []
    while grid_copy != {}:
        position, node = grid_copy.popitem()
        
        for other in grid_copy.values():
            if is_close(node, other):
                connect(node, other)

        tmp.append(node)

    ocean[:] = tmp


class Engine:

    nearby = []

    nearby_rel = {}
    nearby_norm = {}

    def __init__(self, node: Node, distance: float, autogenerate=True):
        self.node = node
        self.distance = distance

        self.autogenerate = autogenerate

    def traverse(self, angle: float):
        dx = int(round(np.cos(angle), 0))
        dy = int(round(np.sin(angle), 0))

        x, y = get_position(self.node)

        new_position = (x+dx, y+dy)

        if is_neighbor(self.node, new_position): # Neighbor exists, switch to it
            self.node = get_neighbors(self.node)[new_position]

        elif self.autogenerate:
            new_node = create_node(new_position)
            connect(self.node, new_node)

            self.node = new_node

        self.nearby = get_nearby_it(self.node, self.distance)

        x, y = get_position(self.node)

        self.nearby_rel = {}
        self.nearby_norm = {}

        recompiler(self.nearby)

        for close_node in self.nearby:
            xi, yi = get_position(close_node)
            self.nearby_rel[(xi, yi)] = close_node
            self.nearby_norm[(xi-x, yi-y)] = close_node