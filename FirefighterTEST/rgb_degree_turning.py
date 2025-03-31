
import time
from utils.brick import Motor
from enum import Enum
from math import sqrt, pi
import threading
import time
from utils.brick import (
    TouchSensor,
    EV3UltrasonicSensor,
    EV3ColorSensor,
    Motor,
    wait_ready_sensors,
    reset_brick,
)
from utils.sound import Sound
stop_signal = False
fires_extinguished = 0
siren_stop = False

# ----------------------------
# Sensors & Motors (Check ports)
# ----------------------------
EMERGENCY_STOP = TouchSensor(4)
ULTRASONIC_SENSOR = EV3UltrasonicSensor(3, mode="cm")         # Front
ULTRASONIC_SENSOR_LEFT = EV3UltrasonicSensor(1, mode="cm")    # Left
COLOUR_SENSOR = EV3ColorSensor(2, mode="id")                  # Front on rotating motor
LEFT_MOTOR = Motor("A")
RIGHT_MOTOR = Motor("B")
COLOUR_MOTOR = Motor("C")                                      # Rotates color sensor
FIRE_SUPPRESSION_MOTOR = Motor("D")                           # Drops sandbag
siren_sound = Sound(duration=0.5, pitch="C4", volume=100)

TARGET_LEFT_DISTANCE = 8  # Distance to maintain from the left wall
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

def rotate_robot(angle: int) -> None:
    """
    Rotates the robot in place by the specified angle (in degrees).
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

    left_init_pos = LEFT_DRIVE.get_position()
    right_init_pos = RIGHT_DRIVE.get_position()

    LEFT_DRIVE.set_power(left_power)
    RIGHT_DRIVE.set_power(left_power)

    left_moving = True
    left_slow = False
    right_moving = True
    right_slow = False
    while True:
        if left_moving and abs(LEFT_DRIVE.get_position() - left_init_pos) > max(0, abs(wheel_angle) - 20):
            LEFT_DRIVE.set_power(left_power // 2)
            left_moving = False
            left_slow = True
        if right_moving and abs(RIGHT_DRIVE.get_position() - right_init_pos) > max(0, abs(wheel_angle) - 20):
            RIGHT_DRIVE.set_power(right_power // 2)
            right_moving = False
            right_slow = True

        if left_slow and abs(LEFT_DRIVE.get_position() - left_init_pos) > abs(wheel_angle):
            LEFT_DRIVE.set_power(0)
            left_slow = False
        if right_slow and abs(RIGHT_DRIVE.get_position() - right_init_pos) > abs(wheel_angle):
            RIGHT_DRIVE.set_power(0)
            right_slow = False

        if (not left_moving and not right_moving
            and not left_slow and not right_slow):
            break

        time.sleep(0.05)

    print("Rotation complete.")

def move_straight(distance: float) -> None:
    """
    Moves the robot the given distance (in cm) straight forward (or backward in
    the case of negative input), using the motor encoders for feedback.
    """
    angle = distance * 720 // (WHEEL_DIAMETER_CM * pi)

    if angle > 0:
        left_power = -30
        right_power = -30
    elif angle < 0:
        left_power = 30
        right_power = 30
    else:
        print("Not moving robot.")
        return

    print(f"Moving robot {distance} cm forward.")

    left_init_pos = LEFT_DRIVE.get_position()
    right_init_pos = RIGHT_DRIVE.get_position()

    LEFT_DRIVE.set_power(left_power)
    RIGHT_DRIVE.set_power(right_power)
    left_moving = True
    right_moving = True
    left_slow = False
    right_slow = False

    time.sleep(0.25)

    while True:
        time.sleep(0.25)

        left_pos = LEFT_DRIVE.get_position()
        right_pos = RIGHT_DRIVE.get_position()
        if left_moving and abs(left_pos - left_init_pos) >= max(0, abs(angle) - 40):
            left_power //= 2
            left_moving = False
            left_slow = True
        elif left_slow and abs(left_pos - left_init_pos) >= abs(angle):
            left_power = 0
            left_slow = False
        if right_moving and abs(right_pos - right_init_pos) >= max(0, abs(angle) - 40):
            right_power //= 2
            right_moving = False
            right_slow = True
        elif right_slow and abs(right_pos - right_init_pos) >= abs(angle):
            right_power = 0
            right_slow = False
        if (not left_moving and not right_moving
            and not left_slow and not right_slow):
            break
        
        difference = (left_pos - left_init_pos) - (right_pos - right_init_pos)
        LEFT_DRIVE.set_power(left_power - difference)
        RIGHT_DRIVE.set_power(right_power + difference)

    LEFT_DRIVE.set_power(0)
    RIGHT_DRIVE.set_power(0)

    print("Movement complete.")


if __name__ == "__main__":
    # Wait for sensors to be ready
    wait_ready_sensors(True)
    print("Starting function tests...")

    # Test rotate_robot: rotate right 90° then left 90°
    print("Testing rotate_robot(90) – should rotate right 90°:")
    rotate_robot(90)
    time.sleep(1)
    print("Testing rotate_robot(-90) – should rotate left 90°:")
    rotate_robot(-90)
    time.sleep(1)

    # Test move_straight: move forward 20 cm, then move backward 20 cm
    print("Testing move_straight(20) – should move forward 20 cm:")
    move_straight(20)
    time.sleep(1)
    print("Testing move_straight(-20) – should move backward 20 cm:")
    move_straight(-20)
    time.sleep(1)

    print("All function tests complete.")
