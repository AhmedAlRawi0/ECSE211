#!/usr/bin/env python3

from utils.sound import Sound
from utils.brick import TouchSensor, EV3UltrasonicSensor, wait_ready_sensors, reset_brick
from time import sleep

US_SENSOR = EV3UltrasonicSensor(2)
PLAY_BUTTON = TouchSensor(1)
STOP_BUTTON = TouchSensor(3)
A4 = Sound(duration=0.3, pitch="A4", volume=80)
B4 = Sound(duration=0.3, pitch="B4", volume=80)
C4 = Sound(duration=0.3, pitch="C4", volume=80)
D4 = Sound(duration=0.3, pitch="D4", volume=80)

def main() -> None:
    
    wait_ready_sensors(True)
    print("Sensors loaded. You may start playing.")

    while not STOP_BUTTON.is_pressed():
        if PLAY_BUTTON.is_pressed():
            distance = US_SENSOR.get_value()
            if distance < 10:
                A4.play()
                A4.wait_done()
            elif distance < 20:
                B4.play()
                B4.wait_done()
            elif distance < 30:
                C4.play()
                C4.wait_done()
            else:
                D4.play()
                D4.wait_done()

if __name__ == "__main__":
    main()
