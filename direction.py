# Static analysis
from __future__ import annotations
from typing import Callable, Tuple, Dict


from enum import Enum

Rotation = int

Position = Tuple[int, int]
# class Position:
#     def __init__(self, x: int, y: int):
#         self._x = x
#         self._y = y
#
#     def __setitem__(self, index: int, value: int) -> None:
#         if index == 0:
#             self._x = value
#         elif index == 1:
#             self._y = value
#         else:
#             raise IndexError("Invalid index")
#
#     def __getitem__(self, index: int):
#         if index == 0:
#             return self._x
#         elif index == 1:
#             return self._y
#         else:
#             raise IndexError("Invalid index")


ORIGO: Position = (0, 0)  # Center position

DIAGONAL: bool = False

if DIAGONAL:

    class Direction(Enum):
        NORTH = 0
        NORTH_EAST = 1
        EAST = 2
        SOUTH_EAST = 3
        SOUTH = 4
        SOUTH_WEST = 5
        WEST = 6
        NORTH_WEST = 7

    MOVEMENT_MAP: Dict[Direction, Position] = {
        Direction.NORTH: (0, 1),
        Direction.NORTH_EAST: (1, 1),
        Direction.EAST: (1, 0),
        Direction.SOUTH_EAST: (1, -1),
        Direction.SOUTH: (0, -1),
        Direction.SOUTH_WEST: (-1, -1),
        Direction.WEST: (-1, 0),
        Direction.NORTH_WEST: (-1, 1),
    }

    OPPOSITE_DIRECTION_MAP: Dict[Direction, Direction] = {
        Direction.NORTH: Direction.SOUTH,
        Direction.NORTH_EAST: Direction.SOUTH_WEST,
        Direction.EAST: Direction.WEST,
        Direction.SOUTH_EAST: Direction.NORTH_WEST,
        Direction.SOUTH: Direction.NORTH,
        Direction.SOUTH_WEST: Direction.NORTH_EAST,
        Direction.WEST: Direction.EAST,
        Direction.NORTH_WEST: Direction.SOUTH_EAST,
    }

    NEARBY_DIRECTION_MAP: Dict[Direction, Tuple[Direction, Direction]] = {
        Direction.NORTH: (Direction.NORTH_WEST, Direction.NORTH_EAST),
        Direction.NORTH_EAST: (Direction.NORTH, Direction.EAST),
        Direction.EAST: (Direction.NORTH_EAST, Direction.SOUTH_EAST),
        Direction.SOUTH_EAST: (Direction.EAST, Direction.SOUTH),
        Direction.SOUTH: (Direction.SOUTH_EAST, Direction.SOUTH_WEST),
        Direction.SOUTH_WEST: (Direction.SOUTH, Direction.WEST),
        Direction.WEST: (Direction.SOUTH_WEST, Direction.NORTH_WEST),
        Direction.NORTH_WEST: (Direction.WEST, Direction.NORTH),
    }


else:

    class Direction(Enum):
        NORTH = 0
        EAST = 1
        SOUTH = 2
        WEST = 3

        @staticmethod
        def rotate(direction: Direction, rotation: Rotation):
            return Direction((direction.value + rotation) % 4)

    MOVEMENT_MAP: Dict[Direction, Position] = {
        Direction.NORTH: (0, 1),
        Direction.EAST: (1, 0),
        Direction.SOUTH: (0, -1),
        Direction.WEST: (-1, 0),
    }

    OPPOSITE_DIRECTION_MAP: Dict[Direction, Direction] = {
        Direction.NORTH: Direction.SOUTH,
        Direction.EAST: Direction.WEST,
        Direction.SOUTH: Direction.NORTH,
        Direction.WEST: Direction.EAST,
    }

    NEARBY_DIRECTION_MAP: Dict[Direction, Tuple[Direction, Direction]] = {
        Direction.NORTH: (Direction.WEST, Direction.EAST),
        Direction.EAST: (Direction.NORTH, Direction.SOUTH),
        Direction.SOUTH: (Direction.EAST, Direction.WEST),
        Direction.WEST: (Direction.SOUTH, Direction.NORTH),
    }


MOVEMENT_MAP_INVERTED: Dict[Position, Direction] = {
    position: direction for direction, position in MOVEMENT_MAP.items()
}

NEARBY_DIRECTION_MAP_INVERTED: Dict[Tuple[Direction, Direction], Direction] = {
    value: key for key, value in NEARBY_DIRECTION_MAP.items()
}


ALL_DIRECTIONS: int = len(Direction)  # All possible directions to move in

# Get the opposite direction to a Direction
oppositeDirection: Callable[..., Direction] = lambda direction: OPPOSITE_DIRECTION_MAP[
    direction
]


def deltaPosition(direction: Direction, position: Position) -> Position:
    """Compute a new Position based on a Direction

    Position + Direction = Direction'

    :param direction: Direction to
    :param position: Current Position
    :return: New Position
    """
    x, y = position

    dx, dy = MOVEMENT_MAP[direction]

    return (x + dx, y + dy)
