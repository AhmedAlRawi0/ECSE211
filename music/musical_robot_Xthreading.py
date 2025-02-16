#!/usr/bin/env python3

from time import sleep
from utils.brick import TouchSensor, EV3UltrasonicSensor, Motor, wait_ready_sensors, reset_brick
from utils.sound import Sound

# Initialize sensors and motors
US_SENSOR = EV3UltrasonicSensor(2)  # Ultrasonic sensor for flute
DRUM_BUTTON = TouchSensor(1)  # Button to start/stop drum
EMERGENCY_STOP = TouchSensor(3)  # Emergency stop button
MOTOR = Motor("A")  # Motor for drumming

# Define musical notes
NOTE_C = Sound(duration=0.3, pitch="C4", volume=80)
NOTE_D = Sound(duration=0.3, pitch="D4", volume=80)
NOTE_E = Sound(duration=0.3, pitch="E4", volume=80)
NOTE_F = Sound(duration=0.3, pitch="F4", volume=80)

# Global state variables
drum_active = False

def play_flute():
    """Plays flute notes based on hand distance detected by ultrasonic sensor."""
    distance = US_SENSOR.get_value()
    
    if distance is None:
        return  # Ignore invalid readings

    if distance < 5:
        NOTE_C.play()
    elif 5 <= distance < 10:
        NOTE_D.play()
    elif 10 <= distance < 20:
        NOTE_E.play()
    elif distance >= 30:
        NOTE_F.play()

    sleep(0.5)  # Small delay to allow smooth transitions, can be tweaked to our liking


def control_drum():
    """Handles drumming motor based on button press."""
    global drum_active

    if DRUM_BUTTON.is_pressed():
        drum_active = not drum_active  # Toggle drumming on/off
        sleep(0.5)  # Debounce

    if drum_active:
        MOTOR.set_power(50)  # Start drumming
    else:
        MOTOR.set_power(0)  # Stop drumming

def check_emergency_stop():
    """Stops all operations immediately when emergency stop is pressed."""
    if EMERGENCY_STOP.is_pressed():
        print("Emergency Stop Activated!")
        MOTOR.set_power(0)  # Stop motor
        reset_brick()  # Reset all sensors and actuators
        return True  # Signal main loop to exit
    return False  # Continue running

if __name__ == "__main__":
    wait_ready_sensors(True)  # Ensure all sensors and motors are ready

    print("Musical Instrument Robot Initialized.")
    print("Press the drum button to start/stop drumming.")
    print("Move your hand in front of the ultrasonic sensor to play flute notes.")
    print("Press the emergency stop button to halt everything.")

    # Main loop (sequential execution without threads)
    while True:
        if check_emergency_stop():
            break  # Exit the loop if emergency stop is triggered

        play_flute()
        control_drum()
        
        sleep(0.1)  # Small delay

    print("System shut down.")
