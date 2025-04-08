
from brickpi3 import BrickPi3
from os import environ

from motor import Motor

WHEEL_SEPARATION_CM = 15
WHEEL_DIAMETER_CM = 4

class Robot:
    def __init__(self):
        self.brickpi = BrickPi3()

        if environ.get("ROBOT_LEFT_DRIVE_PORT") is not None:
            self.left_motor = Motor(self.brickpi, environ["ROBOT_LEFT_DRIVE_PORT"])
        else:
            self.left_motor = Motor(self.brickpi, "A")

        if environ.get("ROBOT_RIGHT_DRIVE_PORT") is not None:
            self.right_motor = Motor(self.brickpi, environ["ROBOT_RIGHT_DRIVE_PORT"])
        else:
            self.right_motor = Motor(self.brickpi, "B")

        if environ.get("ROBOT_COLOUR_SENSOR_MOTOR_PORT") is not None:
            self.colour_sensor_motor = Motor(self.brickpi, environ["ROBOT_COLOUR_SENSOR_MOTOR_PORT"])
        else:
            self.colour_sensor_motor = Motor(self.brickpi, "C")

        if environ.get("ROBOT_DROPPER_MOTOR_PORT") is not None:
            self.dropper_motor = Motor(self.brickpi, environ["ROBOT_DROPPER_MOTOR_PORT"])
        else:
            self.dropper_motor = Motor(self.brickpi, "D")

        if environ.get("ROBOT_COLOUR_SENSOR_PORT") is not None:
            self.colour_sensor = ColourSensor(self.brickpi, environ["ROBOT_COLOUR_SENSOR_PORT"])
        else:
            self.colour_sensor = ColourSensor(self.brickpi, "2")

        if environ.get("ROBOT_FRONT_US_SENSOR_PORT") is not None:
            self.front_us_sensor = UltrasonicSensor(self.brickpi, environ["ROBOT_FRONT_US_SENSOR_PORT"])
        else:
            self.front_us_sensor = UltrasonicSensor(self.brickpi, "3")

        if environ.get("ROBOT_SIDE_US_SENSOR_PORT") is not None:
            self.side_us_sensor = UltrasonicSensor(self.brickpi, environ["ROBOT_SIDE_US_SENSOR_PORT"])
        else:
            self.side_us_sensor = UltrasonicSensor(self.brickpi, "1")

        if environ.get("ROBOT_TOUCH_SENSOR_PORT") is not None:
            self.emergency_stop = TouchSensor(self.brickpi, environ["ROBOT_TOUCH_SENSOR_PORT"])
        else:
            self.emergency_stop = TouchSensor(self.brickpi, "2")

    def rotate(self, angle):
        wheel_angle = angle * WHEEL_SEPARATION_CM // WHEEL_DIAMETER_CM
        self.left_motor.turn_by_angle(wheel_angle)
        self.right_motor.turn_by_angle(-wheel_angle)

    def drive(self, distance_cm):
        wheel_angle = distance_cm * 720 // WHEEL_DIAMETER_CM
        self.left_motor.turn_by_angle(wheel_angle)
        self.right_motor.turn_by_angle(wheel_angle)

    def tick(self):
        self.left_motor.tick()
        self.right_motor.tick()
        self.colour_sensor_motor.tick()
        self.dropper_motor.tick()

        self.colour_sensor.tick()
        self.front_us_sensor.tick()
        self.side_us_sensor.tick()
        self.emergency_stop.tick()
