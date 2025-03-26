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

# ----------------------------
# Global Variables
# ----------------------------
stop_signal = False
fires_extinguished = 0

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

# ----------------------------
# Helper Functions
# ----------------------------
def drive_forward_with_correction(power=-20, duration=0.5, Ldist=5):
    if stop_signal:
        return
    distance_left = ULTRASONIC_SENSOR_LEFT.get_cm()
    correction = "unknown"

    if distance_left is not None:
        if distance_left > Ldist + 0.5:
            LEFT_MOTOR.set_power(power)
            RIGHT_MOTOR.set_power(power - 5)
            correction = "left"
        elif distance_left < Ldist - 0.5:
            LEFT_MOTOR.set_power(power - 5)
            RIGHT_MOTOR.set_power(power)
            correction = "right"
        else:
            LEFT_MOTOR.set_power(power)
            RIGHT_MOTOR.set_power(power)
            correction = "straight"
    else:
        LEFT_MOTOR.set_power(power)
        RIGHT_MOTOR.set_power(power)

    time.sleep(duration)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print(f"Correction applied: {correction} (Left Distance: {distance_left})")

def turn_right_90():
    if stop_signal:
        return
    LEFT_MOTOR.set_power(-50)
    RIGHT_MOTOR.set_power(0)
    time.sleep(1.3)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

def turn_left_90():
    if stop_signal:
        return
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(-50)
    time.sleep(1.3)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

def rotate_sensor_to_position(target, speed, threshold=2):
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
    rotation_time = abs(angle) / 90.0
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
    print(f"Aligning robot using sensor angle: {angle}°")
    FIRE_SUPPRESSION_MOTOR.set_power(40)
    time.sleep(0.1)
    FIRE_SUPPRESSION_MOTOR.set_power(-40)
    time.sleep(0.1)
    FIRE_SUPPRESSION_MOTOR.set_power(0)
    print("Sandbag deployed.")
    rotate_robot(-angle)

def avoid_blue_sticker(angle):
    print(f"Blue sticker detected at angle {angle}°. Avoiding...")
    LEFT_MOTOR.set_power(-20)
    RIGHT_MOTOR.set_power(-20)
    time.sleep(0.5)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    if angle > 0:
        rotate_robot(-45)
    else:
        rotate_robot(45)
    print("Avoidance complete.")

# ----------------------------
# Threads
# ----------------------------
def monitor_emergency_stop():
    global stop_signal
    while not stop_signal:
        if EMERGENCY_STOP.is_pressed():
            print("Emergency Stop Activated!")
            stop_signal = True
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            FIRE_SUPPRESSION_MOTOR.set_power(0)
            reset_brick()
            break
        time.sleep(0.1)

def play_siren():
    while not stop_signal:
        siren_sound.play()
        time.sleep(0.5)

# ----------------------------
# Navigation Sequence
# ----------------------------
def navigate_to_fire_room():
    print("Navigation started...")
    while not stop_signal:
        drive_forward_with_correction(power=-20, duration=0.5, Ldist=8)
        front_distance = ULTRASONIC_SENSOR.get_cm()
        if front_distance is not None and front_distance <= 57:
            print(f"Wall detected at {front_distance} cm.")
            break

    time.sleep(0.2)
    turn_right_90()
    print("Turned right 90°.")

    while not stop_signal:
        drive_forward_with_correction(power=-20, duration=0.4, Ldist=55)
        front_distance = ULTRASONIC_SENSOR.get_cm()
        if front_distance is not None and front_distance <= 33:
            print(f"Wall detected at {front_distance} cm.")
            break

    time.sleep(0.2)
    turn_left_90()
    print("Turned left 90°.")
    print("Arrived at fire room.")

# ----------------------------
# Fire Detection
# ----------------------------
def scan_and_extinguish_fires():
    global fires_extinguished
    print("Fire scanning started...")
    while fires_extinguished < 2 and not stop_signal:
        for angle in range(-180, -40, 10):
            if stop_signal:
                break
            rotate_sensor_to_position(angle, speed=25)
            time.sleep(0.05)
            color_val = COLOUR_SENSOR.get_value()

            if color_val == 5:
                print(f"Red detected at {angle}°")
                rotate_sensor_to_position(-50, speed=50)
                time.sleep(0.1)
                drop_sandbag_with_alignment(angle)
                fires_extinguished += 1
                break
            elif color_val == 6:
                print(f"Blue detected at {angle}°")
                avoid_blue_sticker(angle)
                rotate_sensor_to_position(0, speed=50)
                time.sleep(0.2)
                break
        time.sleep(0.2)
    print("All required fires extinguished.")

# ----------------------------
# Main Execution
# ----------------------------
def main_mission():
    global stop_signal
    emergency_thread = threading.Thread(target=monitor_emergency_stop)
    siren_thread = threading.Thread(target=play_siren)
    emergency_thread.start()
    siren_thread.start()

    navigate_to_fire_room()
    stop_signal = stop_signal or False  # Stop siren once in fire room
    print("Stopping siren.")
    scan_and_extinguish_fires()

    stop_signal = True
    emergency_thread.join()
    siren_thread.join()
    print("Mission completed.")

if __name__ == "__main__":
    wait_ready_sensors(True)
    print("Firefighter Robot Full Mission Starting...")
    main_mission()
    print("System shut down.")