# AI Instructions For Code Demo Development

This repository is for developing small, practical code demos for a custom ESP32-C3 development board with several onboard sensors.

AI coding tools such as Codex should follow these instructions when creating or modifying demos in this workspace.

## 1. Primary goal

Create demos that are:

- Easy to run on the target board
- Focused on one clear hardware capability or sensor use case
- Small, readable, and well-commented
- Safe to test incrementally
- Easy for a human developer to extend

Prefer working demos over broad frameworks.

## 2. Repository layout

- `Board Info/` contains board-level hardware references
- `Sensor Info/` contains sensor-specific notes and datasheets
- `micropython example/` is the default location for MicroPython demos

When adding a new demo, put it in a clearly named folder under `micropython example/` unless the user explicitly asks for a different language or framework.

Recommended demo folder structure:

- `main.py` or another obvious entry file
- `README.md`
- Optional small helper modules if they improve clarity

Do not create unnecessary build systems, package managers, or large scaffolding for simple demos.

## 3. Hardware assumptions

Before writing board-facing code, use these local references:

- `Board Info/Development_Board_Pin_Connections.md`
- Relevant files in `Sensor Info/*.md`

Current board wiring summary:

- Main sensor bus: `SDA = GPIO6`, `SCL = GPIO7`
- USB: `D+ = GPIO19`, `D- = GPIO18`
- UART header: `TXD = U0TXD`, `RXD = U0RXD`
- QMI8658 interrupts: `GPIO2`, `GPIO3`
- LTR-381 interrupt: `GPIO4`
- SPA06 extra pin: `GPIO5`
- Boot button uses `GPIO9`
- Reset uses `EN`

Treat `GPIO9` as a sensitive boot/strapping pin. Avoid using it for normal demo behavior unless the user explicitly asks for that.

## 4. Default development approach

Unless the user requests otherwise:

- Prefer MicroPython demos
- Prefer direct, dependency-light code
- Use polling first, then interrupts only when they add real value
- Keep initialization explicit rather than overly abstract
- Print useful runtime status to the serial console

For sensor demos:

- Start with bus scan or device identity check when practical
- Verify the expected device address
- Read a simple identification or status register first
- Then add measurement logic
- Convert raw values into human-meaningful units when possible

## 5. Demo quality bar

Each demo should try to include:

- Clear setup section with pin definitions and constants
- Basic device detection or sanity check
- Simple error handling with readable messages
- A straightforward main loop
- Short comments for non-obvious register operations
- A README that explains what the demo does and how to run it

If a demo depends on assumptions that are not verified, state them clearly in the README.

## 6. Code style

Write code that is:

- Short
- Explicit
- Easy to debug over serial logs
- Friendly to beginners

Prefer:

- Descriptive variable names
- Small functions
- Constants for register addresses and configuration values
- Simple control flow

Avoid:

- Large class hierarchies for tiny demos
- Premature optimization
- Hidden magic values
- Over-generalized hardware abstraction layers unless requested

## 7. README expectations

Each new demo README should include:

- Purpose of the demo
- Target board and sensor used
- Pin assumptions
- Expected I2C address or interface mode
- How to run it
- What success looks like on the serial console
- Known limitations or next steps

## 8. When information is missing

If hardware details are unclear:

- First check `Board Info/`
- Then check the matching `Sensor Info/` markdown
- Prefer local repo documentation over guesswork

If something is still ambiguous, make the smallest reasonable assumption and state it in code comments or README notes.

## 9. Editing rules for AI tools

- Do not delete or rewrite unrelated files
- Keep changes scoped to the requested demo
- Reuse existing local documentation instead of inventing new hardware facts
- If adding a driver stub, keep it minimal and focused on the specific demo
- If a full driver is not necessary, do not build one

## 10. Good demo examples

Good demo tasks include:

- Scan the I2C bus and report detected devices
- Read accelerometer and gyroscope data from QMI8658
- Read temperature and humidity from SHT4x
- Read pressure data from SPA06
- Read light/color data from LTR-381
- Combine two sensors in one small data-reporting script

## 11. Final output expectations

When finishing a demo task, the AI tool should leave behind:

- Working code in the appropriate demo folder
- A short README
- Brief notes about assumptions, limitations, or unverified behavior

Favor simple demos that run today over ambitious demos that are hard to validate.

## 12. Local tooling

Local ESP flashing tooling is installed in this workspace:

- `esptool/` contains a local `esptool` installation
- Main executable: `esptool/bin/esptool.exe`

To run it from the repository root, use:

```powershell
.\esptool\bin\esptool.exe version
```

## 13. ESP32-C3 MicroPython compile tooling

Local MicroPython bytecode tooling for the ESP32-C3 board is installed in this workspace:

- `micropython-esp32c3-tools/` contains a local `mpy-cross` setup for compiling `.py` to `.mpy`
- Wrapper scripts: `micropython-esp32c3-tools/compile_esp32c3_mpy.cmd` and `micropython-esp32c3-tools/compile_esp32c3_mpy.ps1`

Compile a MicroPython demo from the repository root with:

```powershell
.\\micropython-esp32c3-tools\\compile_esp32c3_mpy.cmd ".\\micropython example\\qmi8658a_usb_serial_demo.py"
```


## 14. ESP32-C3 MicroPython upload and run process

Local upload tooling for the ESP32-C3 board is installed in this workspace:

- `micropython-esp32c3-tools/mpremote-local/` contains a local `mpremote` installation
- Wrapper script: `micropython-esp32c3-tools/mpremote_esp32c3.cmd`

Recommended workflow for MicroPython demos:

1. Compile the script to `.mpy` when useful:

```cmd
.\micropython-esp32c3-tools\compile_esp32c3_mpy.cmd ".\micropython example\your_demo\main.py"
```

2. Make sure the ESP32-C3 board is running MicroPython normally and is not held in bootloader mode. If the board was connected while holding `BOOT`, release `BOOT` and tap `EN` before trying to upload.

3. Check that the board presents a MicroPython REPL on its COM port.

4. Upload the demo entry file as `main.py`:

```cmd
.\micropython-esp32c3-tools\mpremote_esp32c3.cmd connect COM4 fs cp ".\micropython example\wifi_gpio9_web_demo\main.py" :main.py
```

5. Reset the board and watch the serial output to confirm startup.

For the validated Wi-Fi demo in this repository, the board printed:

- `ESP32-C3 Wi-Fi button demo`
- `Access point SSID: MicroSense-C3-Button`
- `Access point password: microsense`
- `Connect your phone and open: http://192.168.4.1/`

If a demo uses `GPIO9`, remember that it is the ESP32-C3 boot/strapping pin and should be treated as a special-case demo rather than a general default pattern.
