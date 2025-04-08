
from brickpi3 import BrickPi3
from time import sleep

SLOW_THRESHOLD = 20
STOP_THRESHOLD = 5

FAST_POWER = 30
SLOW_POWER = FAST_POWER // 2

class Motor:
    def __init__(self, brickpi, port_str):
        self.brickpi = brickpi
        if port_str == "A":
            self.port = brickpi.PORT_A
        elif port_str == "B":
            self.port = brickpi.PORT_B
        elif port_str == "C":
            self.port = brickpi.PORT_C
        elif port_str == "D":
            self.port = brickpi.PORT_D
        else:
            raise Exception("invalid motor port")

        brickpi.reset_motor_encoder(self.port, 0)
        self.target_angle = 0

    def turn_by_angle(self, angle):
        self.target_angle += angle

    def tick(self):
        motor_position = self.brickpi.get_motor_position(self.port)
        motor_offset = motor_position - self.target_angle

        if motor_offset > SLOW_THRESHOLD:
            self.brickpi.set_motor_power(self.port, -FAST_POWER)
        elif motor_offset > STOP_THRESHOLD:
            self.brickpi.set_motor_power(self.port, -SLOW_POWER)
        elif motor_offset > -STOP_THRESHOLD:
            self.brickpi.set_motor_power(self.port, 0)
        elif motor_offset > -SLOW_THRESHOLD:
            self.brickpi.set_motor_power(self.port, SLOW_POWER)
        else:
            self.brickpi.set_motor_power(self.port, FAST_POWER)
