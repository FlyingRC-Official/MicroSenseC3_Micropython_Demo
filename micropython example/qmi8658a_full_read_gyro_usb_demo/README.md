# QMI8658A Full-Read Library And Gyro USB Serial Demo

## Purpose

This MicroPython demo adds a reusable `QMI8658A` driver for the on-board IMU and a small `main.py` example that prints only gyroscope readings over the ESP32-C3 USB serial port.

The library reads:

- temperature
- accelerometer
- gyroscope

The example prints:

- timestamp in milliseconds
- `gx_dps`
- `gy_dps`
- `gz_dps`

## Target Board

- Custom ESP32-C3 development board in this repository

## Pin Assumptions

- I2C `SDA`: `GPIO6`
- I2C `SCL`: `GPIO7`
- QMI8658A I2C address: `0x6A`
- USB serial comes from the ESP32-C3 USB connection

## Files

- `qmi8658a.py`: reusable QMI8658A driver
- `main.py`: gyro-only USB serial example

## Library API

The `QMI8658A` class exposes:

- `probe()`
- `chip_id()`
- `reset()`
- `configure()`
- `init()`
- `read_raw()`
- `read_scaled()`
- `read_accel_raw()`
- `read_accel_g()`
- `read_gyro_raw()`
- `read_gyro_dps()`
- `read_temperature_c()`

`read_scaled()` returns a dictionary with:

- `temp_c`
- `accel_g`
- `gyro_dps`

## How To Run

1. Copy `qmi8658a.py` and `main.py` to the board filesystem.
2. Place `main.py` at the board root as `/main.py`.
3. Reset the board.
4. Open the USB serial COM port at the MicroPython REPL connection.

If you want to upload from this repository, the local tooling can be used with `mpremote_esp32c3.cmd`.

## Expected Serial Output

You should see lines similar to:

```text
QMI8658A gyro USB serial demo
I2C: bus=0, SDA=GPIO6, SCL=GPIO7, addr=0x6A
Library reads temperature, accelerometer, and gyroscope data
USB serial output below is gyro only
Columns: ms,gx_dps,gy_dps,gz_dps
Initializing sensor...
Sensor ready
15,0.12,-0.05,0.09
116,0.09,-0.04,0.02
216,0.18,1.67,-0.21
```

## Success Looks Like

- The script starts without an initialization error.
- The serial console shows the startup banner once.
- The serial console then prints CSV samples repeatedly.
- Rotating the board changes the reported gyro values.

## Notes And Limitations

- This version uses I2C polling only.
- FIFO, interrupts, self-test, and motion-engine features are intentionally not used.
- The library reads temperature and accelerometer data, but the example does not print them.
- The sensor output data rate is configured faster than the print loop. The demo intentionally downsamples to keep the USB serial output easy to read.
