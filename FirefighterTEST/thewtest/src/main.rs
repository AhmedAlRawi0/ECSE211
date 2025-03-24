use brickpi::BrickPi;

fn main() -> anyhow::Result<()> {
    let brickpi = BrickPi::open("/dev/spidev0.1")?;

    println!("Hello, BrickPi!");
}
