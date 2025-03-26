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

# Sensors & Motors
EMERGENCY_STOP = TouchSensor(4)
ULTRASONIC_SENSOR = EV3UltrasonicSensor(3, mode="cm")         # Front-facing, need to confirm in case it's different
ULTRASONIC_SENSOR_LEFT = EV3UltrasonicSensor(1, mode="cm")    # Left-facing (new), need to confirm in case it's different
COLOUR_SENSOR = EV3ColorSensor(2)
LEFT_MOTOR = Motor("A")
RIGHT_MOTOR = Motor("B")
COLOUR_MOTOR = Motor("C")  # I still need to figure smt for the rotating color motor
siren_sound = Sound(duration=0.5, pitch="C4", volume=100)

# Calibration constant (roy idea)
TARGET_LEFT_DISTANCE = 2.5  # we can adjust this, i am just guessing

# ----------------------------
# Helper Functions
# ----------------------------
def drive_forward_with_correction(power=-20, duration=0.5): 
    """Drive forward while correcting drift using the left ultrasonic sensor."""
    if stop_signal:
        return
    distance_left = ULTRASONIC_SENSOR_LEFT.get_cm()
    correction = 0

    if distance_left is not None:
        if distance_left > TARGET_LEFT_DISTANCE + 1: # we can change the margin.
            # Too far from wall — slant left
            LEFT_MOTOR.set_power(power)
            RIGHT_MOTOR.set_power(power+5)
            correction = "left"
        elif distance_left < TARGET_LEFT_DISTANCE - 1:
            # Too close to wall — slant right
            LEFT_MOTOR.set_power(power+5)
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

# based on tutorials, we need to check this
# Constants based on your robot's physical configuration
RW = 0.021  # Wheel radius in meters (2.1 cm)
RB = 0.068   # Distance between wheels (wheelbase) in meters (6.8 cm)
ORIENTTODEG = RB / RW  # Scaling factor for rotation

def turn_right_90():
    """Accurate 90° right turn using motor encoders and sleep estimation."""
    if stop_signal:
        return

    angle = 90
    motor_degrees = int(angle * ORIENTTODEG)
    degrees_per_second = 180  # You can tune this value
    estimated_time = abs(motor_degrees) / degrees_per_second

    print(f"Turning right 90° using {motor_degrees} motor degrees, sleeping for {estimated_time:.2f}s")

    LEFT_MOTOR.set_position_relative(motor_degrees)
    RIGHT_MOTOR.set_position_relative(-motor_degrees)
    time.sleep(estimated_time)

    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)


def turn_left_90():
    """Accurate 90° left turn using motor encoders and sleep estimation."""
    if stop_signal:
        return

    angle = 90
    motor_degrees = int(angle * ORIENTTODEG)
    degrees_per_second = 180
    estimated_time = abs(motor_degrees) / degrees_per_second

    print(f"Turning left 90° using {motor_degrees} motor degrees, sleeping for {estimated_time:.2f}s")

    LEFT_MOTOR.set_position_relative(-motor_degrees)
    RIGHT_MOTOR.set_position_relative(motor_degrees)
    time.sleep(estimated_time)

    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)


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

    # Threads
    emergency_thread = threading.Thread(target=monitor_emergency_stop)
    siren_thread = threading.Thread(target=play_siren)
    emergency_thread.start()
    siren_thread.start()

    print("Subsystem Test Started.")

    # Step 1: Drive until 55 cm from wall
    while not stop_signal:
        drive_forward_with_correction(power=-20, duration=0.4) #we can change here
        front_distance = ULTRASONIC_SENSOR.get_cm()
        if front_distance is not None and front_distance <= 55:
            print(f"Front wall detected at {front_distance} cm.")
            break

    # Step 2: Turn right 90°
    turn_right_90()
    print("Turned right 90°.")

    # Step 3: Drive until 30 cm from next wall
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
# Main
# ----------------------------
if __name__ == "__main__":
    wait_ready_sensors(True)
    print("Firefighter Robot Subsystem Test Initialized.")
    subsystem_test()
    print("System shut down.")
