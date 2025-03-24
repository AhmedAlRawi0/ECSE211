use std::{thread, time::Duration};

use anyhow::{anyhow, bail};
use brickpi3::{BrickPi3, MotorPort, SensorData, SensorPort, SensorType};

fn main() -> anyhow::Result<()> {
    let mut brickpi = BrickPi3::open("/dev/spidev0.1")?;

    brickpi.set_sensor_type(SensorPort::Port4, SensorType::Touch, 0)?;

    print!("Configuring sensors... ");
    while let Err(_) = brickpi.read_sensor(SensorPort::Port4) {}
    println!("done.");

    let enc_pos_left = brickpi.read_motor_encoder(MotorPort::PortA)?;
    let enc_pos_right = brickpi.read_motor_encoder(MotorPort::PortB)?;

    brickpi.set_motor_power(MotorPort::PortA, 20)?;
    thread::sleep(Duration::from_millis(50));
    brickpi.set_motor_power(MotorPort::PortB, -20)?;
    thread::sleep(Duration::from_millis(50));

    loop {
        let SensorData::Touch { pressed } = brickpi
            .read_sensor(SensorPort::Port4)
            .map_err(|e| anyhow!("{e:?}"))?
        else {
            bail!("invalid sensor data")
        };
        if pressed {
            println!("Cancelled.");
            break;
        }
        if brickpi.read_motor_encoder(MotorPort::PortA)? - enc_pos_left > 179
            || brickpi.read_motor_encoder(MotorPort::PortB)? - enc_pos_right < -179
        {
            println!("Rotation complete!");
            break;
        }
        thread::sleep(Duration::from_millis(50));
    }

    brickpi.set_motor_power(MotorPort::PortA, 0)?;
    thread::sleep(Duration::from_millis(50));
    brickpi.set_motor_power(MotorPort::PortB, 0)?;
    thread::sleep(Duration::from_millis(50));

    println!("Hello, BrickPi!");

    Ok(())
}
