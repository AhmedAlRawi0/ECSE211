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


def control_movement():
    """Controls the movement of the robot based on the state."""
    global robot_moving

    while not stop_signal:
        if robot_moving:
            LEFT_MOTOR.set_power(50)
            RIGHT_MOTOR.set_power(50)
        else:
            LEFT_MOTOR.set_power(0)
            RIGHT_MOTOR.set_power(0)
        sleep(0.1)  # Small delay to avoid excessive CPU usage


def check_obstacles():
    """Stops the motors if an obstacle is within 10 cm."""
    global robot_moving
    while not stop_signal:
        distance = ULTRASONIC_SENSOR.get_value()
        if distance is not None and distance <= 10:
            print("Obstacle detected! Stopping.")
            robot_moving = False  # Stop the robot
        else:
            robot_moving = True  # Resume movement when clear
        sleep(0.1)


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

    # Start parallel tasks
    move_thread = threading.Thread(target=control_movement)
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
