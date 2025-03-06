import threading
from time import sleep
from utils.brick import EV3ColorSensor, EV3UltrasonicSensor, Motor, TouchSensor, wait_ready_sensors, reset_brick

# Initialize sensors and motors
COLOR_SENSOR = EV3ColorSensor("3")  # Detects fire (red color)
ULTRASONIC_SENSOR = EV3UltrasonicSensor("2")  # Detects obstacles
EMERGENCY_STOP = TouchSensor("1")  # Stops everything immediately
SECOND_TOUCH = TouchSensor("4")  # Reserved for future functionality
LEFT_MOTOR = Motor("D")  # Left wheel motor
RIGHT_MOTOR = Motor("A")  # Right wheel motor
DUMP_MOTOR = Motor("C")  # Medium motor to drop sandbag

# Global control variables
stop_signal = False
robot_moving = True  # Track if the robot should move


def detect_fire():
    """Stops the robot and activates the dump mechanism if fire (red color) is detected."""
    global robot_moving

    while not stop_signal:
        color = COLOR_SENSOR.get_value()

        if color is not None:  # Ensure a valid reading
            print(f"Detected Color: {color}")  # Debugging log

            if color == 5:  # Red detected
                print("Fire detected! Stopping movement and dropping sandbag.")
                
                # Stop the robot
                robot_moving = False
                LEFT_MOTOR.set_power(0)
                RIGHT_MOTOR.set_power(0)

                # Activate dump mechanism
                DUMP_MOTOR.set_power(50)
                sleep(1)
                DUMP_MOTOR.set_power(0)

                # Resume movement after dropping sandbag
                robot_moving = True

        sleep(0.2)  # Increase frequency of color detection