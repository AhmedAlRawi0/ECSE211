#!/usr/bin/env python3
"""
Firefighter Rescue Robot Implementation

Requirements:
- Starts at base (bottom left of a 5x5 grid).
- Mission must complete within 3 minutes.
- Autonomously navigates; avoids obstacles and walls.
- Only enters the fire room (identified by an orange threshold).
- Plays a fire truck siren until entering the fire room.
- Extinguishes at least 2 fires (detected as red stickers) by dropping a sandbag.
- Returns to base after the mission.
- Has an emergency stop button (touch sensor) that halts all operations.
"""

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

stop_signal = False           # Set when emergency stop is pressed
in_fire_room = False          # Indicates when robot has reached the fire room
fires_extinguished = 0        # Count of extinguished fires

# TBC w/ roy
EMERGENCY_STOP = TouchSensor(4)  
# Color sensor used for grid navigation, fire detection and room entrance detection.
# Using "id" mode returns a numeric code (see: Black=1, Yellow=4, Red=5, Orange=?) from Google
COLOR_SENSOR = EV3ColorSensor(2, mode="id")
# Ultrasonic sensor used for wall detection (returns distance in centimeters)
ULTRASONIC_SENSOR = EV3UltrasonicSensor(1, mode="cm")
# Driving motors (need to check the motor ports from last time)
LEFT_MOTOR = Motor("A")
RIGHT_MOTOR = Motor("B")
# Motor to activate the fire suppression (simulate dropping a sandbag)
FIRE_SUPPRESSION_MOTOR = Motor("D")

siren_sound = Sound(duration=0.5, pitch="C4", volume=100)

# ----------------------------
# Helper Functions for Driving
# ----------------------------
def drive_forward(power=20, duration=0.5): # we can change this
    """Drive both motors forward for a specified duration."""
    if stop_signal:
        return
    LEFT_MOTOR.set_power(power)
    RIGHT_MOTOR.set_power(power)
    time.sleep(duration)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

def turn_right_90():
    """Perform an approximate 90° right turn using differential drive."""
    if stop_signal:
        return
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(-50)
    time.sleep(0.8)  # we can change this
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

def turn_left_90():
    """Perform an approximate 90° left turn using differential drive."""
    if stop_signal:
        return
    LEFT_MOTOR.set_power(-50)
    RIGHT_MOTOR.set_power(0)
    time.sleep(0.8)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

# ----------------------------
# Siren Playback (Threaded)
# ----------------------------
def play_siren():
    """
    Continuously play the siren until the robot enters the fire room.
    The loop will stop once 'in_fire_room' becomes True.
    """
    while not stop_signal and not in_fire_room:
        siren_sound.play()
        time.sleep(0.5)  # Re-trigger sound periodically

# ----------------------------
# Emergency Stop Monitor (Threaded)
# ----------------------------
def monitor_emergency_stop():
    """Continuously check the emergency stop sensor."""
    global stop_signal
    while not stop_signal:
        if EMERGENCY_STOP.is_pressed():
            print("Emergency Stop Activated!")
            stop_signal = True
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            FIRE_SUPPRESSION_MOTOR.set_power(0)
            reset_brick()  # Reset sensors and actuators
            break
        time.sleep(0.1)

# ----------------------------
# Navigation: Moving to the Fire Room
# ----------------------------
def navigate_to_fire_room():
    """
    I have written this in more of a sequential manner as it's extremely difficult to do it in a dynamic way, this is my max lol
    Navigate from the base to the fire room using the following steps:
      1. Drive forward until three black grid lines are detected OR ultrasonic sensor reads 55ish cm from wall (to be checked, I just picked the number based 
      on pure guesses)
      2. Turn right 90°.
      3. Drive forward until four more black lines are detected OR ultrasonic sensor indicates a 30ish cm distance
      4. Turn left 90°.
      5. Drive forward until the color sensor detects the fire room entrance (orange threshold, I need to test this honestly because I followed a tutorial 
      on how to do it using the modre=id).
    """
    global in_fire_room
    # Step 1: Move forward while counting black grid lines (black = code 1)
    black_lines = 0
    while black_lines < 3 and not stop_signal: #! I can comment this out if we decide to go with the ditanace sensor
        drive_forward(power=50, duration=0.5)
        color_val = COLOR_SENSOR.get_value() #! we might need to find another approach if this does not work (usnig rgb values probs or refer to lab 2)
        if color_val == 1:
            black_lines += 1
            print(f"Detected black line {black_lines}")
            time.sleep(0.3)  # debounce to avoid multiple counts
        # Also check if the ultrasonic sensor reads 55 cm or more (wall reached)
        distance = ULTRASONIC_SENSOR.get_cm()
        if distance is not None and distance >= 55:
            print("Reached 55 cm from wall")
            break

    # Step 2: Turn right 90°
    turn_right_90()

    # Step 3: Move forward until four black lines are counted OR until ultrasonic sensor reads 30ish cm
    black_lines = 0
    while black_lines < 4 and not stop_signal:
        drive_forward(power=50, duration=0.5)
        color_val = COLOR_SENSOR.get_value()
        if color_val == 1: #! I can comment this out if we decide to go with the ditanace sensor
            black_lines += 1
            print(f"Detected black line during second leg: {black_lines}")
            time.sleep(0.3)
        distance = ULTRASONIC_SENSOR.get_cm()
        if distance is not None and distance <= 30:
            print("Ultrasonic sensor indicates 30 cm from wall")
            break

    # Step 4: Turn left 90° to enter the fire room...
    turn_left_90()

    # Step 5: Drive forward until the fire room entrance is detected (orange = code 7) ughhhhhhh, we need to test this
    while not stop_signal:
        drive_forward(power=50, duration=0.5)
        color_val = COLOR_SENSOR.get_value()
        if color_val == 7:
            print("Detected fire room entrance (orange).")
            break
        time.sleep(0.1)
    in_fire_room = True  # Signal that the fire room has been reached

# ----------------------------
# Fire Detection & Extinguishing
# ----------------------------
def scan_and_extinguish_fires():
    """
    this is just an inital stupid idea, we need to test this and see how it works, i genuinly A
    In the fire room, continuously scan for red stickers (fire, red = code 5).
    When fire is detected:
      - Stop movement.
      - Activate the fire suppression mechanism (drop sandbag).
      - Increment the count of extinguished fires.
    Continue scanning until at least 2 fires are extinguished.
    """
    global fires_extinguished
    while fires_extinguished < 2 and not stop_signal:
        color_val = COLOR_SENSOR.get_value()
        if color_val == 5:
            print("Fire detected! Initiating suppression.")
            # Stop any movement before deploying suppression
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            drop_sandbag()
            fires_extinguished += 1
            print(f"Fires extinguished: {fires_extinguished}")
            time.sleep(1)  # pause after extinguishing a fire
        else:
            time.sleep(0.2)
    print("Required fires have been extinguished.")

def drop_sandbag():
    """
    Simulate dropping the sandbag by running the suppression motor.
    Even if the bag bounces away, it is considered valid.
    """
    print("Dropping sandbag on fire...")
    FIRE_SUPPRESSION_MOTOR.set_power(50)
    time.sleep(1)  # time to drop the sandbag
    FIRE_SUPPRESSION_MOTOR.set_power(0)
    print("Sandbag deployed.")

# ----------------------------
# Return-to-Base Navigation
# ----------------------------
def return_to_base():
    """
    After extinguishing fires, navigate back to base:
      1. Reverse until the orange threshold (exit) is detected.
      2. Turn right 90°.
      3. Drive forward until the ultrasonic sensor detects a wall (within 30 cm).
      4. Turn left 90°.
      5. Drive a pre-determined distance to reach base.
    """
    global in_fire_room
    in_fire_room = False  # Leaving the fire room

    # Step 1: Reverse until exit (orange threshold) is detected.
    while not stop_signal:
        LEFT_MOTOR.set_power(-50)
        RIGHT_MOTOR.set_power(-50)
        color_val = COLOR_SENSOR.get_value()
        if color_val == 7: # again, testing is required to verify our sensors actually return such a number
            print("Detected exit (orange threshold).")
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            break
        time.sleep(0.5)

    # Step 2: Turn right 90°.
    turn_right_90()

    # Step 3: Drive forward until the ultrasonic sensor indicates proximity to a wall.
    while not stop_signal:
        drive_forward(power=50, duration=0.5)
        distance = ULTRASONIC_SENSOR.get_cm()
        if distance is not None and distance <= 30:
            print("Wall detected on return path.")
            break
        time.sleep(0.1)

    # Step 4: Turn left 90°.
    turn_left_90()

    # Step 5: Drive forward a set distance to return to base.
    drive_forward(power=50, duration=2.0)  # Adjust duration as needed
    print("Robot has returned to base.")

# ----------------------------
# Main Mission Sequence
# ----------------------------
def main_mission():
    global stop_signal
    mission_start = time.time()

    # Start the siren (runs until the fire room is reached)
    siren_thread = threading.Thread(target=play_siren)
    siren_thread.start()

    # Navigate from base to the fire room
    navigate_to_fire_room()
    print("Fire room reached. Stopping siren.")

    # Scan for and extinguish fires until at least 2 fires are put out
    scan_and_extinguish_fires()

    # Return to base following the specified path
    return_to_base()
    print("Mission completed. Robot returned to base.")

    # Check total mission time
    total_time = time.time() - mission_start
    if total_time > 180:
        print("Warning: Mission time exceeded 3 minutes.")
    else:
        print(f"Mission time: {total_time:.2f} seconds.")

# ----------------------------
# Main Execution
# ----------------------------
if __name__ == "__main__":
    wait_ready_sensors(True)
    print("Firefighter Rescue Robot Initialized.")
    print("Starting mission...")

    # Start emergency stop monitor thread
    emergency_thread = threading.Thread(target=monitor_emergency_stop)
    emergency_thread.start()

    # Run the main mission sequence
    main_mission()

    # Wait for the emergency stop thread to finish (if not already)
    emergency_thread.join()
    print("System shut down.")
