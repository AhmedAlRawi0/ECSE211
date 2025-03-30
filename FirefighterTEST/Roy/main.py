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

# ----------------------------
# Helper Functions
# ----------------------------
def drive_forward_with_correction(power=-20, duration=0.5, Ldist=None, Fdist = 100, tolerance=0.3, correction_offset=5):
    if stop_signal:
        return
    # If Ldist is not provided, set it to the first sensor reading
    if Ldist is None:
        Ldist = ULTRASONIC_SENSOR_LEFT.get_cm()
    print(f"[DEBUG] Starting drive_forward_with_correction: Target Fdist = {Fdist} cm, Ldist = {Ldist} cm")

    while not stop_signal:
        # Check front distance
        front_distance = ULTRASONIC_SENSOR.get_cm()
        print(f"[DEBUG] Front sensor reading: {front_distance} cm")
        if front_distance is not None and front_distance <= Fdist:
            print(f"[DEBUG] Target front distance reached: {front_distance} cm")
            break

        distance_left = ULTRASONIC_SENSOR_LEFT.get_cm()
        print(f"Left distance is {distance_left}")

        if distance_left > Ldist + tolerance:
            LEFT_MOTOR.set_power(power)
            RIGHT_MOTOR.set_power(power - correction_offset)
            correction = "left"

        elif distance_left < Ldist - tolerance:
            LEFT_MOTOR.set_power(power - correction_offset)
            RIGHT_MOTOR.set_power(power)
            correction = "right"

        else:
            LEFT_MOTOR.set_power(power)
            RIGHT_MOTOR.set_power(power)
            correction = "straight"

        print(f"[DEBUG] Correction applied: {correction} (Left Distance: {distance_left} cm)")
        time.sleep(0.0001)
        LEFT_MOTOR.set_power(0)
        RIGHT_MOTOR.set_power(0)
        time.sleep(0.0001)

def drive_forward_straight(angle): #shit
    
    # Convert the desired forward rotation to a negative target encoder value.
    target = -abs(angle)
    
    # Reset encoders
    LEFT_MOTOR.reset_encoder()
    RIGHT_MOTOR.reset_encoder()
    
    # Set initial power levels (tweak these as needed)
    left_power = -30
    right_power = -30
    LEFT_MOTOR.set_power(left_power)
    RIGHT_MOTOR.set_power(right_power)
    
    # Drive until both wheels reach the target position within a small threshold.
    while True:
        left_enc = LEFT_MOTOR.get_encoder()
        right_enc = RIGHT_MOTOR.get_encoder()
        if abs(left_enc - target) < 10 and abs(right_enc - target) < 10:
            break
        
        # Calculate the difference between encoder readings to correct drift.
        diff = left_enc - right_enc
        correction = 0.1 * diff  # Adjust this factor as necessary
        
        # Adjust power levels based on the difference.
        adjusted_left_power = left_power - correction
        adjusted_right_power = right_power + correction
        
        LEFT_MOTOR.set_power(adjusted_left_power)
        RIGHT_MOTOR.set_power(adjusted_right_power)
        
        time.sleep(0.01)
    
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print(f"Drive forward complete: {angle}° rotation achieved with straight correction.")


    
def turn_right_90():
    if stop_signal:
        return
    LEFT_MOTOR.set_power(-50)
    RIGHT_MOTOR.set_power(0)
    time.sleep(1.1)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

def turn_left_90():
    if stop_signal:
        return
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(-50)
    time.sleep(1.1)
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

    if 30 <= angle <= 80:
        print(f"Aligning robot using sensor angle: {angle}°")
        FIRE_SUPPRESSION_MOTOR.set_power(60)
        time.sleep(0.1)
        FIRE_SUPPRESSION_MOTOR.set_power(-60)
        time.sleep(0.1)
        FIRE_SUPPRESSION_MOTOR.set_power(0)
        time.sleep(0.1)
        print("Sandbag deployed with no change in angle.")
    
    elif angle < 30:
        print(f"Angle {angle}° less than 30°: Rotating -25° (right) before dropping sandbag.")
        rotate_robot(-25)
        FIRE_SUPPRESSION_MOTOR.set_power(60)
        time.sleep(0.1)
        FIRE_SUPPRESSION_MOTOR.set_power(-60)
        time.sleep(0.1)
        FIRE_SUPPRESSION_MOTOR.set_power(0)
        print("Sandbag deployed.")
        time.sleep(0.3)
        rotate_robot(25)

    elif angle > 80:
        print(f"Angle {angle}° greater than 80°: Rotating 45° (left) before dropping sandbag.")
        rotate_robot(25)
        FIRE_SUPPRESSION_MOTOR.set_power(60)
        time.sleep(0.1)
        FIRE_SUPPRESSION_MOTOR.set_power(-60)
        time.sleep(0.1)
        FIRE_SUPPRESSION_MOTOR.set_power(0)
        print("Sandbag deployed.")
        time.sleep(0.3)
        rotate_robot(-25)

def avoid_green_sticker(angle):
    print(f"[DEBUG] Green sticker detected at angle {angle}°. Initiating avoidance maneuver...")
    # Initial forward bump to clear the sticker area
    LEFT_MOTOR.set_power(30)
    RIGHT_MOTOR.set_power(30)
    time.sleep(0.80)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print("[DEBUG] Completed initial backward bump; robot stopped.")

    # Decide rotation direction based on detected angle
    if angle >= 60:
        print(f"[DEBUG] Angle {angle}° >= 70, rotating robot right by 45°.")
        rotate_robot(-90)
        turn_angle = -90
    elif angle < 60:
        print(f"[DEBUG] Angle {angle}° < 70, rotating robot left by 45°.")
        rotate_robot(90)
        turn_angle = 90
    
    print("[DEBUG] Avoidance maneuver complete.")

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
    while not siren_stop and not stop_signal:
        siren_sound.play()
        time.sleep(0.5)

# ----------------------------
# Navigation Sequence
# ----------------------------
def navigate_to_fire_room():
    print("Navigation to fire room started...")
    # Drive forward until the front sensor detects a wall at 57 cm
    drive_forward_with_correction(power=-20, duration=0.5, Ldist=8, Fdist=57)
    time.sleep(0.2)
    turn_right_90()
    print("Turned right 90°.") 

    # Drive forward until the front sensor detects a wall at 33 cm
    drive_forward_with_correction(power=-20, duration=0.4, Ldist=55, Fdist=33)
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
    # Reset the encoder for the color sensor motor to set the initial position to 0°
    COLOUR_MOTOR.reset_encoder()
    # Rotate sensor to initial position (0°)
    rotate_sensor_to_position(0, speed=50)
    
    while fires_extinguished < 2 and not stop_signal:
        for angle in range(0, 132, 10):
            if stop_signal:
                break
            rotate_sensor_to_position(angle, speed=25)
            time.sleep(0.03)
            color_val = COLOUR_SENSOR.get_value()

            if color_val == 5:
                print(f"Red detected at {angle}°")
                rotate_sensor_to_position(100, speed=50)
                time.sleep(0.1)
                drop_sandbag_with_alignment(angle)
                fires_extinguished += 1
                break
            elif color_val == 1:
                print(f"Green detected at {angle}°")
                rotate_sensor_to_position(0, speed=50)
                avoid_green_sticker(angle)
                time.sleep(0.2)
                break
        time.sleep(0.2)
    print("All required fires extinguished.")


def navigate_inside_fire_room():
    print("Navigation inside fire room started...")
    # Drive forward until the front sensor reads 8 cm (with left sensor target at 81 cm)
    drive_forward_with_correction(power=-20, duration=0.5, Ldist=81, Fdist=8)
    time.sleep(0.2)
    turn_left_90()
    print("Turned left 90°.")
    # Drive forward until the front sensor reads 57 cm (with left sensor target at 110 cm)

    drive_forward_with_correction(power=-20, duration=0.4, Ldist=110, Fdist=57)
    time.sleep(0.2)
    turn_left_90()
    print("Turned left 90°.")
    print("Navigation inside fire room complete.")

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

    print("Arrived at fire room. Stopping siren.")
    siren_stop = True
    siren_thread.join()
    print("Siren stopped.")
    
    scan_thread = threading.Thread(target=scan_and_extinguish_fires)
    navigation_thread = threading.Thread(target=navigate_inside_fire_room)
    scan_thread.start()
    navigation_thread.start()

    scan_thread.join()
    navigation_thread.join()

    # Signal emergency thread to stop and finish the mission
    stop_signal = True
    emergency_thread.join()
    print("Mission completed.")

if __name__ == "__main__":
    wait_ready_sensors(True)
    print("Firefighter Robot Full Mission Starting...")
    main_mission()
    print("System shut down.")