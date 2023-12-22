# Static analysis
from __future__ import annotations
from typing import Generator, Callable

from queue import Queue
from enum import Enum

import datetime  # Logging
import pickle

# Local package for Direction and Position logic
from direction import (
    Rotation,
    Position,
    Direction,
    ORIGO,
    deltaPos,
    oppositeDirection,
    NEARBY_DIRECTION_MAP,
    ALL_DIRECTIONS,
)


MAX_ORDER: int = 13  # How far the nodes can be seen
INFINITY: int = 1 << 32  # Just a big number

assert MAX_ORDER < INFINITY, "You will not be able to visit all nodes"


class EngineMode(Enum):
    """Different Modes the engine may operate in"""

    NORMAL = 0  # Default, works like a regular grid
    READ_ONLY = 1  # Cannot do anything except traverse
    LIMINAL = 2  # Perform liminal operations


class NodeState(Enum):
    """States a Node may be in"""

    NOT_VISITED = 0
    VISITED = 1
    TMP_VISITED = 2
    IGNORE = 3


def cleanVisited(visited: list[Node]) -> None:
    """Reset all Nodes

    :param visited: list of Nodes
    """
    for node in visited:
        node.state = NodeState.NOT_VISITED


Data = object


class Node:
    """Node class that lives inside Engine

    :param data: Your object
    :param index: Id
    :param locked: If it can be removed
    :param state: Can be set by other functions
    """

    var: int = 0

    def __init__(self, data: Data = None):
        """Node constructor where Data is optional

        :param data: optional Data to store on Node
        """

        # User data
        self._data: Data = data

        # Runtime variables
        self.locked: bool = False
        self.state: NodeState = NodeState.NOT_VISITED

        # Protected
        self._neighbors: list[Node | None] = [None] * ALL_DIRECTIONS

        # Final Static, DO NOT MODIFY
        self._index: int = Node.var
        Node.var += 1

    # ---- Object overrides ----
    def __len__(self) -> int:
        return len(list(self.values()))

    def __eq__(self, obj: object) -> bool:
        """Checks if a Node equals another Node

        A node can only be similar if they are the same

        :param obj: object to check against
        :return: bool
        """
        return self is obj
        if isinstance(obj, int):
            return self.state == obj
        else:
            return self is obj

    def __contains__(self, item: object) -> bool:
        """Overload in operator

        Usage:

        >>> Node in node # True or False

        >>> Direction in node # True or False

        >>> Data in node # True or False

        >>> object in node # False

        :param item: Direction, Node or Data anything else wont work
        :return: if inside Node
        """
        if isinstance(item, Direction):
            return self[item] != None
        elif isinstance(item, Node):
            return item in self._neighbors
        elif isinstance(item, Data):
            return item is self.data
        else:
            return False

    def __getitem__(self, direction: Direction) -> Node | None:
        """Slice of Node. Either Node or None

        Usage:

        >>> neighbor: Node = node[direction]

        :param direction: desired direction
        :return: Node or None
        """
        return self._neighbors[direction.value]

    def __setitem__(self, direction: Direction, node: Node | None) -> None:
        """Setter for Node

        Usage:

        >>> node: Node = Node()
        >>> node[direction] = ...

        :param node: the value to assign
        :type node: Node or None
        :param direction: Direction
        """
        self._neighbors[direction.value] = node

    def __hash__(self) -> int:
        """Overload hash for Node

        :return: hash value for Node
        """
        return id(self)

    def __repr__(self) -> str:
        """Node representation

        :return: string
        """
        f = lambda direction: direction if (self[direction] is not None) else " " * 12
        out = f"""
            {f(Direction.NORTH)} 
        
{f(Direction.WEST)}     {self.getId()}   {f(Direction.EAST)} 
        
            {f(Direction.SOUTH)} 
        """

        return out

    def __str__(self) -> str:
        """Node as string

        :return: str
        """
        return self.__repr__()

    # ---- Helper Functions ----
    def log(self, message: str, level: int = 0) -> None:
        """Log a message from a certain node

        :param message: Your message
        :param level: Logging level
        """
        print(f"({datetime.datetime.now()}) from Node=({self.getId()}) LOG: {message}")

    def keys(self) -> Generator[Direction, None, None]:
        for i, neighbor in enumerate(self._neighbors):
            if neighbor is not None:
                yield Direction(i)

    def values(self) -> Generator[Node, None, None]:
        """Get all valid neighbors to Node all None will be ignored

        Usage:

        >>> for neighbor in node.values():
                ...


        :return: a valid neighbor
        """
        for neighbor in self._neighbors:
            if neighbor is not None:
                yield neighbor

    def items(self) -> Generator[tuple[Direction, Node], None, None]:
        """Get both direction and neighbor from all neighbors to node

        Usage:

        >>> for direction, neighbor in node.items():
                ...

        :return: a valid direction and neighbor
        """
        for i, neighbor in enumerate(self._neighbors):
            if neighbor is not None:
                yield (Direction(i), neighbor)

    # ---- Getters and Setters ----
    def setData(self, data: Data) -> None:
        """Setter for data

        :param data: your data
        """
        self._data = data

    def getData(self) -> Data:
        """Getter for data

        :return: Data on Node
        """
        return self._data

    def getId(self) -> int:
        """Getter for Node ID

        :return: id number
        """
        return self._index

    # ---- Methods ----
    def toggleLock(self) -> None:
        """Toggle lock state for Node"""
        self.locked = not self.locked

    def isLocked(self) -> bool:
        """Determine if Node is locked

        :return: Locked state
        """
        return self.locked is True

    # ---- Graph Functions ----
    def isLeaf(self) -> bool:
        """Determine if Node is a leaf (only one neighbor)

        :return: if leaf
        """
        return len(self) == 1

    def rotate(self, rotation: Rotation) -> None:
        """Rotate node similar to rolling

        :param steps: how many rolls
        """
        rotation %= ALL_DIRECTIONS
        if rotation == 0:
            self.log("Will not rotate when not needed")
            return
        new_neighbors: list[Node | None] = [None] * ALL_DIRECTIONS

        for i, neighbor in enumerate(self._neighbors):
            new_neighbors[(i + rotation) % ALL_DIRECTIONS] = neighbor

        self._neighbors = new_neighbors

    def remove(self) -> dict[Direction, Node]:
        """Remove all references to Node

        :return: dictionary of previous node constallaion
        """
        neighbors: dict[Direction, Node] = dict(self.items())
        for direction, neighbor in neighbors.items():
            self.disconnect(direction, neighbor)

        return neighbors

    def canRemove(self) -> bool:
        """Checks if Node can be removed or not

        :return: [TODO:return]
        """
        if self.getId() == 0 or self.isLocked():
            return False

        return len(self) > 0

    def isConnected(self, direction: Direction, node: Node) -> bool:
        """Checks if Node is connected in a specific direction

        :param direction: desired Direction
        :param node: other Node
        :return: if is connected
        """
        return (self[direction] is node) and (
            node[oppositeDirection(direction)] is self
        )

    def canConnect(self, direction: Direction, node: Node) -> bool:
        """Find out if Node can be connected

        :param direction: the desired direction
        :param node: other Node
        :return: if can be connected
        """
        return (self[direction] is None) and (
            node[oppositeDirection(direction)] is None
        )

    def connect(self, direction: Direction, node: Node) -> None:
        """Connect two Nodes

        :param direction: desired direction
        :param node: other Node to connect
        """
        self[direction] = node
        node[oppositeDirection(direction)] = self

    def disconnect(self, direction: Direction, node: Node) -> None:
        """Disconnect two Nodes

        :param direction: Desired direction
        :param node: other Node to disconnect from
        """
        self[direction] = None
        node[oppositeDirection(direction)] = None

    def directionTo(self, node: Node) -> Direction | None:
        """Get the first valid direction to Node or None

        :param node: target Node
        :return: Direction or None
        """
        for direction, neighbor in self.items():
            if neighbor == node:
                return direction


def isArticulationPoint(node: Node) -> bool:
    """Checks if node is articulation point. This is done by computing if each
    neighbor is able to traverse to all other neighbors without visiting the
    current node. If this is true, the current node is redundant and can be
    removed.

    This code is a bit convoluted with cache, however this is because its taking
    shortcuts. If a node was previously found, then finding it again would mean
    that the current neighbor is also able to traverse to a node further away
    and so on...

    :param node: current Node
    :return: if its an articulation point
    """
    neighbors: set[Node] = set(node.values())
    done: bool = False
    cache: list[Node] = []
    node.state = NodeState.IGNORE

    while len(neighbors) > 0 and not done:
        start = neighbors.pop()
        if start.state == NodeState.VISITED:
            continue
        elif (
            start.state == NodeState.NOT_VISITED and cache != []
        ):  # This rarely happens
            cleanVisited(cache)
            cache = []

        for neighbor in neighbors:
            if neighbor.state == NodeState.VISITED:
                continue
            if cache != []:
                recache: list[Node] = []

                # Search for neighbors until a VISITED node is found
                result = DFSwithFunction(
                    neighbor,
                    NodeState.TMP_VISITED,
                    recache,
                    lambda n: n.state == NodeState.VISITED,
                )

                # Add all visited Nodes to cache
                for n in recache:
                    n.state = NodeState.VISITED
                    cache.append(n)
                if not result:  # Is there a better way to stop nested loop?
                    done = True
                    break

            else:
                # A complete search until start is found
                result = DFSwithFunction(
                    neighbor, NodeState.VISITED, cache, lambda n: n == start
                )

                if not result:
                    done = True
                    break

    node.state = NodeState.NOT_VISITED
    cleanVisited(cache)

    return not done


def DFSwithFunction(
    node: Node,
    territory: NodeState,
    visited: list[Node],
    f: Callable[..., bool],
    depth: int = MAX_ORDER,
) -> bool:
    """Perform DFS and apply a function f(node) for each Node encountered and
    stop at max depth or when callback is satisfied

    WARNING: You must clean up all nodes in visited

    :param node: Current Node
    :param territory: which territory current node shall belong to
    :param visited: aldready visited Nodes
    :param f: Callback for Node
    :param depth: Current depth
    :return: if found
    """
    if f(node):
        return True
    if depth < 0:
        return False

    node.state = territory
    visited.append(node)

    for neighbor in node.values():
        # if neighbor.state not in (NodeState.IGNORE, NodeState.VISITED, territory):
        if (neighbor.state != NodeState.IGNORE) and (neighbor.state != territory):
            found: bool = DFSwithFunction(neighbor, territory, visited, f, depth - 1)
            if found:
                return True

    return False


Grid = dict[Position, tuple[int, Node]]
World = dict[int, list[tuple[Position, Node]]]


def relativeExplorer(
    node: Node,
    n: int,
    place: Grid,
    position: Position,
    visited: list[Node],
):
    """Explore the network similar to DFS but with limits
    and the added functionality to map the network to Eucleidian space.

    :param node: current Node to search
    :param n: order of allowed concecutive movements
    :param place: the grid to build up
    :param position: current Eucleidian position
    :param visited: already visited Nodes
    """
    if position not in place or n > place[position][0]:
        place[position] = (n, node)

    # Maximum depth reached
    if n < 0:
        return

    for direction, neighbor in node.items():
        if neighbor.state == NodeState.NOT_VISITED:
            neighbor.state = NodeState.VISITED  # Must clean afterwards
            visited.append(neighbor)
            relativeExplorer(
                neighbor,
                n - 1,
                place,
                deltaPos(direction, position),
                visited,  # Maybe optimized for local search of recent?
            )


def rotateAll(node: Node, rotation: Rotation) -> None:
    """Rotate all NOT_VISITED Nodes in the network

    :param node: current Node
    :param rotation: how to rotate
    """

    def f(other: Node) -> bool:
        other.rotate(rotation)
        return False

    visited: list[Node] = []
    DFSwithFunction(node, NodeState.VISITED, visited, f, INFINITY)
    cleanVisited(visited)


def bend(node: Node, pivot: Node, rotation: Rotation) -> bool:
    """Try to bend the node with regards to pivot. Return True if actually
    bended.

    :param node: node to bend
    :param pivot: node to bend around
    :param times: type of rotation
    :return: if bended
    """

    if not (
        not node.isLeaf()
        and pivot != node
        and pivot in node  # If pivot is neighbor
        and not node.isLocked()
        and not isArticulationPoint(node)
    ):
        return False

    # Will always be a Direction
    previousDirection: Direction | None = node.directionTo(pivot)
    if previousDirection == None:
        raise ValueError("Previous direction is undefined")

    potential: Direction = Direction.rotate(previousDirection, -rotation)

    if node[potential] in (pivot, None):
        pivot.state = NodeState.IGNORE
        rotateAll(node, rotation)
        pivot.state = NodeState.NOT_VISITED

        newDirection: Direction = Direction.rotate(previousDirection, rotation)

        node[newDirection] = node[previousDirection]
        node[previousDirection] = pivot
        return True

    else:
        return False


class Engine:
    """Interface to the network of Nodes

    :param mode: [TODO:attribute]
    :param order: [TODO:attribute]
    :param node: [TODO:attribute]
    :param start: [TODO:attribute]
    :param previous: [TODO:attribute]
    :param grid: [TODO:attribute]
    :param world: [TODO:attribute]
    :param path: [TODO:attribute]
    :param mode: [TODO:attribute]
    :param previous: [TODO:attribute]
    :param node: [TODO:attribute]
    :param world: [TODO:attribute]
    """

    def __init__(self, mode: EngineMode = EngineMode.NORMAL, order: int = MAX_ORDER):
        self.mode: EngineMode = mode
        self.order: int = order
        self.setOrder(order)
        self.setMode(mode)

        self.node: Node = Node()
        self.start: Node = self.node
        self.node.toggleLock()

        self.previous: Node = self.node

        # World stuff
        self.grid: Grid = {}
        self.world: World = {}
        self.path: list[Node] = []

        self.update()

    def search(self, node: Node) -> list[Node]:
        """Search for a Node in the network

        WARNING if Node is not present in the Engine, an empty list will be
        returned

        :param node: target Node
        :return: ordered path to Node
        """
        q = Queue()
        q.put(self.node)

        visited: list[Node] = []
        pathMap: dict[Node, Node] = {}

        while not q.empty():
            other: Node = q.get()

            if other == node:
                break

            for neighbor in other.values():
                if neighbor.state == NodeState.NOT_VISITED:
                    neighbor.state = NodeState.VISITED
                    visited.append(neighbor)
                    q.put(neighbor)
                    pathMap[neighbor] = other

        cleanVisited(visited)
        path: list[Node] = []

        other: Node = node
        i = 0
        while True:
            if i > 50:
                print("Too far!")
                break
            if other not in pathMap:
                break

            path.append(other)
            other = pathMap[other]
            i += 1

        return path

    def getOrder(self) -> int:
        """Getter for order

        :return: int
        """
        return self.order

    def setOrder(self, value: int) -> None:
        """Setter for engine traversal order

        :param value: new positive integer
        """
        assert isinstance(value, int), "Invalid range type: " + str(value)
        assert value >= 0, "Invalid range: " + str(value)
        if self.order != value:
            self.order = value
            print("Changing order")
            self.update()

    def getPath(self) -> list[Node]:
        return self.path

    def setMode(self, mode: EngineMode) -> None:
        """Setter for EngineMode

        :param mode: new Mode
        """
        assert isinstance(mode, EngineMode), "Invalid mode: " + str(mode)
        self.mode = mode

    def getMode(self) -> EngineMode:
        """Getter for engine Mode

        :return: mode
        """
        return self.mode

    def getNode(self) -> Node:
        return self.node

    def getGrid(self) -> World:
        return self.world

    def move(self, direction: Direction) -> bool:
        """Tries to move in a desired Direction

        :param direction: your Direction
        :return: if successful
        """

        node: Node = traverse(self.node, direction, self.grid, self.mode)
        if self.node != node:
            self.remove()  # Optimize by removing redundant Nodes
            self.previous = self.node
            self.node = node

            self.update()

            return True

        return False

    def closestValidDirection(
        self, direction: Direction
    ) -> Generator[Direction, None, None]:
        """Compute the closest valid direction to a current direction

        :param direction: target Direction
        :return: Direction generator
        """
        near: tuple[Direction, Direction] = NEARBY_DIRECTION_MAP[direction]
        for possibleDirection in self.node.keys():
            if possibleDirection in near:
                yield possibleDirection

    def remove(self) -> bool:
        """Tries to remove current Node from the network

        :return: if successful
        """

        if (
            self.mode != EngineMode.READ_ONLY
            and self.node.canRemove()
            and isArticulationPoint(self.node)
        ):
            if self.node == self.previous:
                for node in self.node.values():
                    self.previous = node
                    break

            self.node.remove()

            self.node = self.previous
            for node in self.node.values():
                self.previous = node
                break

            self.update()

            return True

        return False

    def insert(self) -> bool:
        """Insert a new to the network on the current position

        :return: if successful
        """
        if self.mode == EngineMode.READ_ONLY or self.node == self.previous:
            return False

        node: Node = Node()
        direction: Direction | None = self.previous.directionTo(self.node)

        if direction == None:  # This should not happen!?
            raise ValueError("Previous node is not a neighbor")

        if self.node.isLeaf():
            self.node.connect(direction, node)
            self.previous = self.node
            self.node = node

        else:
            self.previous.disconnect(direction, self.node)
            self.previous.connect(direction, node)
            node.connect(direction, self.node)
            self.previous = node
            self.node

        self.update()

        return True

    @staticmethod
    def deserialize(filename: str) -> Engine:
        # Deserialize the network of nodes
        with open(filename, "rb") as file:
            network: Engine = pickle.load(file)

        return network

    @staticmethod
    def serialize(network: Engine, filename: str) -> None:
        """Serialize the world"""

        # Serialize the network of nodes
        with open(filename, "wb") as file:
            pickle.dump(network, file)

    def update(self) -> None:
        """Generate a 2D representation of the network. Will keep Nodes with
        shorter Manhattan distance.

        :return: Grid of the world
        """
        self.grid.clear()
        all_visited: list[Node] = []
        relativeExplorer(self.node, self.order, self.grid, ORIGO, all_visited)

        cleanVisited(all_visited)

        world: World = {}

        for position, (priority, node) in self.grid.items():
            if priority not in world:
                world[priority] = []

            world[priority].append((position, node))

        self.world = world

    def tryRotate(self, rotation: Rotation) -> bool:
        """Try to bend the network at the current position

        It will try to bend the current node but will fallback to a rotation if
        bend was unsuccessful.

        :param rotation: desired rotation
        :return: if it could perform operations
        """
        if self.mode == EngineMode.READ_ONLY:
            return False

        if not bend(self.node, self.previous, rotation):
            rotateAll(self.node, rotation)

        self.update()

        return True

    def optimize(self) -> bool:
        """Best effort optimization where it tries to straighten all paths
        outwards. Could be used to remove some interdimensional collisions.

        WARNING: this function is destructive! the network state may be
        overwritten and is not easily recovered. All data will remain the same
        though.

        :return: if optimized
        """

        def rec(node: Node, parent: Node, visited: list[Node]):
            visited.append(node)
            flattened = False

            for neighbor in node.values():
                if neighbor not in visited:
                    flattened = rec(neighbor, node, visited)

            if node == parent:
                return flattened
            parentDirection: Direction | None = parent.directionTo(node)

            if parentDirection is None:  # This happens in directed graphs
                return flattened

            n_neighbors: int = len(node)

            if n_neighbors not in (0, 3):
                rotation: Rotation = -1

                while node[parentDirection] == None and rotation < 2:
                    if rotation != 0 and bend(node, parent, rotation):
                        flattened = True
                    rotation += 1

            return flattened

        visited: list[Node] = [self.node]
        flattened = rec(self.node, self.node, visited)
        if flattened:
            print("Performed optimization")
            self.update()

        return flattened


def connectNearby(node: Node, grid: Grid, position: Position) -> None:
    """Checks for all potential neighbors to Node and tries to connect them.

    :param node: Current Node to extend
    :param grid: the grid
    :param position: Current Position
    """
    for direction in Direction:
        if node[direction] is None:
            newPos = deltaPos(direction, position)
            if newPos in grid:
                other = grid[newPos][1]
                if node.canConnect(direction, other):
                    node.connect(direction, other)
                else:
                    node.log("Could not connect")


def traverse(node: Node, direction: Direction, grid: Grid, mode: EngineMode) -> Node:
    """Traverse a relative network and maybe build more of it. This is a central
    function in the engine that is responsible for how the movement is handled.

    :param node: Current Node
    :param direction: Desired Direction
    :param grid: current layout
    :param mode: how to behave when traversing
    :return: Your new Node (or previous if Failure)
    """

    position: Position = deltaPos(direction, ORIGO)

    # Will add a new node in any case, except immediate neighbor exist
    if mode == EngineMode.LIMINAL:
        neighbor = node[direction]
        if neighbor == None:
            neighbor = Node()
            node.connect(direction, neighbor)

        return neighbor

    # If not liminal, non-local travel is tested
    elif position in grid:
        return grid[position][1]

    # If non-local is empty, try neighbor or self
    elif mode == EngineMode.READ_ONLY:
        neighbor = node[direction]
        return neighbor or node  # Defaults to this node, ie no movement

    elif mode == EngineMode.NORMAL:
        # We can assume connect works, since no previous method worked
        neighbor = Node()
        # Connect neighbor a number of times
        connectNearby(neighbor, grid, position)
        return neighbor

    else:
        node.log("Unable to traverse to anything")

        return node
