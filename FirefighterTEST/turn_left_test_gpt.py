#!/usr/bin/env python3

import time
import sys
from brickpi3 import BrickPi3

# Define global constants for ports
LEFT_MOTOR = BrickPi3.PORT_A
RIGHT_MOTOR = BrickPi3.PORT_B
EMERGENCY_STOP = BrickPi3.PORT_4

def main():
    try:
        # Initialize BrickPi3
        brickpi = BrickPi3()
        
        # Configure touch sensor on port 4
        brickpi.set_sensor_type(EMERGENCY_STOP, BrickPi3.SENSOR_TYPE.TOUCH)
        
        print("Configuring sensors... ", end='')
        # Wait until sensor is ready
        while True:
            try:
                brickpi.get_sensor(EMERGENCY_STOP)
                break
            except BrickPi3.SensorError:
                pass
        print("done.")
        
        # Read initial encoder positions
        enc_pos_left = brickpi.get_motor_encoder(LEFT_MOTOR)
        enc_pos_right = brickpi.get_motor_encoder(RIGHT_MOTOR)
        
        # Start motors
        brickpi.set_motor_power(LEFT_MOTOR, 20)
        time.sleep(0.05)
        brickpi.set_motor_power(RIGHT_MOTOR, -20)
        time.sleep(0.05)
        
        # Main control loop
        while True:
            # Check emergency stop
            try:
                pressed = brickpi.get_sensor(EMERGENCY_STOP)
                if pressed:
                    print("Cancelled.")
                    break
            except Exception as e:
                print(f"Error reading sensor: {e}")
                break
            
            # Read encoder positions
            enc_new_pos_left = brickpi.get_motor_encoder(LEFT_MOTOR)
            enc_new_pos_right = brickpi.get_motor_encoder(RIGHT_MOTOR)
            
            # Check if rotation threshold is reached
            if enc_new_pos_left - enc_pos_left > 290 or enc_new_pos_right - enc_pos_right < -290:
                # Slow down
                brickpi.set_motor_power(LEFT_MOTOR, 10)
                brickpi.set_motor_power(RIGHT_MOTOR, -10)
                
                # Check if final rotation is complete
                if enc_new_pos_left - enc_pos_left > 300 or enc_new_pos_right - enc_pos_right < -300:
                    print("Rotation complete!")
                    break
            
            time.sleep(0.05)
        
        # Stop motors
        brickpi.set_motor_power(LEFT_MOTOR, 0)
        time.sleep(0.05)
        brickpi.set_motor_power(RIGHT_MOTOR, 0)
        time.sleep(0.05)
        
        print("Hello, BrickPi!")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Always reset BrickPi when exiting
        try:
            brickpi.reset_all()
        except:
            pass

if __name__ == "__main__":
    main()
