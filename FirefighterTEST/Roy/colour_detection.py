
from enum import Enum
from math import sqrt

class Colour(Enum):
    WHITE = 1
    YELLOW = 2
    ORANGE = 3
    GREEN = 4
    RED = 5

def colour_distance(xs: list[int], ys: list[int]) -> float:
    """
    This function should define a distance metric over the vector space R^3.
    """
    return sqrt(sum((a - b) ** 2 for a, b in zip(xs, ys)))

def rgb_to_colour(rgb: list[int]) -> Colour:
    """
    Converts a colour, expressed as an RGB value from the colour sensor, to one
    of five known colours which will be useful for the robot.

    This function performs a nearest-neighbour search within a metric space of
    RGB values, with metric defined by the `color_distance` function.
    """
    colours = [
        ([306, 258, 126], Color.WHITE),
        ([284, 177, 20], Color.YELLOW),
        ([237, 56, 12], Color.ORANGE),
        ([149, 176, 16], Color.GREEN),
        ([180, 21, 8], Color.RED),
    ]

    return min(colours, key=lambda c: colour_distance(c[0], rgb))[1]
