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
# GPT VERSION
# Global variables
stop_signal = False

# Sensors & Motors
EMERGENCY_STOP = TouchSensor(4)
ULTRASONIC_SENSOR = EV3UltrasonicSensor(3, mode="cm")         # Front-facing; confirm port if needed
ULTRASONIC_SENSOR_LEFT = EV3UltrasonicSensor(1, mode="cm")    # Left-facing (new); confirm port if needed
COLOUR_SENSOR = EV3ColorSensor(2)
LEFT_MOTOR = Motor("A")
RIGHT_MOTOR = Motor("B")
COLOUR_MOTOR = Motor("C")  # Rotating color sensor (not used in this script)
siren_sound = Sound(duration=0.5, pitch="C4", volume=100)

# Calibration constants
TARGET_LEFT_DISTANCE = 2.5  # Desired distance from left wall (in cm); adjust as needed
TURN_MOTOR_DEGREES_FOR_90 = 180  # Motor encoder degrees for a 90° turn; calibrate this

# ----------------------------
# Helper Functions for Driving
# ----------------------------
def drive_forward_with_correction(power=-20, duration=0.5):
    """
    Drives forward while using the left ultrasonic sensor to correct its path.
    If the robot is too far from the left wall, it steers left.
    If too close, it steers right.
    """
    if stop_signal:
        return
    distance_left = ULTRASONIC_SENSOR_LEFT.get_cm()
    adjustment = 5  # Adjustment factor for correction
    margin = 1      # Allowable margin in cm

    if distance_left is not None:
        if distance_left > TARGET_LEFT_DISTANCE + margin:
            # Too far from wall: steer left (left motor faster, right motor slower)
            left_speed = power - adjustment  # More negative = faster
            right_speed = power + adjustment
            correction = "left"
        elif distance_left < TARGET_LEFT_DISTANCE - margin:
            # Too close to wall: steer right (left motor slower, right motor faster)
            left_speed = power + adjustment
            right_speed = power - adjustment
            correction = "right"
        else:
            left_speed = power
            right_speed = power
            correction = "straight"
    else:
        left_speed = power
        right_speed = power
        correction = "straight"

    LEFT_MOTOR.set_power(left_speed)
    RIGHT_MOTOR.set_power(right_speed)
    time.sleep(duration)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print(f"Correction applied: {correction} (Left Distance: {distance_left})")

def turn_robot(angle):
    """
    Turns the robot by a specified angle in degrees.
    Positive angle turns right; negative turns left.
    Uses motor encoder feedback to determine when the desired turn is complete.
    The constant TURN_MOTOR_DEGREES_FOR_90 is used as a basis for a 90° turn.
    """
    if stop_signal:
        return
    # Reset motor encoders
    LEFT_MOTOR.set_position(0)
    RIGHT_MOTOR.set_position(0)
    
    # Calculate target motor rotation based on the desired angle.
    # For a 90° turn, each motor should rotate by TURN_MOTOR_DEGREES_FOR_90 degrees on average.
    target_rotation = abs(angle) / 90 * TURN_MOTOR_DEGREES_FOR_90
    
    turn_speed = 200  # Degrees per second (adjust as needed)
    if angle > 0:
        # Turn right: left motor forward, right motor backward.
        LEFT_MOTOR.set_dps(turn_speed)
        RIGHT_MOTOR.set_dps(-turn_speed)
    else:
        # Turn left: left motor backward, right motor forward.
        LEFT_MOTOR.set_dps(-turn_speed)
        RIGHT_MOTOR.set_dps(turn_speed)
    
    # Wait until the average motor rotation meets the target.
    while not stop_signal:
        left_deg = abs(LEFT_MOTOR.get_position())
        right_deg = abs(RIGHT_MOTOR.get_position())
        avg_deg = (left_deg + right_deg) / 2
        if avg_deg >= target_rotation:
            break
        time.sleep(0.01)
    
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print(f"Turned {'right' if angle > 0 else 'left'} by {abs(angle)}° (target motor rotation: {target_rotation}°)")

def turn_right_90():
    """Turns the robot right exactly 90°."""
    turn_robot(90)

def turn_left_90():
    """Turns the robot left exactly 90°."""
    turn_robot(-90)

# ----------------------------
# Threads for Emergency and Siren
# ----------------------------
def monitor_emergency_stop():
    global stop_signal
    while not stop_signal:
        if EMERGENCY_STOP.is_pressed():
            print("Emergency Stop Activated!")
            stop_signal = True
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            reset_brick()
            break
        time.sleep(0.1)

def play_siren():
    while not stop_signal:
        siren_sound.play()
        time.sleep(0.5)

# ----------------------------
# Test Sequence
# ----------------------------
def subsystem_test():
    global stop_signal

    # Start emergency stop and siren threads
    emergency_thread = threading.Thread(target=monitor_emergency_stop)
    siren_thread = threading.Thread(target=play_siren)
    emergency_thread.start()
    siren_thread.start()

    print("Subsystem Test Started.")

    # Step 1: Drive forward until front sensor detects a wall at 55 cm
    while not stop_signal:
        drive_forward_with_correction(power=-20, duration=0.4)
        front_distance = ULTRASONIC_SENSOR.get_cm()
        if front_distance is not None and front_distance <= 55:
            print(f"Front wall detected at {front_distance} cm.")
            break

    # Step 2: Turn right 90°
    turn_right_90()
    print("Turned right 90°.")

    # Step 3: Drive forward until front sensor detects a wall at 30 cm
    while not stop_signal:
        drive_forward_with_correction(power=-20, duration=0.4)
        front_distance = ULTRASONIC_SENSOR.get_cm()
        if front_distance is not None and front_distance <= 30:
            print(f"Wall detected at {front_distance} cm.")
            break

    # Step 4: Turn left 90°
    turn_left_90()
    print("Turned left 90°.")

    stop_signal = True
    siren_thread.join()
    emergency_thread.join()
    print("Subsystem Test Completed.")

# ----------------------------
# Main Execution
# ----------------------------
if __name__ == "__main__":
    wait_ready_sensors(True)
    print("Firefighter Robot Subsystem Test Initialized.")
    subsystem_test()
    print("System shut down.")
