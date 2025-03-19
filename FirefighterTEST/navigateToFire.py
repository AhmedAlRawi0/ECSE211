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

# Emergency stop button
EMERGENCY_STOP = TouchSensor(4)
# Ultrasonic sensor for distance detection
ULTRASONIC_SENSOR = EV3UltrasonicSensor(1, mode="cm")
# Driving motors
LEFT_MOTOR = Motor("A")
RIGHT_MOTOR = Motor("B")
# Siren sound
siren_sound = Sound(duration=0.5, pitch="C4", volume=100)

# ----------------------------
# Helper Functions for Driving
# ----------------------------
def drive_forward(power=-20, duration=0.5):
    """Drive both motors forward for a specified duration."""
    if stop_signal:
        return
    LEFT_MOTOR.set_power(power)
    RIGHT_MOTOR.set_power(power)
    time.sleep(duration)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

def turn_right_90():
    """Turn right approximately 90°."""
    if stop_signal:
        return
    LEFT_MOTOR.set_power(-50)
    RIGHT_MOTOR.set_power(0)
    time.sleep(0.8)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

def turn_left_90():
    """Turn left approximately 90°."""
    if stop_signal:
        return
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(-50)
    time.sleep(0.8)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

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
            reset_brick()
            break
        time.sleep(0.1)

# ----------------------------
# Siren Playback (Threaded)
# ----------------------------
def play_siren():
    """Play siren until stop_signal is activated."""
    while not stop_signal:
        siren_sound.play()
        time.sleep(0.5)  # Re-trigger sound periodically

# ----------------------------
# Test Sequence
# ----------------------------
def subsystem_test():
    """Test subsystems in a controlled sequence."""
    global stop_signal

    # Start emergency stop monitor in a separate thread
    emergency_thread = threading.Thread(target=monitor_emergency_stop)
    emergency_thread.start()

    # Start siren in a separate thread
    siren_thread = threading.Thread(target=play_siren)
    siren_thread.start()

    print("Subsystem Test Started.")

    # Step 1: Drive forward until ultrasonic sensor reads 55 cm
    while not stop_signal:
        drive_forward(power=-20, duration=0.5)
        distance = ULTRASONIC_SENSOR.get_cm()
        if distance is not None and distance <= 55:
            print(f"Wall detected at {distance} cm. Stopping.")
            break
        time.sleep(0.1)

    # Step 2: Turn right 90°
    turn_right_90()
    print("Turned right 90°.")

    # Step 3: Drive forward until ultrasonic sensor reads 30 cm
    while not stop_signal:
        drive_forward(power=-20, duration=0.5)
        distance = ULTRASONIC_SENSOR.get_cm()
        if distance is not None and distance <= 30:
            print(f"Wall detected at {distance} cm. Stopping.")
            break
        time.sleep(0.1)

    # Step 4: Turn left 90°
    turn_left_90()
    print("Turned left 90°.")

    # Stop siren after the test
    #global stop_signal
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
