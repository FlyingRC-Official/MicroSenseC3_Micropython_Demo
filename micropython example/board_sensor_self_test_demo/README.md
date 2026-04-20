# Board Sensor Self-Test Demo

## Purpose

This MicroPython demo is a first-run board health check for the custom ESP32-C3 development board in this repository.

It verifies the full onboard sensor set on the shared I2C bus:

- `QMI8658A` IMU
- `QMC6309` magnetometer
- `SPA06-003` pressure sensor
- `SHT40` temperature and humidity sensor
- `LTR-381RGB-01` light and color sensor

The demo starts with a one-shot self-test summary, then continues with a slow live monitor so users can see working sensor data on the serial console.

## Target Board

- Custom ESP32-C3 development board in this repository

## Pin Assumptions

- I2C bus ID: `0`
- I2C `SDA`: `GPIO6`
- I2C `SCL`: `GPIO7`
- USB serial comes from the ESP32-C3 USB connection

## Expected I2C Addresses

- `QMI8658A`: `0x6A`
- `QMC6309`: `0x7C`
- `SPA06-003`: `0x77`
- `SHT40`: `0x44`
- `LTR-381RGB-01`: `0x53`

## Files

- `main.py`: startup self-test and live monitor entrypoint
- `board_sensors.py`: focused sensor helpers used by the demo

## What The Demo Checks

The startup test uses these rules:

- `PASS`: the sensor was detected and returned one usable sample
- `WARN`: the sensor returned a usable sample, but a broad sanity check looked suspicious
- `FAIL`: the sensor was missing, unreadable, timed out, or failed identity or CRC checks

Soft warnings do not fail the whole board by themselves.

Examples of warnings:

- pressure outside a broad normal range
- humidity that had to be clamped back into `0..100 %RH`
- light sensor sample where every channel is zero

## How To Run

1. Copy `board_sensors.py` and `main.py` to the board filesystem.
2. Place `main.py` at the board root as `/main.py`.
3. Reset the board.
4. Open the USB serial COM port used by the MicroPython REPL.

Example upload commands from the repository root:

```cmd
.\micropython-esp32c3-tools\mpremote_esp32c3.cmd connect COM4 fs cp ".\micropython example\board_sensor_self_test_demo\board_sensors.py" :board_sensors.py
.\micropython-esp32c3-tools\mpremote_esp32c3.cmd connect COM4 fs cp ".\micropython example\board_sensor_self_test_demo\main.py" :main.py
```

Replace `COM4` with your board's port.

## Expected Serial Output

You should see output shaped like this:

```text
MicroSense board sensor self-test demo
I2C: bus=0, SDA=GPIO6, SCL=GPIO7, freq=400000Hz
Expected onboard sensors:
  QMI8658A        0x6A
  QMC6309         0x7C
  SPA06-003       0x77
  SHT40           0x44
  LTR-381RGB-01   0x53
Detected I2C addresses: 0x44, 0x53, 0x6A, 0x77, 0x7C
Running startup checks...
PASS QMI8658A 0x6A id=0x05 temp=24.8C accel=(0.00,0.01,1.00) gyro=(0.1,0.0,-0.1)
PASS QMC6309 0x7C id=0x90 mag=(0.012,-0.006,0.421)G
PASS SPA06-003 0x77 id=0x11 temp=25.1C pressure=1008.54hPa
PASS SHT40 0x44 temp=24.7C humidity=46.8%RH
PASS LTR-381RGB-01 0x53 id=0xC2 ir=142 rgb=(231,198,167)
OVERALL: PASS
Live monitor: 5 sensor(s), update every 2000 ms
12ms QMI8658A temp=24.8C accel=(0.00,0.01,1.00) gyro=(0.1,0.0,-0.1) | QMC6309 mag=(0.012,-0.006,0.421)G | SPA06-003 temp=25.1C pressure=1008.54hPa | SHT40 temp=24.7C humidity=46.8%RH | LTR-381RGB-01 ir=142 rgb=(231,198,167)
```

## Success Looks Like

- The script starts and prints the expected sensor list.
- The I2C scan shows the expected onboard addresses.
- Each healthy onboard sensor reports `PASS`.
- The overall summary is `PASS` when all sensors are working.
- The live monitor continues printing compact sensor updates every two seconds.

If a sensor is damaged or missing, the demo should still continue and show the failure clearly in the startup summary.

## Notes And Limitations

- This demo only checks the five onboard sensors listed above.
- It does not test Wi-Fi, Bluetooth, USB data transfer, the boot button, or external header pins.
- It uses polling only and does not use the interrupt pins on `GPIO2`, `GPIO3`, or `GPIO4`.
- The `LTR-381RGB-01` demo output reports raw IR and RGB counts, not calibrated lux or color temperature.
- The `SPA06-003` pressure reading depends on local air pressure and environment, so only broad sanity checks are applied.
- The startup logic avoids interactive movement or light-change checks so the demo stays beginner-friendly and repeatable.
