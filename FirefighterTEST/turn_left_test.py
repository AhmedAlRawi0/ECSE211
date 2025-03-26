
from utils.brick import (
    TouchSensor,
    Motor,
    wait_ready_sensors,
    reset_brick,
)

EMERGENCY_STOP = TouchSensor(4)

LEFT_MOTOR = Motor("A")
RIGHT_MOTOR = Motor("B")

def main() -> None:
    print("Configuring sensors... ", end="")
    wait_ready_sensors(True)
    print("done.")

    enc_pos_left = LEFT_MOTOR.get_position()
    enc_pos_right = RIGHT_MOTOR.get_position()

    LEFT_MOTOR.set_power(20)
    RIGHT_MOTOR.set_power(20)

    while not EMERGENCY_STOP.is_pressed():
        enc_new_pos_left = LEFT_MOTOR.get_position()
        enc_new_pos_right = RIGHT_MOTOR.get_position()

        if (enc_new_pos_left - enc_pos_left > 290
            or enc_new_pos_right - enc_pos_right < -290):
            LEFT_MOTOR.set_power(10)
            RIGHT_MOTOR.set_power(-10)

            if (enc_new_pos_left - enc_pos_left > 300
                or enc_new_pos_right - enc_pos_right < -300):
                print("Rotation complete.")
                break

    LEFT_MOTOR.set_power(0)
    RIGHT_MOTOR.set_power(0)

    print("Test complete.")

if __name__ == "__main__":
    main()
