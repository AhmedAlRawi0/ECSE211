#!/usr/bin/env python3

from utils.sound import Sound
from utils.brick import TouchSensor, EV3UltrasonicSensor, wait_ready_sensors, reset_brick
from time import sleep

# Sensor and button setup
US_SENSOR = EV3UltrasonicSensor(2)
PLAY_BUTTON = TouchSensor(1)
STOP_BUTTON = TouchSensor(3)

# Define sound notes
A4 = Sound(duration=0.3, pitch="A4", volume=80)
B4 = Sound(duration=0.3, pitch="B4", volume=80)
C4 = Sound(duration=0.3, pitch="C4", volume=80)
D4 = Sound(duration=0.3, pitch="D4", volume=80)

def main() -> None:
    wait_ready_sensors(True)
    print("Sensors loaded. You may start playing.")

    # Open CSV file for logging
    with open("Flute_test.csv", "w") as output_file:
        output_file.write("Distance (cm), Note Played\n")  # CSV header

        while not STOP_BUTTON.is_pressed():
            if PLAY_BUTTON.is_pressed():
                distance = US_SENSOR.get_value()

                if distance < 10:
                    A4.play()
                    output_file.write(f"{distance}, A4\n")
                    A4.wait_done()
                elif distance < 20:
                    B4.play()
                    output_file.write(f"{distance}, B4\n")
                    B4.wait_done()
                elif distance < 30:
                    C4.play()
                    output_file.write(f"{distance}, C4\n")
                    C4.wait_done()
                else:
                    D4.play()
                    output_file.write(f"{distance}, D4\n")
                    D4.wait_done()

    print("Test completed. Data saved in Flute_test.csv.")

if __name__ == "__main__":
    main()
