#!/usr/bin/env python3

import threading
from time import sleep
from utils.brick import EV3ColorSensor, EV3UltrasonicSensor, Motor, TouchSensor, wait_ready_sensors, reset_brick

# Initialize sensors and motors (ports to be assigned later)
COLOR_SENSOR = EV3ColorSensor("3")  # Detects fire (red color)
ULTRASONIC_SENSOR = EV3UltrasonicSensor("2")  # Detects obstacles
EMERGENCY_STOP = TouchSensor("1")  # Stops everything immediately
SECOND_TOUCH = TouchSensor("4")  # Reserved for future functionality
LEFT_MOTOR = Motor("D")  # Left wheel motor
RIGHT_MOTOR = Motor("A")  # Right wheel motor
DUMP_MOTOR = Motor("C")  # Medium motor to drop sandbag

# Global stop signal
stop_signal = False


def move_forward():
    """Moves the robot forward."""
    while not stop_signal:
        LEFT_MOTOR.set_power(50)
        RIGHT_MOTOR.set_power(50)
        sleep(0.1)


def check_obstacles():
    """Stops the motors if an obstacle is within 10 cm."""
    global stop_signal
    while not stop_signal:
        distance = ULTRASONIC_SENSOR.get_value()
        if distance is not None and distance <= 10:
            print("Obstacle detected! Stopping.")
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
        sleep(0.1)


def detect_fire():
    """Activates the dump mechanism if fire (red color) is detected."""
    while not stop_signal:
        color = COLOR_SENSOR.get_value()
        if color == 5:  # Red color code
            print("Fire detected! Dropping sandbag.")
            DUMP_MOTOR.set_power(50)
            sleep(1)
            DUMP_MOTOR.set_power(0)
        sleep(0.1)


def emergency_stop():
    """Stops all operations when the emergency button is pressed."""
    global stop_signal
    while not stop_signal:
        if EMERGENCY_STOP.is_pressed():
            print("Emergency Stop Activated!")
            stop_signal = True
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
            DUMP_MOTOR.set_power(0)
            reset_brick()
            break
        sleep(0.1)


if __name__ == "__main__":
    wait_ready_sensors(True)
    print("Firefighter Rescue Robot Initialized.")
    print("Moving forward, detecting fire and obstacles.")

    # Start parallel tasks
    move_thread = threading.Thread(target=move_forward)
    obstacle_thread = threading.Thread(target=check_obstacles)
    fire_thread = threading.Thread(target=detect_fire)
    stop_thread = threading.Thread(target=emergency_stop)

    move_thread.start()
    obstacle_thread.start()
    fire_thread.start()
    stop_thread.start()

    # Wait for emergency stop
    stop_thread.join()
    move_thread.join()
    obstacle_thread.join()
    fire_thread.join()

    print("System shut down.")
