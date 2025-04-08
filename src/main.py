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
from math import *


# Global Variables
stop_signal = False
fires_extinguished = 0
siren_stop = False
in_room = False
fire_detected = False


# Sensors & Motors (Check ports)

EMERGENCY_STOP = TouchSensor(4)
ULTRASONIC_SENSOR = EV3UltrasonicSensor(3, mode="cm")         
ULTRASONIC_SENSOR_LEFT = EV3UltrasonicSensor(1, mode="cm")   
COLOUR_SENSOR = EV3ColorSensor(2, mode="id")                 
LEFT_MOTOR = Motor("A")
RIGHT_MOTOR = Motor("B")
COLOUR_MOTOR = Motor("C")                                     
FIRE_SUPPRESSION_MOTOR = Motor("D")                        
siren_sound = Sound(duration=0.5, pitch="C4", volume=100)

# Constants for movement
WHEEL_SEPARATION_CM = 15 
WHEEL_DIAMETER_CM = 4.2


# Helper Functions

def drive_forward_with_correction(power=-20, Ldist=None, duration=0.5, Fdist=None, tolerance=0.3, correction_offset=5):
    if stop_signal:
        return
    
    if Ldist is None:
        Ldist = ULTRASONIC_SENSOR_LEFT.get_cm()

    if Fdist is None:
        Fdist = ULTRASONIC_SENSOR_LEFT.get_cm()

    print(f"[DEBUG] Starting drive_forward_with_correction: Target Fdist = {Fdist} cm, Ldist = {Ldist} cm")

    while not stop_signal:
        
        front_distance = ULTRASONIC_SENSOR.get_cm()
        print(f"[DEBUG] Front sensor reading: {front_distance} cm")
        if front_distance is not None and front_distance <= Fdist:
            print(f"[DEBUG] Target front distance reached: {front_distance} cm")
            break

        distance_left = ULTRASONIC_SENSOR_LEFT.get_cm()
        print(f"[DEBUG] Left sensor reading: {distance_left} cm")

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

        print(f"[DEBUG] Correction applied: {correction} (Left sensor reading: {distance_left} cm)")

    time.sleep(0.1)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    time.sleep(0.1)

def drive_forward_with_correction_room(power=-10, duration=0.5, Ldist=None, Fdist=None, tolerance=0.3, correction_offset=5):
    global fires_extinguished

    if stop_signal:
        return
    # If Ldist is not provided, set it to the first left sensor reading
    if Ldist is None:
        Ldist = ULTRASONIC_SENSOR_LEFT.get_cm()
    
    if Fdist is None:
        Fdist = ULTRASONIC_SENSOR_LEFT.get_cm()

    print(f"[DEBUG] Starting drive_forward_with_correction_incremental: Target Fdist = {Fdist} cm, Ldist = {Ldist} cm")
    stop = False
    # Record the initial front sensor reading
    
    while not stop_signal and not stop:
        while not stop_signal and not fire_detected:
            
            if fires_extinguished >= 2:
                power = -20    

            front_distance = ULTRASONIC_SENSOR.get_cm()
            print(f"[DEBUG] Front sensor reading: {front_distance} cm")
            
            # If the current front distance is less than or equal to target, stop
            if front_distance is not None and front_distance <= Fdist:
                print(f"[DEBUG] Target front distance reached: {front_distance} cm")
                stop = True
                break
    
            distance_left = ULTRASONIC_SENSOR_LEFT.get_cm()
            print(f"[DEBUG] Left sensor reading: {distance_left} cm")
            
            # Apply correction based on left sensor reading relative to Ldist
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
            
            print(f"[DEBUG] Correction applied: {correction} (Left sensor reading: {distance_left} cm)")
            time.sleep(duration)
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            time.sleep(0.5)

        time.sleep(1)

    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    time.sleep(0.1)
    print("[DEBUG] drive_forward_with_correction_incremental complete.")

    
def turn_right_90():
    if stop_signal:
        return
    LEFT_MOTOR.set_power(-50)
    RIGHT_MOTOR.set_power(0)
    time.sleep(1.1)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print("[DEBUG] Turned right 90°.")

def turn_left_90():
    if stop_signal:
        return
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(-50)
    time.sleep(1.1)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print("[DEBUG] Turned left 90°.")

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
    print(f"[DEBUG] Sensor rotated to target angle {target}° (current: {current}°).")

def rotate_robot(angle):
    if stop_signal:
        return
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
    print("[DEBUG] Rotation complete.")

def drop_sandbag_with_alignment(angle):

    def deploy_sandbag():
        FIRE_SUPPRESSION_MOTOR.set_power(30)
        time.sleep(0.1)
        FIRE_SUPPRESSION_MOTOR.set_power(-30)
        time.sleep(0.1)
        FIRE_SUPPRESSION_MOTOR.set_power(0)
        time.sleep(0.1)
        print("[DEBUG] Sandbag deployed.")

    def movement(duration=0.3):
        LEFT_MOTOR.set_power(-20)
        RIGHT_MOTOR.set_power(-20)
        time.sleep(duration)
        LEFT_MOTOR.set_power(0)
        RIGHT_MOTOR.set_power(0)
        time.sleep(duration)

    if angle <= 30:
        print(f"[DEBUG] Angle {angle}° < 30°: Rotate -30° before deploy.")
        rotate_robot(-30)
        deploy_sandbag()
        rotate_robot(30)

    elif 30 < angle < 60:
        movement()
        print(f"[DEBUG] Angle {angle}° between 30–60°: Rotate -15° before deploy.")
        rotate_robot(-15)
        deploy_sandbag()
        rotate_robot(15)

    elif 60 <= angle <= 80:
        movement()
        print(f"[DEBUG] Angle {angle}° between 60–80°: No rotation.")
        deploy_sandbag()

    elif 80 < angle < 120:
        movement(duration=0.5)
        print(f"[DEBUG] Angle {angle}° between 80–120°: Rotate 15° before deploy.")
        rotate_robot(15)
        deploy_sandbag()
        rotate_robot(-15)

    else:
        print(f"[DEBUG] Angle {angle}° >= 120°: Rotate 30° before deploy.")
        rotate_robot(30)
        deploy_sandbag()
        rotate_robot(-30)

    

def avoid_green_sticker(angle):
    print(f"[DEBUG] Green sticker detected at angle {angle}°. Initiating avoidance maneuver...")
    # Initial forward bump backwards to clear the sticker area
    LEFT_MOTOR.set_power(30)
    RIGHT_MOTOR.set_power(30)
    time.sleep(0.80)
    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)
    print("[DEBUG] Completed initial forward bump; robot stopped.")

    if angle >= 75:
        print(f"[DEBUG] Angle {angle}° >= 75, rotating robot right by 90°.")
        rotate_robot(-90)
        turn_angle = -90
    elif angle < 75:
        print(f"[DEBUG] Angle {angle}° < 75, rotating robot left by 90°.")
        rotate_robot(90)
        turn_angle = 90

    print("[DEBUG] Moving forward with correction after initial turn.")
    drive_forward_with_correction(power=-20, duration=0.5, Ldist=None, Fdist=None)
    
    print(f"[DEBUG] Rotating robot opposite direction by {-turn_angle}°.")
    rotate_robot(-turn_angle)
    
    print("[DEBUG] Moving forward with correction after reorienting.")
    drive_forward_with_correction(power=-20, duration=0.5, Ldist=None, Fdist=None)
    
    print(f"[DEBUG] Rotating robot back by {turn_angle}° to resume path.")
    rotate_robot(-turn_angle)
    
    # Final forward movement with correction
    print("[DEBUG] Final forward movement with correction.")
    drive_forward_with_correction(power=-20, duration=0.5, Ldist=None, Fdist=None)

    print(f"[DEBUG] Rotating robot back by {turn_angle}° to resume path.")
    rotate_robot(turn_angle)
    
    print("[DEBUG] Avoidance maneuver complete.")


def monitor_emergency_stop():
    global stop_signal
    while not stop_signal:
        if EMERGENCY_STOP.is_pressed():
            print("[DEBUG] Emergency Stop Activated!")
            stop_signal = True
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            FIRE_SUPPRESSION_MOTOR.set_power(0)
            reset_brick()
            break
        time.sleep(0.1)

def play_siren():
    global siren_stop, stop_signal
    while not siren_stop and not stop_signal:
        siren_sound.play()
        time.sleep(0.5)


def navigate_to_fire_room():
    global in_room
    print("[DEBUG] Navigation to fire room started...")
    drive_forward_with_correction(power=-20, duration=0.5, Ldist=8, Fdist=57)
    time.sleep(0.2)
    turn_right_90()
    print("[DEBUG] Turned right 90°.")
    drive_forward_with_correction(power=-20, duration=0.4, Ldist=55, Fdist=33)
    time.sleep(0.2)
    turn_left_90()
    print("[DEBUG] Turned left 90°.")
    print("[DEBUG] Arrived at fire room.")
    in_room = True

def navigate_to_base():
    print("[DEBUG] Navigation to base started...")
    # we can add a check for the orange threshold here, but i would recommend making it in the scan_and_extinguish_fires function
    # so when we scan it we trigger this
    drive_forward_with_correction(power=-20, duration=0.5, Ldist=27, Fdist=57)
    time.sleep(0.2)
    turn_right_90()
    print("[DEBUG] Turned right 90°.")
    drive_forward_with_correction(power=-20, duration=0.5, Ldist=55, Fdist=8)
    time.sleep(0.2)
    turn_left_90()
    print("[DEBUG] Turned left 90°.")
    drive_forward_with_correction(power=-20, duration=0.4, Ldist=112, Fdist=8)
    time.sleep(0.2)
    print("[DEBUG] Arrived at base.")

def rotate_sensor_loop():

    global angle, fires_extinguished, stop_signal, fire_detected

    COLOUR_MOTOR.reset_encoder()
    if in_room:
        print("[DEBUG] Fire scanning started...")
    while not stop_signal and fires_extinguished < 2:
        if not fire_detected:
            angles = list(range(0, 152, 10)) + list(range(150, -1, -10))
            for angle in angles:
                if stop_signal or fire_detected:
                    break
                rotate_sensor_to_position(angle, speed=25)
                time.sleep(0.03)
        else:
            time.sleep(3)
            rotate_sensor_to_position(0, speed=25)
        
def detect_fires_and_respond():

    global angle, fires_extinguished, stop_signal, fire_detected

    while not stop_signal and fires_extinguished < 2:
        color_val = COLOUR_SENSOR.get_value()        
        
        #print(f"[DEBUG] Sensor angle: {angle}°, Color: {color_val}")

        if color_val == 5:  # red

            fire_detected = True
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            print(f"[DEBUG] Red detected at {angle}° - stopping motors")
            time.sleep(0.2)
            rotate_sensor_to_position(150, speed=50)
            time.sleep(0.2)
            drop_sandbag_with_alignment(angle)
            fires_extinguished += 1
            time.sleep(1)
            fire_detected = False

        elif color_val == 3:  # Green detected
            fire_detected = True
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            print(f"[DEBUG] Green detected at {angle}° - stopping motors for 2 seconds.")
            time.sleep(0.2)
            rotate_sensor_to_position(0, speed=50)
            time.sleep(0.2)
            avoid_green_sticker(angle)
            time.sleep(1)
            fire_detected = False

        time.sleep(0.1)


def navigate_inside_fire_room():
    print("[DEBUG] Navigation inside fire room started...")
    drive_forward_with_correction_room(power=-10, duration=0.5, Ldist=76, Fdist=31)
    time.sleep(0.2)
    rotate_robot(-90)
    print("[DEBUG] rotated right 90°.")
    drive_forward_with_correction_room(power=-10, duration=0.5, Ldist=31, Fdist=9)
    time.sleep(0.2)
    rotate_robot(90)
    print("[DEBUG] rotated left 90°.")
    drive_forward_with_correction_room(power=-10, duration=0.5, Ldist=100, Fdist=8)
    time.sleep(0.2)
    rotate_robot(90)
    print("[DEBUG] rotated left 90°.")
    drive_forward_with_correction_room(power=-10, duration=0.5, Ldist=98, Fdist=50)
    time.sleep(0.2)
    rotate_robot(90)
    print("[DEBUG] rotated left 90°.")
    drive_forward_with_correction_room(power=-10, duration=0.5, Ldist=50, Fdist=74)
    time.sleep(0.2)
    rotate_robot(90)
    print("[DEBUG] rotated left 90°.")
    drive_forward_with_correction_room(power=-10, duration=0.5, Ldist=28, Fdist=26)
    time.sleep(0.2)
    rotate_robot(-90)
    print("[DEBUG] rotated right 90°.")

    print("[DEBUG] Navigation inside fire room complete.")

def main_mission():
    global stop_signal, siren_stop
    emergency_thread = threading.Thread(target=monitor_emergency_stop)
    siren_thread = threading.Thread(target=play_siren)
    emergency_thread.start()
    siren_thread.start()

    navigate_to_fire_room()

    print("[DEBUG] Arrived at fire room. Stopping siren.")
    siren_stop = True
    time.sleep(0.1)
    siren_thread.join()
    print("[DEBUG] Siren stopped.")

    sweep_thread = threading.Thread(target=rotate_sensor_loop)
    detect_thread = threading.Thread(target=detect_fires_and_respond)
    navigation_thread = threading.Thread(target=navigate_inside_fire_room)

    print("[DEBUG] Starting sweep thread.")
    sweep_thread.start()
    print("[DEBUG] Starting detect thread.")
    detect_thread.start()
    print("[DEBUG] Starting navigation inside fire room thread.")
    navigation_thread.start()
    
    sweep_thread.join()
    detect_thread.join()
    navigation_thread.join()
    print("[DEBUG] All threads joined.")

    navigate_to_base()

    emergency_thread.join()
    print("[DEBUG] Mission completed.")

if __name__ == "__main__":
    wait_ready_sensors(True)
    print("[DEBUG] Firefighter Robot Full Mission Starting...")
    main_mission()
    print("[DEBUG] System shut down.")