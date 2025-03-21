import threading
import time
from utils.brick import (
    TouchSensor,
    EV3ColorSensor,
    Motor,
    wait_ready_sensors,
    reset_brick,
)

# Global Variables
stop_signal = False
fires_extinguished = 0  # Number of fires extinguished

# Sensors & Motors
EMERGENCY_STOP = TouchSensor(3)  # Emergency stop button
COLOR_SENSOR = EV3ColorSensor(1, mode="id")  # Color sensor for fire detection
FIRE_SUPPRESSION_MOTOR = Motor("C")  # Motor to drop sandbag

# ----------------------------
# Emergency Stop Monitor (Threaded)
# ----------------------------
def monitor_emergency_stop():
    """Continuously check the emergency stop sensor."""
    global stop_signal
    while not stop_signal:
        if EMERGENCY_STOP.is_pressed():
            print(" Emergency Stop Activated! Halting all operations.")
            stop_signal = True
            FIRE_SUPPRESSION_MOTOR.set_power(0)
            reset_brick()  # Reset sensors and actuators
            break
        time.sleep(0.1)

# ----------------------------
# Fire Detection & Extinguishing
# ----------------------------
def scan_and_extinguish_fires():
    """
    Continuously scans for fires (red color).
    When a fire is detected, drops a sandbag and increments count.
    Stops when 2 fires are extinguished or emergency stop is pressed.
    """
    global fires_extinguished

    print("Fire scanning started... Looking for red stickers.")

    while fires_extinguished < 2 and not stop_signal:
        color_val = COLOR_SENSOR.get_value()
        
        if color_val == 5:  # Red detected (fire)
            print(f"Fire detected! Initiating suppression ({fires_extinguished + 1}/2).")
            drop_sandbag()
            fires_extinguished += 1
            time.sleep(1)  # Pause to simulate extinguishing

        time.sleep(0.2)  # Prevent excessive polling

    print(" Required fires extinguished. Stopping fire scan.")

# ----------------------------
# Sandbag Deployment
# ----------------------------
def drop_sandbag():
    """
    Simulates dropping a sandbag to extinguish a fire.
    """
    print("🪣 Dropping sandbag on fire...")
    FIRE_SUPPRESSION_MOTOR.set_power(50)
    time.sleep(1)  # Time to drop the sandbag
    FIRE_SUPPRESSION_MOTOR.set_power(0)
    print("Sandbag deployed.")

# ----------------------------
# Fire Suppression Test Sequence
# ----------------------------
def fire_suppression_test():
    """Runs the fire detection, suppression, and emergency stop test."""
    global stop_signal

    # Start emergency stop monitoring in a separate thread
    emergency_thread = threading.Thread(target=monitor_emergency_stop)
    emergency_thread.start()

    # Start fire scanning and suppression
    scan_and_extinguish_fires()

    # Stop after fires are extinguished or emergency stop is triggered
    stop_signal = True
    emergency_thread.join()

    print("Fire suppression test completed.")

# ----------------------------
# Main Execution
# ----------------------------
if __name__ == "__main__":
    wait_ready_sensors(True)
    print(" Firefighter Robot Fire Suppression Test Initialized.")
    fire_suppression_test()
    print(" System shut down.")
