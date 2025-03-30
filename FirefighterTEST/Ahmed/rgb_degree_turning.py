
import time
from utils.brick import Motor
from enum import Enum
from math import sqrt

# Constants for movement
WHEEL_SEPARATION_CM = 15
WHEEL_DIAMETER_CM = 4

# Drive Motors for aligning the robot (assumed ports)
LEFT_DRIVE = Motor("A")
RIGHT_DRIVE = Motor("B")

class Color(Enum):
    WHITE = 1
    YELLOW = 2
    ORANGE = 3
    GREEN = 4
    RED = 5

def color_distance(xs: list[int], ys: list[int]) -> float:
    """
    This function should define a distance metric over the vector space R^3.
    """
    return sqrt(sum((a - b) ** 2 for a, b in zip(xs, ys)))

def rgb_to_color(rgb: list[int]) -> Color:
    """
    Converts a colour, expressed as an RGB value from the colour sensor, to one
    of five known colours which will be useful for the robot.

    This function performs a nearest-neighbour search within a metric space of
    RGB values, with metric defined by the `color_distance` function.
    """
    colors = [
        ([306, 258, 126], Color.WHITE),
        ([284, 177, 20], Color.YELLOW),
        ([237, 56, 12], Color.ORANGE),
        ([149, 176, 16], Color.GREEN),
        ([180, 21, 8], Color.RED),
    ]

    return min(colors, key=lambda c: color_distance(c[0], rgb))[1]

def rotate_robot(angle):
    """
    Rotates the robot in place by the specified angle.
    Positive angle rotates right; negative rotates left.
    """
    if angle == 0:
        print("Not rotating robot.")
        return
    wheel_angle = angle * WHEEL_SEPARATION_CM / WHEEL_DIAMETER_CM
    print(f"Rotating robot by {angle}° (counter-rotating wheels by {wheel_angle}°).")
    if angle > 0:
        # To rotate right: left motor forward, right motor backward.
        left_power = 30
        right_power = -30
    elif angle < 0:
        # To rotate left: left motor backward, right motor forward.
        left_power = -30
        right_power = 30

    LEFT_DRIVE.set_power(left_power)
    RIGHT_DRIVE.set_power(left_power)

    left_moving = True
    left_slow = False
    right_moving = True
    right_slow = False
    while True:
        if left_moving and abs(LEFT_MOTOR.get_position()) > max(0, abs(wheel_angle) - 20):
            LEFT_MOTOR.set_power(left_power // 2)
            left_moving = False
            left_slow = True
        if right_moving and abs(RIGHT_MOTOR.get_position()) > max(0, abs(wheel_angle) - 20):
            RIGHT_MOTOR.set_power(right_power // 2)
            right_moving = False
            right_slow = True

        if left_slow and abs(LEFT_MOTOR.get_position()) > abs(wheel_angle):
            LEFT_MOTOR.set_power(0)
            left_slow = False
        if right_slow and abs(RIGHT_MOTOR.get_position()) > abs(wheel_angle):
            RIGHT_MOTOR.set_power(0)
            right_slow = False

        if (not left_moving and not right_moving
            and not left_slow and not right_slow):
            break

        time.sleep(0.05)

    print("Rotation complete.")
