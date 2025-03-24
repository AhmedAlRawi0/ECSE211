use anyhow::{anyhow, bail};
use brickpi3::{BrickPi3, MotorPort, SensorData, SensorError, SensorPort, SensorType};

fn main() -> anyhow::Result<()> {
    let mut brickpi = BrickPi3::open("/dev/spidev0.1")?;

    brickpi.set_sensor_type(SensorPort::Port4, SensorType::Touch, 0)?;

    print!("Configuring sensors... ");
    while let Err(SensorError::NotConfigured) = brickpi.read_sensor(SensorPort::Port4) {}
    println!("done.");

    brickpi.set_motor_power(MotorPort::PortA, 10)?;
    brickpi.set_motor_power(MotorPort::PortB, 10)?;

    brickpi.set_motor_power(MotorPort::PortA, 0)?;
    brickpi.set_motor_power(MotorPort::PortB, 0)?;

    brickpi.set_motor_position_relative(MotorPort::PortA, 179)?;
    brickpi.set_motor_position_relative(MotorPort::PortB, -179)?;

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
    }

    brickpi.set_motor_power(MotorPort::PortA, 0)?;
    brickpi.set_motor_power(MotorPort::PortB, 0)?;

    println!("Hello, BrickPi!");

    Ok(())
}
