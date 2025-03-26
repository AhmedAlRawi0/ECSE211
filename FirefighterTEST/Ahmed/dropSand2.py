import threading
import time
from utils.brick import (
    TouchSensor,
    EV3ColorSensor,
    Motor,
    wait_ready_sensors,
    reset_brick,
)

# Global Variables
stop_signal = False
fires_extinguished = 0  # Number of fires extinguished
target_angle = 0        # Angle where a red sticker was detected

# Sensors & Motors, need to confirm the ports
EMERGENCY_STOP = TouchSensor(4)            # Emergency stop button
COLOR_SENSOR = EV3ColorSensor(2, mode="id")  # Color sensor for fire detection
FIRE_SUPPRESSION_MOTOR = Motor("D")          # Motor to drop sandbag
COLOUR_MOTOR = Motor("C")                    # Rotating motor for the color sensor

# Drive Motors for aligning the robot (assumed ports)
LEFT_DRIVE = Motor("A")
RIGHT_DRIVE = Motor("B")

# ----------------------------
# Helper Function: Rotate Sensor to Position
# ----------------------------
def rotate_sensor_to_position(target, speed, threshold=2):
    """
    Rotates the color sensor motor to the given absolute position.
    Uses feedback from get_position() to stop within a threshold.
    """
    current = COLOUR_MOTOR.get_position()
    while abs(current - target) > threshold and not stop_signal:
        # Determine direction
        if current < target:
            COLOUR_MOTOR.set_power(speed)
        else:
            COLOUR_MOTOR.set_power(-speed)
        time.sleep(0.02)  # Short delay for responsiveness
        current = COLOUR_MOTOR.get_position()
    COLOUR_MOTOR.set_power(0)
    # Ensure final position is set (could add correction logic here if needed)
    print(f"Sensor rotated to target angle {target}° (current: {current}°).")

# ----------------------------
# Emergency Stop Monitor (Threaded)
# ----------------------------
def monitor_emergency_stop():
    """Continuously check the emergency stop sensor."""
    global stop_signal
    while not stop_signal:
        if EMERGENCY_STOP.is_pressed():
            print("Emergency Stop Activated! Halting all operations.")
            stop_signal = True
            FIRE_SUPPRESSION_MOTOR.set_power(0)
            reset_brick()  # Reset sensors and actuators
            break
        time.sleep(0.1)

# ----------------------------
# Helper Function: Rotate Robot
# ----------------------------
def rotate_robot(angle):
    """
    Rotates the robot in place by the specified angle.
    Positive angle rotates right; negative rotates left.
    Assumes a conversion of 90° per second at a given motor power.
    """
    rotation_time = abs(angle) / 90.0  # Adjust conversion factor as needed
    print(f"Rotating robot by {angle}° (estimated {rotation_time:.2f}s).")
    if angle > 0:
        # To rotate right: left motor forward, right motor backward.
        LEFT_DRIVE.set_power(30)
        RIGHT_DRIVE.set_power(-30)
    elif angle < 0:
        # To rotate left: left motor backward, right motor forward.
        LEFT_DRIVE.set_power(-30)
        RIGHT_DRIVE.set_power(30)
    time.sleep(rotation_time)
    LEFT_DRIVE.set_power(0)
    RIGHT_DRIVE.set_power(0)
    print("Rotation complete.")

# ----------------------------
# Function: Drop Sandbag with Alignment
# ----------------------------
def drop_sandbag_with_alignment(angle):
    """
    Aligns the robot so that the detected red sticker is straight ahead,
    then drops the sandbag.
    """
    print(f"Aligning robot using sensor angle: {angle}°")
    # Rotate the robot by the sensor offset so that the target is centered.
    #rotate_robot(angle)
    # Optionally, add a sensor feedback loop here for fine tuning
    print("🪣 Dropping sandbag on fire...")
    FIRE_SUPPRESSION_MOTOR.set_power(40)
    time.sleep(0.1)  # Time to drop the sandbag
    FIRE_SUPPRESSION_MOTOR.set_power(-40)
    time.sleep(0.1)
    FIRE_SUPPRESSION_MOTOR.set_power(0)
    print("Sandbag deployed.")
    # Rotate back to original heading if needed
    rotate_robot(-angle)

# ----------------------------
# Function: Avoid Blue Sticker
# ----------------------------
def avoid_blue_sticker(angle):
    """
    Initiates an avoidance maneuver when a blue sticker is detected.
    Uses the detected angle to determine which way to turn.
    """
    print(f"Blue sticker detected at angle {angle}°. Initiating avoidance maneuver.")
    # Back up slightly
    LEFT_DRIVE.set_power(-20)
    RIGHT_DRIVE.set_power(-20)
    time.sleep(0.5)  # Back up duration
    LEFT_DRIVE.set_power(0)
    RIGHT_DRIVE.set_power(0)
    # Turn away from the blue sticker.
    if angle > 0:
        print("Turning left to avoid blue sticker.")
        rotate_robot(-45)  # Turn left by 45° (adjust as needed)
    else:
        print("Turning right to avoid blue sticker.")
        rotate_robot(45)   # Turn right by 45° (adjust as needed)
    print("Avoidance maneuver complete.")

# ----------------------------
# Fire Detection & Extinguishing with Sweeping Color Sensor
# ----------------------------
def scan_and_extinguish_fires():
    """
    Continuously sweeps the color sensor (via COLOUR_MOTOR) over 180°.
    When a red sticker is detected, the sensor returns to 0°,
    and the robot aligns itself (using the detected angle) before dropping the sandbag.
    If a blue sticker is detected, the robot triggers an avoidance maneuver.
    Stops when 2 fires are extinguished or an emergency stop is triggered.
    """
    global fires_extinguished, target_angle

    print("Fire scanning started... Looking for red or blue stickers.")

    while fires_extinguished < 2 and not stop_signal:
        # Sweep sensor from -90° to +90°
        for angle in range(-180, -40, 10):  # Adjust step size as needed
            if stop_signal:
                break
            # Rotate sensor to the specified angle
            rotate_sensor_to_position(angle, speed=25)
            time.sleep(0.05)  # Allow time for sensor stabilization

            color_val = COLOR_SENSOR.get_value()
            # Check for red sticker (fire)
            if color_val == 5:  # Red detected
                print(f"Red sticker detected at angle {angle}°.")
                target_angle = angle
                # Return sensor to the normal (0°) position
                rotate_sensor_to_position(-50, speed=50)
                time.sleep(0.1)
                drop_sandbag_with_alignment(target_angle)
                fires_extinguished += 1
                break  # Exit the sweep loop and resume scanning

            # Check for green sticker
            elif color_val == 6:  # green detected
                print(f"Blue sticker detected at angle {angle}°.")
                avoid_blue_sticker(angle)
                # Optionally return sensor to 0° after avoidance
                rotate_sensor_to_position(0, speed=50)
                time.sleep(0.2)
                break  # Restart the sweep after handling blue sticker

        time.sleep(0.2)  # Pause before starting the next sweep

    print("Required fires extinguished. Stopping fire scan.")

# ----------------------------
# Fire Suppression Test Sequence
# ----------------------------
def fire_suppression_test():
    """Runs the fire detection, suppression, and emergency stop test."""
    global stop_signal

    # Start emergency stop monitoring in a separate thread
    emergency_thread = threading.Thread(target=monitor_emergency_stop)
    emergency_thread.start()

    # Start fire scanning and suppression
    scan_and_extinguish_fires()

    # Stop after fires are extinguished or emergency stop is triggered
    stop_signal = True
    emergency_thread.join()

    print("Fire suppression test completed.")

# ----------------------------
# Main Execution
# ----------------------------
if __name__ == "__main__":
    wait_ready_sensors(True)
    print("Firefighter Robot Fire Suppression Test Initialized.")
    fire_suppression_test()
    print("System shut down.")
