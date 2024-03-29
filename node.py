# Static analysis
from __future__ import annotations
from typing import Generator, Callable, Dict, Tuple, Any, List, Set
from queue import Queue
from enum import Enum

import datetime  # Logging
import pickle

import sys

# Local package for Direction and Position logic
from direction import (
    Rotation,
    Position,
    Direction,
    ORIGO,
    deltaPosition,
    oppositeDirection,
    NEARBY_DIRECTION_MAP,
    ALL_DIRECTIONS,
)

Data = Any

INFINITY: int = sys.maxsize  # Just a big number


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


def cleanVisited(visited: List[Node]) -> None:
    """Reset all Nodes

    :param visited: list of Nodes
    """
    for node in visited:
        node.state = NodeState.NOT_VISITED


class Node:
    """Node class that lives inside Engine

    :param data: Your object
    :param index: Id
    :param locked: If it can be removed
    :param state: Can be set by other functions
    """

    var: int = 0  # Global do not modify

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
        self._neighbors: List[Node | None] = [None] * ALL_DIRECTIONS

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
            return self[item] is not None
        elif isinstance(item, Node):
            return item in self._neighbors
        elif isinstance(item, Data):
            return item is self._data
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

        def f(direction: Direction) -> str:
            if self[direction] is not None:
                return str(direction)
            else:
                return " " * 12

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

    def items(self) -> Generator[Tuple[Direction, Node], None, None]:
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
        new_neighbors: List[Node | None] = [None] * ALL_DIRECTIONS

        for i, neighbor in enumerate(self._neighbors):
            new_neighbors[(i + rotation) % ALL_DIRECTIONS] = neighbor

        self._neighbors = new_neighbors

    def remove(self) -> Dict[Direction, Node]:
        """Remove all references to Node

        :return: dictionary of previous node constallaion
        """
        neighbors: Dict[Direction, Node] = dict(self.items())
        for direction, neighbor in neighbors.items():
            self.disconnect(direction, neighbor)

        return neighbors

    def canRemove(self) -> bool:
        """Checks if Node can be removed or not

        :return: [TODO:return]
        """
        if self.getId() == 0 or self.isLocked():
            return False

        if self._data is not None:
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


# ---- Complex functions ----


def isArticulationPoint(node: Node, depth: int = INFINITY) -> bool:
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
    neighbors: Set[Node] = set(node.values())
    done: bool = False
    cache: List[Node] = []
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
                recache: List[Node] = []

                # Search for neighbors until a VISITED node is found
                result = DFSWithCallback(
                    neighbor,
                    NodeState.TMP_VISITED,
                    recache,
                    lambda n: n.state == NodeState.VISITED,
                    depth,
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
                result = DFSWithCallback(
                    neighbor, NodeState.VISITED, cache, lambda n: n == start, depth
                )

                if not result:
                    done = True
                    break

    node.state = NodeState.NOT_VISITED
    cleanVisited(cache)

    return not done


def DFSWithCallback(
    node: Node,
    territory: NodeState,
    visited: list[Node],
    f: Callable[..., bool],
    depth: int,
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
    if depth == 0:
        return False

    node.state = territory
    visited.append(node)

    for neighbor in node.values():
        # if neighbor.state not in (NodeState.IGNORE, NodeState.VISITED, territory):
        if (neighbor.state != NodeState.IGNORE) and (neighbor.state != territory):
            found: bool = DFSWithCallback(neighbor, territory, visited, f, depth - 1)
            if found:
                return True

    return False


def DFSWithCallbackAfter(
    node: Node,
    parent: Node,
    visited: List[Node],
    f: Callable[..., bool],
    args: Dict[Any, Any],
) -> bool:
    visited.append(node)
    for neighbor in node.values():
        if neighbor not in visited:
            if DFSWithCallbackAfter(neighbor, node, visited, f, args):
                return True

    if node == parent:
        return False

    return f(node, parent, args)


def DFSWithCallbackAndPosition(
    node: Node,
    position: Position,
    territory: NodeState,
    visited: list[Node],
    f: Callable[..., bool],
    depth: int,
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
    if f(node, position):
        return True
    if depth == 0:
        return False

    node.state = territory
    visited.append(node)

    for direction, neighbor in node.items():
        # if neighbor.state not in (NodeState.IGNORE, NodeState.VISITED, territory):
        if (neighbor.state != NodeState.IGNORE) and (neighbor.state != territory):
            found: bool = DFSWithCallbackAndPosition(
                neighbor,
                deltaPosition(direction, position),
                territory,
                visited,
                f,
                depth - 1,
            )
            if found:
                return True

    return False


Grid = Dict[Position, Tuple[int, Node]]
World = Dict[int, List[Tuple[Position, Node]]]


def DFSWithPath(
    node: Node,
    n: int,
    place: Dict[Position, Tuple[int, Node, Position]],
    previousPosition: Position,
    currentPosition: Position,
    visited: List[Node],
) -> None:
    """Visit Nodes until maximum depth is reached, and save which position you
    came from to build up a path on how to get to each node

    :param node: Start Node
    :param n: depth
    :param place: the world
    :param previousPosition: where you came from
    :param currentPosition: where you are
    :param visited: all visited Nodes
    """
    if currentPosition not in place or n > place[currentPosition][0]:
        place[currentPosition] = (n, node, previousPosition)

    if n == 0:
        return

    for direction, neighbor in node.items():
        if neighbor not in visited:
            DFSWithPath(
                neighbor,
                n - 1,
                place,
                currentPosition,
                deltaPosition(direction, currentPosition),
                [node] + visited,
            )


Line = Tuple[Position, Position]


def DFStest(
    node: Node,
    parent: Node,
    n: int,
    previousPosition: Position,
    currentPosition: Position,
    visited: List[Node],
    lineSpace={},  # Required acyclic graph
) -> Dict[int, List[Line]]:
    if n < 0:
        return lineSpace

    for direction, neighbor in node.items():
        if neighbor not in visited:
            lineSpace = DFStest(
                neighbor,
                node,
                n - 1,
                currentPosition,
                deltaPosition(direction, currentPosition),
                [node] + visited,
                lineSpace=lineSpace,
            )

    if node == parent:
        return lineSpace

    if n not in lineSpace:
        lineSpace[n] = []

    lineSpace[n].append((previousPosition, currentPosition))

    return lineSpace


def relativeExplorer(
    node: Node,
    n: int,
    place: Grid,
    position: Position,
    visited: List[Node],
) -> None:
    """Explore the network similar to DFS but with limits
    and the added functionality to map the network to Eucleidian space.

    :param node: current Node to search
    :param n: depth of allowed concecutive movements
    :param place: the grid to build up
    :param position: current Eucleidian position
    :param visited: already visited Nodes
    """
    if position not in place or n > place[position][0]:
        place[position] = (n, node)

    # Maximum depth reached
    if n == 0:
        return

    for direction, neighbor in node.items():
        if neighbor.state == NodeState.NOT_VISITED:
            neighbor.state = NodeState.VISITED  # Must clean afterwards
            visited.append(neighbor)
            relativeExplorer(
                neighbor,
                n - 1,
                place,
                deltaPosition(direction, position),
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

    visited: List[Node] = []
    DFSWithCallback(node, NodeState.VISITED, visited, f, INFINITY)
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
        and node in pivot  # --||--
        and not node.isLocked()
        and not isArticulationPoint(node)
    ):
        return False

    # Will always be a Direction
    previousDirection: Direction | None = node.directionTo(pivot)
    if previousDirection is None:
        raise ValueError("Previous direction is undefined")

    # Determine what object will take pivots position
    potential: Direction = Direction.rotate(previousDirection, -rotation)

    # Since pivot stays on the same place, any other than None or pivot cannot
    # take its place
    if node[potential] in (pivot, None):
        # All nodes except those behind (and) pivot will be rotated
        pivot.state = NodeState.IGNORE
        rotateAll(node, rotation)
        pivot.state = NodeState.NOT_VISITED

        newDirection: Direction = Direction.rotate(previousDirection, rotation)

        node[newDirection] = node[previousDirection]
        node[previousDirection] = pivot
        return True

    else:  # Could not bend
        return False


def countCollisions(startNode: Node) -> int:
    def f(
        node: Node,
        position: Position,
        place: Dict[Node, List[Position]],
        visited: List[Node],
    ):
        if node not in place:
            place[node] = [position]
        elif position not in place[node]:  # Node exists in multiple places. Bad...
            place[node].append(position)
            print("I exists on multiple places...")
        else:
            return

        for direction, neighbor in node.items():
            if neighbor not in visited:
                f(
                    neighbor,
                    deltaPosition(direction, position),
                    place,
                    [neighbor] + visited,
                )

    world = {}
    f(startNode, ORIGO, world, [])

    all_positions = set()

    collisions: int = 0

    for positions in world.values():
        for position in positions:
            if position in all_positions:
                collisions += 1
            else:
                all_positions.add(position)

    return collisions


class Engine:
    """Engine for relative Nodes

    This engine allows the user to:

    * Traverse
    * Search Data
    * Add/Insert
    * Remove/Delete
    * Store Data
    * Shortest route to Data
    * Rotate + fold network
    * Relative -> 2D untangling

    Several optimizations are enabled to work efficiently. The engine prunes
    redundant Nodes when encountered. This behaviour can be prevented by manually
    locking Nodes.


    :param mode: The mode for the engine to operate in
    :param depth: operation depth
    :param node: current Node
    :param start: initial Node
    :param previous: previous Node
    :param grid: 2D representation
    """

    def __init__(self, mode: EngineMode, depth: int):
        assert isinstance(
            mode, EngineMode
        ), "You must have a valid EngineMode, not: " + str(mode)

        assert isinstance(
            depth, int
        ), "The visibility must be a posivive integer, not: " + str(depth)
        assert 0 <= depth, "depth must be a posivite integer, not: " + str(depth)

        self.mode: EngineMode = mode
        self.depth: int = depth
        self.setDepth(depth)
        self.setMode(mode)

        self.node: Node = Node()
        self.start: Node = self.node
        self.node.toggleLock()

        self.previous: Node = self.node

        # World stuff
        self.grid: Grid = {}
        self.world: World = {}
        self.path: List[Node] = []

        self.update()

    def setDrawer(self, f: Callable[..., None]) -> None:
        self.drawer = f

    def search(self, node: Node) -> List[Node]:
        """Search for a Node in the network

        WARNING if Node is not present in the Engine, an empty list will be
        returned

        :param node: target Node
        :return: depthed path to Node
        """
        q = Queue()
        q.put(self.node)

        visited: List[Node] = []
        pathMap: Dict[Node, Node] = {}

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
        path: List[Node] = []

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
            if other == self.node:
                break
            i += 1

        return path

    def getDepth(self) -> int:
        """Getter for depth

        :return: int
        """
        return self.depth

    def setDepth(self, value: int) -> None:
        """Setter for engine traversal depth

        :param value: new positive integer
        """
        assert isinstance(value, int), "Invalid range type: " + str(value)
        assert value >= 0, "Invalid range: " + str(value)
        if self.depth != value:
            self.depth = value
            print("Changing depth")
            self.update()

    def getPath(self) -> List[Node]:
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
        near: Tuple[Direction, Direction] = NEARBY_DIRECTION_MAP[direction]
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

        if direction is None:  # This should not happen!?
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
        all_visited: List[Node] = []
        relativeExplorer(self.node, self.depth, self.grid, ORIGO, all_visited)

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
        previousCollisions: int = countCollisions(self.node)
        if not bend(self.node, self.previous, rotation):
            # return False
            rotateAll(self.node, rotation)

        else:
            if countCollisions(self.node) > previousCollisions:
                if self.mode != EngineMode.LIMINAL:
                    bend(self.node, self.previous, -rotation)

                    print("You can only bend with collisions in LIMINAL mode")

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

        if self.mode == EngineMode.READ_ONLY:
            return False

        def rec(node: Node, parent: Node, visited: List[Node]):
            visited.append(node)
            flattened: bool = False

            for neighbor in node.values():
                if neighbor not in visited:
                    flattened = rec(neighbor, node, visited)

            if node == parent:
                return flattened
            parentDirection: Direction | None = parent.directionTo(node)

            if parentDirection is None:  # This happens in directed graphs
                return flattened

            n_neighbors: int = len(node)

            if n_neighbors not in (0, ALL_DIRECTIONS - 1):
                rotation: Rotation = -1

                while (node[parentDirection] is None) and (rotation < 2):
                    if rotation != 0 and bend(node, parent, rotation):
                        flattened = True
                    rotation += 1

            return flattened

        visited: List[Node] = []
        flattened: bool = rec(self.node, self.node, visited)
        if flattened:
            print("Performed optimization")
            self.update()

        return flattened

    def _untangle(self) -> bool:
        """Naive untanglement where backtracking is used together with DFS to
        bend around the network until no further collisions are present. This
        algorithm is not fully optimized but a POC that is actually able to
        untangle some networks using trial and error. This algorithm is
        destructive by rotating the network, but no Nodes are:

        * Connected
        * Disconnected
        * Removed
        * Added

        Maybe the user wants to reconnect the network after the untanglement to
        fix new neighbors and remove redundant nodes?

        :return: status
        """
        if self.mode == EngineMode.READ_ONLY:
            return False

        collisions: int = countCollisions(self.node)  # This function costs a lot

        if collisions == 0:
            print("Nothing to untangle :)")
            return False

        def rec(node: Node, parent: Node, visited: List[Node], collisions: List[int]):
            visited.append(node)
            done: bool = False

            for neighbor in node.values():
                if neighbor not in visited:
                    done = rec(neighbor, node, visited, collisions)
                    if done:
                        return True

            if collisions[0] == 0:
                return True

            if node == parent:
                return done
            parentDirection: Direction | None = parent.directionTo(node)

            if parentDirection is None:  # This happens in directed graphs
                return done

            n_neighbors: int = len(node)

            if n_neighbors not in (0, ALL_DIRECTIONS - 1):
                rotation: Rotation = -1

                didUntangle = False
                haveBend = False

                # rotationCount: Rotation = 0
                #
                # toCheck: Tuple[Rotation, Rotation] = (-1, 2)
                #
                # rotation = -1
                #
                # tmpBest = collisions[0]
                #
                # tryAnother = False
                #
                # if bend(node, parent, rotation):
                #     currentCollisions = countCollisions(node)
                #
                #     if currentCollisions == 0:
                #         collisions[0] -= collisions[0] - currentCollisions
                #         return True  # Done
                #     elif currentCollisions < tmpBest:
                #         tmpBest = currentCollisions
                #
                #     else:
                #         rotation = 2

                while not didUntangle and (rotation < 2):
                    if rotation != 0 and bend(node, parent, rotation):
                        currentCollisions = countCollisions(node)
                        haveBend = True

                        if currentCollisions == 0:
                            # Why is python so evil... why cant i modify global
                            # collisions...

                            collisions[0] -= collisions[0] - currentCollisions
                            # print("FOUND DONE")
                            return True  # Done
                        elif currentCollisions < collisions[0]:
                            didUntangle = True
                            collisions[0] -= collisions[0] - currentCollisions
                            # print("FOUND")

                    rotation += 1

                if haveBend and not didUntangle:
                    bend(node, parent, -rotation)

            return done

        visited: List[Node] = []
        # print(collisions)
        collisionCount = [collisions]
        flattened: bool = rec(self.node, self.node, visited, collisionCount)
        # print(collisionCount[0])
        if collisionCount[0] == 0:
            print("Fully converted to absolute space!")

        elif collisionCount[0] < collisions:
            print("Making progress")

        elif (
            not flattened and collisionCount[0] > 0
        ):  # This is bad, the system cannot convert to 2D
            # space, it is up to the user to fix collisions. This required deletions
            # of Nodes. I am not sure if this is a global error or if it can be
            # mitigated by simply going to a different node
            print(
                "Absolute-space error. Cannot perform automatic untanglement. User intervention is required!"
            )

        self.update()

        return True

    def drawState(self):
        self.update()
        self.drawer()

    def untangle(self) -> bool:
        """Naive untanglement where backtracking is used together with DFS to
        bend around the network until no further collisions are present. This
        algorithm is not fully optimized but a POC that is actually able to
        untangle some networks using trial and error. This algorithm is
        destructive by rotating the network, but no Nodes are:

        * Connected
        * Disconnected
        * Removed
        * Added

        Maybe the user wants to reconnect the network after the untanglement to
        fix new neighbors and remove redundant nodes?

        :return: status
        """
        if self.mode == EngineMode.READ_ONLY:
            return False

        collisions: int = countCollisions(self.node)  # This function costs a lot

        if collisions == 0:
            print("Nothing to untangle :)")
            return False

        def rectifier(node: Node, parent: Node, args):
            parentDirection: Direction | None = parent.directionTo(node)

            if parentDirection is None:  # This happens in directed graphs
                print("This should not happen")
                return False

            n_neighbors: int = len(node)

            if n_neighbors not in (0, ALL_DIRECTIONS - 1):
                didUntangle: bool = False

                tmpBest = args["collisions"]

                if bend(node, parent, -1):
                    currentCollisions = countCollisions(node)
                    if currentCollisions < tmpBest:
                        tmpBest = currentCollisions
                        didUntangle = True
                    # elif currentCollisions > tmpBest:
                    #     bend()

                    if bend(node, parent, 2):
                        currentCollisions = countCollisions(node)
                        if currentCollisions < tmpBest:
                            tmpBest = currentCollisions  # Done
                        elif didUntangle and (currentCollisions > tmpBest):
                            bend(node, parent, -2)  # Undo :/
                        else:
                            bend(node, parent, -1)
                    else:
                        if not didUntangle:
                            bend(node, parent, 1)

                else:  # Test only the other rotation
                    if bend(node, parent, 1):
                        currentCollisions = countCollisions(node)
                        if currentCollisions < tmpBest:
                            tmpBest = currentCollisions  # Done

                        else:
                            bend(node, parent, -1)

                if tmpBest < args["collisions"]:
                    args["collisions"] = tmpBest
                    args["draw"]()
                    import time

                    time.sleep(0.3)

                return args["collisions"] == 0

            return False

        args = {"collisions": collisions, "draw": self.drawState}

        aNode: Node = self.node

        for i in range(10):
            previousCollisionCount: int = args["collisions"]
            done: bool = DFSWithCallbackAfter(aNode, aNode, [], rectifier, args)

            if done:
                print("Fully converted to absolute space")
                break
            elif args["collisions"] < previousCollisionCount:
                print("making progress")
            else:  # This is bad
                print("Unable to convert to absolute space")
                break
        self.update()

        return True
        errorCount = 0

        # print(collisions)
        collisionCount = [collisions]

        tested: List[Node] = []
        print(args)

        visited: List[Node] = []

        while True and errorCount < 10:
            visited = []
            flattened: bool = DFSWithCallbackAfter(aNode, aNode, [], rectifier, args)
            print(args)
            break
            # print(collisionCount[0])
            if collisionCount[0] == 0:
                print("Fully converted to absolute space!")
                break

            elif collisionCount[0] < collisions:
                collisions = collisionCount[0]
                print("Making progress")

            elif (
                not flattened and collisionCount[0] > 0
            ):  # This is bad, the system cannot convert to 2D
                # space, it is up to the user to fix collisions. This required deletions
                # of Nodes. I am not sure if this is a global error or if it can be
                # mitigated by simply going to a different node

                tested.append(aNode)

                neighbors = list(aNode.values())
                for neighbor in neighbors:
                    if neighbor not in tested:
                        aNode = neighbor
                errorCount += 1
        if errorCount >= 10:
            print(
                "Absolute-space error. Cannot perform automatic untanglement. User intervention is required!"
            )

        self.update()

        return True

        def rec(node: Node, parent: Node, visited: List[Node], collisions: List[int]):
            visited.append(node)
            done: bool = False

            for neighbor in node.values():
                if neighbor not in visited:
                    done = rec(neighbor, node, visited, collisions)
                    if done:
                        return True

            if collisions[0] == 0:
                return True

            if node == parent:
                return done
            parentDirection: Direction | None = parent.directionTo(node)

            if parentDirection is None:  # This happens in directed graphs
                return done

            n_neighbors: int = len(node)

            if n_neighbors not in (0, ALL_DIRECTIONS - 1):
                didUntangle: bool = False

                tmpBest = collisions[0]

                if bend(node, parent, -1):
                    currentCollisions = countCollisions(node)
                    if currentCollisions < tmpBest:
                        tmpBest = currentCollisions
                        didUntangle = True
                    # elif currentCollisions > tmpBest:
                    #     bend()

                    if bend(node, parent, 2):
                        currentCollisions = countCollisions(node)
                        if currentCollisions < tmpBest:
                            tmpBest = currentCollisions  # Done
                        elif didUntangle and (currentCollisions > tmpBest):
                            bend(node, parent, -2)  # Undo :/
                        else:
                            bend(node, parent, -1)
                    else:
                        if not didUntangle:
                            bend(node, parent, 1)

                else:  # Test only the other rotation
                    if bend(node, parent, 1):
                        currentCollisions = countCollisions(node)
                        if currentCollisions < tmpBest:
                            tmpBest = currentCollisions  # Done

                        else:
                            bend(node, parent, -1)

                if tmpBest < collisions[0]:
                    collisions[0] -= collisions[0] - tmpBest

                if collisions[0] == 0:
                    return True

            return done

        visited: List[Node] = []
        # print(collisions)
        collisionCount = [collisions]

        aNode: Node = self.node
        errorCount = 0

        tested: List[Node] = []

        while True and errorCount < 10:
            visited = []
            flattened: bool = rec(aNode, aNode, visited, collisionCount)
            # print(collisionCount[0])
            if collisionCount[0] == 0:
                print("Fully converted to absolute space!")
                break

            elif collisionCount[0] < collisions:
                collisions = collisionCount[0]
                print("Making progress")

            elif (
                not flattened and collisionCount[0] > 0
            ):  # This is bad, the system cannot convert to 2D
                # space, it is up to the user to fix collisions. This required deletions
                # of Nodes. I am not sure if this is a global error or if it can be
                # mitigated by simply going to a different node

                tested.append(aNode)

                neighbors = list(aNode.values())
                for neighbor in neighbors:
                    if neighbor not in tested:
                        aNode = neighbor
                errorCount += 1
        if errorCount >= 10:
            print(
                "Absolute-space error. Cannot perform automatic untanglement. User intervention is required!"
            )

        self.update()

        return True

    def prune(self) -> None:
        """Prune network by connecting all nodes that may be connected"""
        if self.mode == EngineMode.READ_ONLY:
            return

        def f(other: Node, position: Position) -> bool:
            connectNearby(other, self.grid, position)
            return False

        visited: List[Node] = []
        DFSWithCallbackAndPosition(
            self.node, ORIGO, NodeState.VISITED, visited, f, INFINITY
        )
        cleanVisited(visited)

        # def f2(other: Node) -> bool:
        #     if other is self.node:
        #         return False
        #     if (
        #         other.canRemove()
        #         and not isArticulationPoint(other)
        #         and not other.isLeaf()
        #     ):
        #         other.remove()
        #
        #     return False
        #
        # visited: List[Node] = []
        # DFSWithCallback(self.node, NodeState.VISITED, visited, f2, INFINITY)
        # cleanVisited(visited)
        self.update()


def connectNearby(node: Node, grid: Grid, position: Position) -> bool:
    """Checks for all potential neighbors to Node and tries to connect them.

    :param node: Current Node to extend
    :param grid: the grid
    :param position: Current Position
    """
    newConnections: bool = False
    for direction in Direction:
        if node[direction] is None:
            newPos: Position = deltaPosition(direction, position)
            if newPos in grid:
                otherNode: Node = grid[newPos][1]
                if node.canConnect(direction, otherNode):
                    node.connect(direction, otherNode)
                    newConnections = True
                else:
                    node.log("Could not connect")

    return newConnections


def traverse(node: Node, direction: Direction, grid: Grid, mode: EngineMode) -> Node:
    """Traverse a relative network and maybe build more of it. This is a central
    function in the engine that is responsible for how the movement is handled.

    :param node: Current Node
    :param direction: Desired Direction
    :param grid: current layout
    :param mode: how to behave when traversing
    :return: Your new Node (or previous if Failure)
    """

    position: Position = deltaPosition(direction, ORIGO)

    # Will add a new node in any case, except immediate neighbor exist
    if mode == EngineMode.LIMINAL:
        neighbor: Node | None = node[direction]
        if neighbor is None:
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
