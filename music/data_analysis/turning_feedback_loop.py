import time

def feedback_loop():
    X = 60  # Target distance from the wall
    
    while True:
        distance = ULTRASONIC_SENSOR.get_cm()  # Read distance
        
        if distance > X:  # Stop when desired distance is reached
            break
        
        """Perform an approximate 90° right turn using differential drive."""
        if stop_signal:
            return  # Exit if a stop signal is detected
        
        LEFT_MOTOR.set_power(50)
        RIGHT_MOTOR.set_power(-50)
        time.sleep(0.8)  # Adjust turning duration if needed
        LEFT_MOTOR.set_power(0)
        RIGHT_MOTOR.set_power(0)
        
        print("Turning feedback loop")
    
    print("Desired distance reached. Stopping feedback loop.")
