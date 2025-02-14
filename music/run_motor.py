#!/usr/bin/env python3

from utils.sound import Sound
from utils.brick import TouchSensor, EV3UltrasonicSensor, Motor, wait_ready_sensors, reset_brick
from time import sleep

RUN_BUTTON = TouchSensor(1)
STOP_BUTTON = TouchSensor(3)
MOTOR = Motor("A")

wait_ready_sensors()

while True:
  if RUN_BUTTON.is_pressed():
    MOTOR.set_power(50)
  elif STOP_BUTTON.is_pressed():
    MOTOR.set_power(0)
