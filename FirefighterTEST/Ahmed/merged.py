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

# Global variables
stop_signal = False
fires_extinguished = 0  # For fire suppression test
target_angle = 0        # Angle where a red sticker was detected

# Sensors & Motors
EMERGENCY_STOP = TouchSensor(4)
ULTRASONIC_SENSOR = EV3UltrasonicSensor(3, mode="cm")         # Front-facing ultrasonic sensor
ULTRASONIC_SENSOR_LEFT = EV3UltrasonicSensor(1, mode="cm")    # Left-facing ultrasonic sensor
COLOR_SENSOR = EV3ColorSensor(2, mode="id")   # Color sensor (using "id" mode)
# For sweeping the sensor, we use a dedicated motor:
COLOUR_MOTOR = Motor("C")
# Driving and fire suppression motors
LEFT_MOTOR = Motor("A")
RIGHT_MOTOR = Motor("B")
FIRE_SUPPRESSION_MOTOR = Motor("D")
siren_sound = Sound(duration=0.5, pitch="C4", volume=100)

# Calibration constants
TARGET_LEFT_DISTANCE = 2.5     # Desired distance from the left wall (cm)
TURN_MOTOR_DEGREES_FOR_90 = 180  # Encoder degrees corresponding to a 90° turn

# ----------------------------
# Helper Functions for Navigation
# ----------------------------
def drive_forward_with_correction(power=-20, duration=0.5):
    """
    Drives forward while using the left ultrasonic sensor to correct its path.
    If the robot is too far from the wall it steers left;
    if too close, it steers right.
    """
    if stop_signal:
        return
    distance_left = ULTRASONIC_SENSOR_LEFT.get_cm()
    margin = 1      # Allowable margin (cm)
    adjustment = 5  # Adjustment value for power correction

    if distance_left is not None:
        if distance_left > TARGET_LEFT_DISTANCE + margin:
            # Too far from wall – steer left (right motor gets extra power)
            left_speed = power
            right_speed = power + adjustment
            correction = "left"
        elif distance_left < TARGET_LEFT_DISTANCE - margin:
            # Too close to wall – steer right (left motor gets extra power)
            left_speed = power + adjustment
            right_speed = power
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

def turn_right_90():
    """Turns right exactly 90° using motor encoders."""
    if stop_signal:
        return
    LEFT_MOTOR.set_position(0)
    RIGHT_MOTOR.set_position(0)
    LEFT_MOTOR.set_dps(200)
    RIGHT_MOTOR.set_dps(-200)
    while abs(LEFT_MOTOR.get_position()) < 180 and not stop_signal:
        time.sleep(0.01)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print("Turned right 90°.")

def turn_left_90():
    """Turns left exactly 90° using motor encoders."""
    if stop_signal:
        return
    LEFT_MOTOR.set_position(0)
    RIGHT_MOTOR.set_position(0)
    LEFT_MOTOR.set_dps(-200)
    RIGHT_MOTOR.set_dps(200)
    while abs(RIGHT_MOTOR.get_position()) < 180 and not stop_signal:
        time.sleep(0.01)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print("Turned left 90°.")

# ----------------------------
# Helper Functions for Fire Suppression
# ----------------------------
def rotate_sensor_to_position(target, speed, threshold=2):
    """
    Rotates the sensor motor to an absolute position (in degrees)
    using feedback from get_position() until within a threshold.
    """
    current = COLOUR_MOTOR.get_position()
    while abs(current - target) > threshold and not stop_signal:
        if current < target:
            COLOUR_MOTOR.set_power(speed)
        else:
            COLOUR_MOTOR.set_power(-speed)
        time.sleep(0.02)
        current = COLOUR_MOTOR.get_position()
    COLOUR_MOTOR.set_power(0)
    print(f"Sensor rotated to target angle {target}° (current: {current}°).")

def rotate_robot(angle):
    """
    Rotates the entire robot by the specified angle.
    Positive angle rotates right; negative rotates left.
    The rotation time is based on a simple conversion (90° per second).
    """
    rotation_time = abs(angle) / 90.0  # Adjust conversion factor as needed
    print(f"Rotating robot by {angle}° (estimated {rotation_time:.2f}s).")
    if angle > 0:
        LEFT_MOTOR.set_power(30)
        RIGHT_MOTOR.set_power(-30)
    elif angle < 0:
        LEFT_MOTOR.set_power(-30)
        RIGHT_MOTOR.set_power(30)
    time.sleep(rotation_time)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print("Rotation complete.")

def drop_sandbag_with_alignment(angle):
    """
    Uses the detected sensor angle to align the robot so that the red sticker is centered,
    then drops the sandbag. After deployment, the robot rotates back.
    """
    print(f"Aligning robot using sensor angle: {angle}°")
    rotate_robot(angle)
    print("🪣 Dropping sandbag on fire...")
    FIRE_SUPPRESSION_MOTOR.set_power(30)
    time.sleep(1)  # Time to drop the sandbag
    FIRE_SUPPRESSION_MOTOR.set_power(-30)
    time.sleep(1)
    FIRE_SUPPRESSION_MOTOR.set_power(0)
    print("Sandbag deployed.")
    rotate_robot(-angle)

def avoid_blue_sticker(angle):
    """
    Initiates an avoidance maneuver when a blue sticker is detected.
    The robot backs up and turns away from the blue sticker.
    """
    print(f"Blue sticker detected at angle {angle}°. Initiating avoidance maneuver.")
    LEFT_MOTOR.set_power(-20)
    RIGHT_MOTOR.set_power(-20)
    time.sleep(0.5)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    if angle > 0:
        print("Turning left to avoid blue sticker.")
        rotate_robot(-45)
    else:
        print("Turning right to avoid blue sticker.")
        rotate_robot(45)
    print("Avoidance maneuver complete.")

def scan_and_extinguish_fires():
    """
    Sweeps the color sensor (via COLOUR_MOTOR) over 180°.
    When a red sticker is detected, it aligns and drops the sandbag.
    If a blue sticker is detected, it performs an avoidance maneuver.
    """
    global fires_extinguished, target_angle
    print("Fire scanning started... Looking for red or blue stickers.")
    while fires_extinguished < 2 and not stop_signal:
        for angle in range(-90, 91, 10):
            if stop_signal:
                break
            rotate_sensor_to_position(angle, speed=50)
            time.sleep(0.2)
            color_val = COLOR_SENSOR.get_value()
            if color_val == 5:  # Red detected
                print(f"Red sticker detected at angle {angle}°.")
                target_angle = angle
                rotate_sensor_to_position(0, speed=50)
                time.sleep(0.2)
                drop_sandbag_with_alignment(target_angle)
                fires_extinguished += 1
                break  # Resume sweeping after handling one detection
            elif color_val == 2:  # Blue detected
                print(f"Blue sticker detected at angle {angle}°.")
                avoid_blue_sticker(angle)
                rotate_sensor_to_position(0, speed=50)
                time.sleep(0.2)
                break
        time.sleep(0.2)
    print("Required fires extinguished. Stopping fire scan.")

def fire_suppression_test():
    """Starts the fire suppression routine (scanning and extinguishing fires)."""
    scan_and_extinguish_fires()
    print("Fire suppression test completed.")

# ----------------------------
# Emergency and Siren Threads
# ----------------------------
def monitor_emergency_stop():
    """Continuously checks the emergency stop sensor."""
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
    """Plays a siren sound periodically."""
    while not stop_signal:
        siren_sound.play()
        time.sleep(0.5)

# ----------------------------
# Navigation and Approach Functions
# ----------------------------
def navigation_to_fire():
    """
    Navigates the robot using ultrasonic sensors:
    - Drives until the front sensor detects a wall at ~55 cm,
    - Turns right 90°,
    - Drives until a wall is detected at ~30 cm,
    - Turns left 90°.
    """
    print("Navigation to fire started.")
    # Step 1: Approach first wall
    while not stop_signal:
        drive_forward_with_correction(power=-20, duration=0.4)
        front_distance = ULTRASONIC_SENSOR.get_cm()
        if front_distance is not None and front_distance <= 55:
            print(f"Front wall detected at {front_distance} cm.")
            break
    # Step 2: Turn right 90°
    turn_right_90()
    # Step 3: Approach second wall
    while not stop_signal:
        drive_forward_with_correction(power=-20, duration=0.4)
        front_distance = ULTRASONIC_SENSOR.get_cm()
        if front_distance is not None and front_distance <= 30:
            print(f"Wall detected at {front_distance} cm.")
            break
    # Step 4: Turn left 90°
    turn_left_90()
    print("Final left turn completed. Ready to approach fire.")

def approach_fire():
    """
    Drives the robot forward until the color sensor detects red,
    confirming the room on fire.
    """
    print("Approaching fire: moving forward until red is detected.")
    while not stop_signal:
        drive_forward_with_correction(power=-20, duration=0.4)
        color_val = COLOR_SENSOR.get_value()
        if color_val == 5:  # Red detected
            print("Red color detected. Room on fire confirmed.")
            break

# ----------------------------
# Main Execution
# ----------------------------
if __name__ == "__main__":
    wait_ready_sensors(True)
    print("Firefighter Robot System Initialized.")
    
    # Start emergency and siren threads (they run throughout the operation)
    emergency_thread = threading.Thread(target=monitor_emergency_stop)
    siren_thread = threading.Thread(target=play_siren)
    emergency_thread.start()
    siren_thread.start()
    
    # Navigation phase: move toward the fire area
    navigation_to_fire()
    
    # Approach phase: drive forward until red is detected
    approach_fire()
    
    # Fire suppression phase: begin scanning and extinguishing fires
    fire_suppression_test()
    
    # Signal stop and wait for threads to finish
    stop_signal = True
    emergency_thread.join()
    siren_thread.join()
    print("System shut down.")
