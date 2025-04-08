
from colour_detection import rgb_to_colour

class ColourSensor:
    def __init__(self, brickpi, port_str):
        self.brickpi = brickpi

        if port_str == "1":
            self.port = brickpi.PORT_1
        elif port_str == "2":
            self.port = brickpi.PORT_2
        elif port_str == "3":
            self.port = brickpi.PORT_3
        elif port_str == "4":
            self.port = brickpi.PORT_4
        else:
            raise Exception("invalid sensor port")

        brickpi.set_sensor_type(self.port, brickpi.SENSOR_TYPE.EV3_COLOR_COLOR_COMPONENTS)
        self.value = brickpi.get_sensor(self.port)

    def get_value(self):
        return rgb_to_colour(self.value)

    def tick(self):
        self.value = self.brickpi.get_sensor(self.port)
