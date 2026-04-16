# MicroSense ESP32-C3 Code Demos

This repository collects small, practical demos for a custom ESP32-C3 development board with several onboard sensors. The current project focus is MicroPython: each demo is meant to be easy to upload, easy to understand, and easy to extend on real hardware.

The root README is the main entry point for the board, the local tooling, and the demo catalog. Each demo folder also includes its own README with run instructions and expected serial output.

## Board Photos

Add these images after you upload the board photos to GitHub:

![Board overview](docs/images/board-overview.jpg)
Suggested file: `docs/images/board-overview.jpg`

![Board top](docs/images/board-top.jpg)
Suggested file: `docs/images/board-top.jpg`

![Board bottom](docs/images/board-bottom.jpg)
Suggested file: `docs/images/board-bottom.jpg`

![Board ports and buttons](docs/images/board-ports.jpg)
Suggested file: `docs/images/board-ports.jpg`

## Board At A Glance

| Item | Details |
|---|---|
| MCU | ESP32-C3 |
| Main sensor bus | `SDA = GPIO6`, `SCL = GPIO7` |
| USB data | `D+ = GPIO19`, `D- = GPIO18` |
| UART header | `TXD = U0TXD`, `RXD = U0RXD` |
| Boot button | `GPIO9` |
| Reset | `EN` |
| Board references | [`Board Info/Development_Board_Pin_Connections.md`](Board%20Info/Development_Board_Pin_Connections.md), schematic PDF in [`Board Info/`](Board%20Info/) |

`GPIO9` is the ESP32-C3 boot and strapping pin. It can be used in special-case demos, but you should avoid holding it during reset or power-up unless you intentionally want bootloader-related behavior.

## Onboard Sensors

| Sensor | Purpose | Interface | Expected Address | Repo Reference |
|---|---|---|---|---|
| QMI8658A | 6-axis IMU: accelerometer + gyroscope + temperature | I2C on `GPIO6` / `GPIO7` | `0x6A` | [`Sensor Info/QMI8658A.md`](Sensor%20Info/QMI8658A.md) |
| QMC6309 | Magnetometer / compass | I2C on `GPIO6` / `GPIO7` | `0x7C` | [`Sensor Info/QMC6309.md`](Sensor%20Info/QMC6309.md) |
| SPA06-003 | Barometric pressure + temperature | I2C on `GPIO6` / `GPIO7` | `0x77` | [`Sensor Info/SPA06-003.md`](Sensor%20Info/SPA06-003.md) |
| SHT40 | Temperature + humidity | I2C on `GPIO6` / `GPIO7` | `0x44` | [`Sensor Info/SHT4x.md`](Sensor%20Info/SHT4x.md) |
| LTR-381RGB-01 | Ambient light, RGB color, IR | I2C on `GPIO6` / `GPIO7` | `0x53` | [`Sensor Info/LTR-381RGB-01.md`](Sensor%20Info/LTR-381RGB-01.md) |

## Repository Layout

| Path | What It Contains |
|---|---|
| [`Board Info/`](Board%20Info/) | Board-level hardware notes, schematic, and pin map |
| [`Sensor Info/`](Sensor%20Info/) | Sensor notes and datasheets used when building demos |
| [`micropython example/`](micropython%20example/) | Current MicroPython demos for the board |
| [`firmware/`](firmware/) | Included firmware assets for the board |
| [`micropython-esp32c3-tools/`](micropython-esp32c3-tools/) | Local compile and upload helpers for ESP32-C3 MicroPython workflows |
| [`esptool/`](esptool/) | Local `esptool` installation for ESP flashing |

## Prerequisites

- The custom ESP32-C3 development board from this repository
- A USB cable and a working serial or REPL connection to the board
- MicroPython running on the board, or the included firmware ready to flash
- The local tools already included in this repo:
  - `esptool/bin/esptool.exe`
  - `micropython-esp32c3-tools/compile_esp32c3_mpy.cmd`
  - `micropython-esp32c3-tools/mpremote_esp32c3.cmd`
- For the Wi-Fi LED demos, an external LED on `GPIO8` with an appropriate resistor

## Quick Start

1. Flash or verify MicroPython on the ESP32-C3 board if needed.
2. Make sure the board is booting normally and is not being held in bootloader mode.
3. Choose a demo under [`micropython example/`](micropython%20example/).
4. Upload the demo's `main.py` and any helper files with the local `mpremote` wrapper.
5. Reset the board.
6. Open the serial console and follow the demo-specific README.

### Flash MicroPython

The repository includes this firmware image:

- [`firmware/micropython-esp32c3/ESP32_GENERIC_C3-20251209-v1.27.0.bin`](firmware/micropython-esp32c3/ESP32_GENERIC_C3-20251209-v1.27.0.bin)

Typical flash command for the included single-binary ESP32-C3 MicroPython image:

```powershell
.\esptool\bin\esptool.exe --chip esp32c3 --port COM4 --baud 460800 write_flash -z 0x0 .\firmware\micropython-esp32c3\ESP32_GENERIC_C3-20251209-v1.27.0.bin
```

Replace `COM4` with your board's port. If you connected the board while holding `BOOT`, release `BOOT` and tap `EN` before trying to run demos normally.

### Optional: Compile A Demo To `.mpy`

```cmd
.\micropython-esp32c3-tools\compile_esp32c3_mpy.cmd ".\micropython example\qmi8658a_full_read_gyro_usb_demo\main.py"
```

### Upload A Demo With `mpremote`

```cmd
.\micropython-esp32c3-tools\mpremote_esp32c3.cmd connect COM4 fs cp ".\micropython example\qmi8658a_full_read_gyro_usb_demo\main.py" :main.py
```

For demos with helper modules, upload those files as well before resetting the board.

## Available Demos

| Demo | Capability | Extra Hardware | Network Mode | Notes |
|---|---|---|---|---|
| [`bluetooth_gpio9_slideshow_remote_demo`](micropython%20example/bluetooth_gpio9_slideshow_remote_demo/README.md) | BLE HID slideshow remote using the onboard button | No extra hardware | BLE | Requires MicroPython firmware with Bluetooth support; uses `GPIO9` |
| [`qmi8658a_full_read_gyro_usb_demo`](micropython%20example/qmi8658a_full_read_gyro_usb_demo/README.md) | Reads the onboard QMI8658A IMU and prints gyro data over USB serial | No extra hardware | None | Good starting point for sensor bring-up on the shared I2C bus |
| [`wifi_gpio9_web_demo`](micropython%20example/wifi_gpio9_web_demo/README.md) | Starts a Wi-Fi access point with a browser UI for button state and LED control | External LED on `GPIO8` | Access point | Assumes active-low LED wiring and uses `GPIO9` |
| [`wifi_sta_gpio8_gpio9_web_demo`](micropython%20example/wifi_sta_gpio8_gpio9_web_demo/README.md) | Joins an existing Wi-Fi network and serves a browser UI for LED and button state | External LED on `GPIO8` | Station | Requires `wifi_config.py` and a phone or PC on the same LAN |

## How To Use The Demos

1. Open the README inside the demo folder you want to run.
2. Upload the demo's `main.py` to the board root as `/main.py`.
3. Upload any helper files the demo needs, such as `ble_hid_keyboard.py` or `wifi_config.py`.
4. Reset the board and watch the serial output.
5. Compare what you see against the demo README's expected output and success criteria.

Special requirements to keep in mind:

- The BLE slideshow demo needs firmware with MicroPython BLE support enabled.
- The station-mode Wi-Fi demo expects a valid `wifi_config.py` on the board.
- Both Wi-Fi LED demos assume an external LED is connected to `GPIO8`.
- Demos that use `GPIO9` are intentionally special-case examples because `GPIO9` is also the boot button.

## Project Notes And Troubleshooting

- `GPIO9` is the ESP32-C3 boot pin. Avoid holding it during reset or power-up unless you want bootloader behavior.
- If a demo does not start, first confirm the board presents a normal MicroPython REPL on its COM port.
- If upload commands fail, verify the COM port name and that no other serial tool is currently connected.
- The BLE demo depends on a firmware build that includes the `bluetooth` module.
- The AP-mode Wi-Fi demo creates its own network; the STA-mode Wi-Fi demo joins your existing router instead.
- The Wi-Fi LED demos assume active-low LED wiring on `GPIO8`. If your LED wiring is inverted, adjust `LED_ON_VALUE` in the demo.
- Most sensors share the same I2C bus on `GPIO6` and `GPIO7`, so start with the documented board pin map before changing bus pins in code.

## Contributing

Contributions are welcome, especially small demos that help validate a single board feature or sensor clearly.

When adding or updating demos in this repository:

- Prefer MicroPython unless there is a strong reason to use another framework.
- Put new demos under [`micropython example/`](micropython%20example/) unless the task explicitly calls for something else.
- Keep each demo small, readable, and focused on one clear use case.
- Include an obvious entry point such as `main.py`.
- Add a demo-local `README.md` that explains:
  - the demo purpose
  - the target board and sensor
  - pin assumptions
  - expected I2C address or interface mode
  - how to run it
  - what success looks like on the serial console
  - limitations, assumptions, or next steps
- Reuse facts from [`Board Info/`](Board%20Info/) and [`Sensor Info/`](Sensor%20Info/) instead of inventing hardware details.
- Keep initialization explicit and easy to debug over serial logs.
- Prefer simple polling first; use interrupts only when they clearly improve the demo.

## Recommended References

- Board pin map: [`Board Info/Development_Board_Pin_Connections.md`](Board%20Info/Development_Board_Pin_Connections.md)
- Sensor notes: [`Sensor Info/`](Sensor%20Info/)
- Demo source and per-demo docs: [`micropython example/`](micropython%20example/)
- Firmware image: [`firmware/micropython-esp32c3/`](firmware/micropython-esp32c3/)
- Compile and upload helpers: [`micropython-esp32c3-tools/`](micropython-esp32c3-tools/)

## Current Gaps

- Board images are referenced above as placeholders and should be uploaded later to `docs/images/`.
- The repository does not currently include a top-level `CONTRIBUTING.md` or `LICENSE` file, so contribution guidance lives here for now.
