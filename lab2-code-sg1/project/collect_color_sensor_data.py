#!/usr/bin/env python3

"""
This test is used to collect data from the color sensor.
It must be run on the robot.
"""

# Add your imports here, if any
from utils.brick import EV3ColorSensor, wait_ready_sensors, TouchSensor, reset_brick
from time import sleep


COLOR_SENSOR_DATA_FILE = "../data_analysis/color_sensor.csv"

# complete this based on your hardware setup
COLOR_SENSOR = EV3ColorSensor(1)  # Port 1 for the color sensor, yet we can change this in the lab
TOUCH_SENSOR = TouchSensor(2)     # Port 2 for the touch sensor

wait_ready_sensors(True)  # Input True to see what the robot is trying to initialize! False to be silent.

def collect_color_sensor_data():
    "Collect color sensor data."
    try:
        output_file = open(COLOR_SENSOR_DATA_FILE, "w")
        output_file.write("R,G,B\n")  # Write CSV header
        
        print("Waiting for the first touch sensor press to start data collection.")

        while not TOUCH_SENSOR.is_pressed():
            pass  # Wait for the first button press
        
        #sleep(1)
        
        while True :
            if TOUCH_SENSOR.is_pressed():
                # Read RGB data from the color sensor
                rgb_data = COLOR_SENSOR.get_rgb()  # Returns (R, G, B)
                r, g, b = rgb_data
                print(f"RGB: {r}, {g}, {b}") # to keep track of the data in the console
                output_file.write(f"{r},{g},{b}\n")  # Write RGB to file
                #sleep(1)  # Small delay to avoid accidental double presses
                while TOUCH_SENSOR.is_pressed():
                        pass  # Debounce to prevent duplicate readings

    except BaseException: # capture all exceptions including KeyboardInterrupt (Ctrl-C)
        pass 
    finally:
        print("Done collecting RGB data.")
        output_file.close()  # Close the file
        reset_brick()  # Reset hardware on the brick
        exit()


if __name__ == "__main__":
    collect_color_sensor_data()
