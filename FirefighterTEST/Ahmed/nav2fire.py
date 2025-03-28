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
TARGET_LEFT_DISTANCE = 8  # we can adjust this, i am just guessing

# ----------------------------
# Helper Functions
# ----------------------------
def drive_forward_with_correction(power=-20, duration=0.5, Ldist=5): 
    """Drive forward while correcting drift using the left ultrasonic sensor."""
    if stop_signal:
        return
    distance_left = ULTRASONIC_SENSOR_LEFT.get_cm()
    correction = 0

    if distance_left is not None:
        if distance_left > Ldist + 0.5: # we can change the margin.
            # Too far from wall — slant left
            LEFT_MOTOR.set_power(power)
            RIGHT_MOTOR.set_power(power-5)
            correction = "left"
        elif distance_left < Ldist - 0.5:
            # Too close to wall — slant right
            LEFT_MOTOR.set_power(power-5)
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
    """Turn right approximately 90°."""
    if stop_signal:
        return
    LEFT_MOTOR.set_power(-50)
    RIGHT_MOTOR.set_power(0)
    time.sleep(1.3)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

def turn_left_90():
    """Turn left approximately 90°."""
    if stop_signal:
        return
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(-50)
    time.sleep(1.3)
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
        drive_forward_with_correction(power=-20, duration=0.5, Ldist=8) #we can change here
        front_distance = ULTRASONIC_SENSOR.get_cm()
        if front_distance is not None and front_distance <= 57:
            print(f"Front wall detected at {front_distance} cm.")
            break

    # Step 2: Turn right 90°
    time.sleep(0.2)
    turn_right_90()
    print("Turned right 90°.")

    # Step 3: Drive until 30 cm from next wall
    while not stop_signal:
        drive_forward_with_correction(power=-20, duration=0.4, Ldist=55)
        front_distance = ULTRASONIC_SENSOR.get_cm()
        if front_distance is not None and front_distance <= 33:
            print(f"Wall detected at {front_distance} cm.")
            break

    # Step 4: Turn left 90°
    time.sleep(0.2)
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
