#!/usr/bin/env python3

import threading # a bit advanced but might as well use it to run diff components simultaneously, if not intsalled in the brickpy we can remove it
from time import sleep
from utils.brick import TouchSensor, EV3UltrasonicSensor, Motor, wait_ready_sensors, reset_brick
from utils.sound import Sound

# Initialize sensors and motors, the ports number will be tweaked on monday:
US_SENSOR = EV3UltrasonicSensor(2)  # Ultrasonic sensor for flute
DRUM_BUTTON = TouchSensor(1)  # Button to start/stop drum
EMERGENCY_STOP = TouchSensor(3)  # Emergency stop button
MOTOR = Motor("A")  # Motor for drumming

# Define musical notes (adjust duration as needed)
NOTE_C = Sound(duration=0.3, pitch="C4", volume=80)
NOTE_D = Sound(duration=0.3, pitch="D4", volume=80)
NOTE_E = Sound(duration=0.3, pitch="E4", volume=80)
NOTE_F = Sound(duration=0.3, pitch="F4", volume=80)

# Global state variables
drum_active = False
stop_signal = False

def play_flute():
    """Continuously reads ultrasonic sensor values and plays notes."""
    global stop_signal
    while not stop_signal:
        distance = US_SENSOR.get_value()
        if distance is None:
            continue  # Ignore invalid readings

        if distance < 5:
            NOTE_C.play()
        elif 5 <= distance < 10:
            NOTE_D.play()
        elif 10 <= distance < 20:
            NOTE_E.play()
        elif distance >= 30:
            NOTE_F.play()

        sleep(0.5)  # Small delay to allow smooth transitions, can be tweaked to our liking


def play_drum():
    """Controls the drumming motor."""
    global drum_active, stop_signal

    while not stop_signal:
        if DRUM_BUTTON.is_pressed():
            drum_active = not drum_active  # Toggle drumming on/off
            sleep(0.5)  # Debounce to prevent multiple toggles

        if drum_active:
            MOTOR.set_power(50)  # Rotate motor for drumming
        else:
            MOTOR.set_power(0)  # Stop motor

        sleep(0.1)  # Small delay 


def emergency_stop():
    """Stops all operations immediately when emergency stop is pressed."""
    global stop_signal, drum_active
    while not stop_signal:
        if EMERGENCY_STOP.is_pressed():
            print("Emergency Stop Activated!")
            stop_signal = True  # Signal all threads to stop
            MOTOR.set_power(0)  # Stop motor
            reset_brick()  # Reset all sensors and actuators
            break  # Exit the function

        sleep(0.1)


if __name__ == "__main__":
    wait_ready_sensors(True)  # Ensure all sensors and motors are ready

    print("Musical Instrument Robot Initialized.")
    print("Press the drum button to start/stop drumming.")
    print("Move your hand in front of the ultrasonic sensor to play flute notes.")
    print("Press the emergency stop button to halt everything.")

    # Create threads for simultaneous execution
    flute_thread = threading.Thread(target=play_flute)
    drum_thread = threading.Thread(target=play_drum)
    stop_thread = threading.Thread(target=emergency_stop)

    # Start all threads
    flute_thread.start()
    drum_thread.start()
    stop_thread.start()

    # Wait for emergency stop
    stop_thread.join()  # Main thread waits for stop
    flute_thread.join()  # Ensure flute stops
    drum_thread.join()  # Ensure drum stops

    print("System shut down.")
