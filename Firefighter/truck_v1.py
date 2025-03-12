import threading
from time import sleep
from utils.brick import TouchSensor, EV3UltrasonicSensor, EV3ColorSensor, Motor, wait_ready_sensors, reset_brick
from utils.sound import Sound

# Initialize sensors and actuators
US_SENSOR = EV3UltrasonicSensor(2)  # Ultrasonic sensor for obstacle detection
COLOR_SENSOR = EV3ColorSensor(3)  # Color sensor for fire detection
EMERGENCY_STOP = TouchSensor(4)  # Emergency stop button
MOTOR_LEFT = Motor("A")  # Left wheel motor
MOTOR_RIGHT = Motor("B")  # Right wheel motor
EXTINGUISHER = Motor("C")  # Extinguishing mechanism, throwing a sandbag
# I am not sure about the extinguisher, as I am not sure how it will work, we have not figured out its logic/hardware yet

# Fire truck siren
SIREN = Sound(duration=3, pitch="C4", volume=100)

# Global variables
stop_signal = False
mission_complete = False
fires_extinguished = 0
return_to_base = False


def move_forward():
    """Moves the robot forward continuously."""
    global stop_signal, mission_complete, return_to_base
    while not stop_signal and not mission_complete:
        MOTOR_LEFT.set_power(50)
        MOTOR_RIGHT.set_power(50)
        sleep(0.1)

def turn_left_90():
    """Executes a 90-degree left turn."""
    MOTOR_LEFT.set_power(-30)
    MOTOR_RIGHT.set_power(30)
    sleep(0.8)  # Adjust timing for accurate 90-degree turn
    MOTOR_LEFT.set_power(50)
    MOTOR_RIGHT.set_power(50)

def turn_right_90():
    """Executes a 90-degree right turn."""
    MOTOR_LEFT.set_power(30)
    MOTOR_RIGHT.set_power(-30)
    sleep(0.8)
    MOTOR_LEFT.set_power(50)
    MOTOR_RIGHT.set_power(50)

def detect_obstacles(): 
    # I am not entirely sure about this in terms of the distance, as the US sensor is placed at the top
    # of the robot, so not sure how it will detect the obstacles beneath it + is it a stikcer or what exactly?
    """Monitors ultrasonic sensor and avoids obstacles."""
    global stop_signal, return_to_base
    while not stop_signal:
        distance = US_SENSOR.get_value()
        if distance and distance < 5:
            MOTOR_LEFT.set_power(0)
            MOTOR_RIGHT.set_power(0)
            sleep(0.5)
            turn_left_90() if distance < 5 else turn_right_90()
        sleep(0.1)

def detect_fire():
    """Detects fire using the color sensor and triggers extinguishing."""
    global mission_complete, fires_extinguished, return_to_base
    while not mission_complete:
        rgb = COLOR_SENSOR.get_rgb()
        if rgb and rgb[0] > rgb[1] and rgb[0] > rgb[2]:  # Red is dominant (fire detected)
            MOTOR_LEFT.set_power(0)
            MOTOR_RIGHT.set_power(0)
            sleep(0.5)
            release_extinguisher()
            fires_extinguished += 1
        
        if fires_extinguished >= 2:
            return_to_base = True  # Start returning to base
        sleep(0.1)

def release_extinguisher(): # to be retweaked once we figure out how the extinguisher works and we gonna throw the sandbag
    """Releases the simulated fire extinguisher."""
    EXTINGUISHER.set_power(50)
    sleep(1)
    EXTINGUISHER.set_power(0)
    print("Fire extinguished!")

def navigate_to_base(): # again, not very clear as we still more questions about the base and will the floor be colored and whatnot
    """Returns the robot to the starting position after completing the mission."""
    global mission_complete
    print("Returning to base...")
    MOTOR_LEFT.set_power(-50)
    MOTOR_RIGHT.set_power(-50)
    sleep(2)  # Adjust based on testing distance
    MOTOR_LEFT.set_power(0)
    MOTOR_RIGHT.set_power(0)
    mission_complete = True
    print("Mission completed!")

def emergency_stop():
    """Stops all operations when emergency stop is pressed."""
    global stop_signal
    while not stop_signal:
        if EMERGENCY_STOP.is_pressed():
            print("Emergency Stop Activated!")
            stop_signal = True
            MOTOR_LEFT.set_power(0)
            MOTOR_RIGHT.set_power(0)
            EXTINGUISHER.set_power(0)
            reset_brick()
            break
        sleep(0.1)

def main():
    """Main function to start the robot."""
    wait_ready_sensors(True)
    print("Firefighter Robot Initialized.")
    SIREN.play()
    
    # Start threads
    movement_thread = threading.Thread(target=move_forward)
    obstacle_thread = threading.Thread(target=detect_obstacles)
    fire_thread = threading.Thread(target=detect_fire)
    stop_thread = threading.Thread(target=emergency_stop)
    
    movement_thread.start()
    obstacle_thread.start()
    fire_thread.start()
    stop_thread.start()
    
    stop_thread.join()  # Wait for emergency stop
    movement_thread.join()
    obstacle_thread.join()
    fire_thread.join()
    
    if return_to_base:
        navigate_to_base()
    
    print("System shut down.")

if __name__ == "__main__":
    main()
