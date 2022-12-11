#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# File: test.py
# Author: Irreq
# Date: 11/12-2022

from liminal_engine import *

def test_create_liminal_space() -> Node:
    """Create a arbitrary liminal space"""
    # Create a start position at (0, 0)
    start = Node(0, 0)

    # Add a bunch of nodes (y is inverted)
    start.connect(Node(0, 1))
    start.connect(Node(1, 1))
    start.connect(Node(1, 1.1))

    # Add a node to one of the neighbors to the start to create a path
    start.neighbors[(1, 1)].connect(Node(1, 2))
    start.neighbors[(1, 1)].connect(Node(2, 2))
    start.neighbors[(1, 1)].connect(Node(2, 1.9))
    start.neighbors[(1, 1)].neighbors[(2, 1.9)].connect(Node(1, 1.1))
    start.neighbors[(1, 1)].neighbors[(2, 1.9)].connect(Node(3, 3))

    start.neighbors[(1, 1.1)].connect(Node(2, 2.1))

    # Create one directional warp from start to (1, 2)
    start.connect(start.neighbors[(1, 1)].neighbors[(1, 2)].pointer())
    start.neighbors[(1, 1)].neighbors[(1, 2)].disconnect(start)

    # Create a non-escapeable trap
    start.connect(Node(5, -2))
    start.neighbors[(5, -2)].disconnect(start)

    return start

def test_associative_ray_caster():
    """Test the raycaster"""
    start = test_create_liminal_space()

    # Initiate the raycaster
    arc = AssociativeRayCaster()

    # Call this each time you've moved your node
    arc.update(start, math.radians(45))

    # Get the results
    result = arc.cast()

    print(result.keys())


if __name__ == "__main__":
    test_associative_ray_caster()