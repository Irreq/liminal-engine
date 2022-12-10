# liminal-engine

Liminal space engine. It is essentially just
walking around nodes in a partially linked data structure. 

What this means is that in our 2D way of thinking,
if you are walking in this pattern:

             (x, y) → → →
                ↑         ↓
                 ←  ←   ←

You should end up in the place you initially started at. However in liminal
space you will end up at the same coordinates, but in a different place.
This means that multiple places can coexist at the same coordinate, so the
*only way to get back to where you started is to walk back the way you came
from. This is because this engine is associative and not absolute like a
grid.

**With this implementation you can actually have tolerance and be able to get
back to where you started by walking "close" to where you walked earlier.*

Some interesting features with this engine:

0. You can create one way paths to drastically reduce travel distance in
one direction.

1. You can create points like: A → → → → A
this could mean that if you were to walk in maybe a straight line,
you will end up in the place where you started.

2. You can create portals, which is saying the two points are actually
sharing an edge, even though they according to our
2D walking logic, shouldn't.

3. You can create spaces that are "smaller" or "bigger" on the inside. It is
worth noting that the concepts of size have no meaning in this realm, but we
can estimate them from our perspective.

4. You can create prisons, which is places with no way out
(disconnected component)

5. Probing a point far away is practically impossible and almost meaningless
because you are probably more interested in knowing what the point is, not
where it is located.

## Usage
You can try out a demo with pygame:

    python3 demo.py

The effect can be broken by reducing the darkness created by the `utils.py` file
but it is recomended to have darkness in order to reduce calculations.