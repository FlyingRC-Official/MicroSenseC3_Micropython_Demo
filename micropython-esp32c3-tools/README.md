# MicroPython ESP32-C3 Tools

This folder contains a local `mpy-cross` setup for compiling MicroPython `.py` files into `.mpy` files intended for the ESP32-C3 board used in this repository.

Installed compiler version:

- `mpy-cross` `1.27.0.post2`

Important note:

- `.mpy` files must be compatible with the MicroPython firmware version running on the ESP32-C3 board

Compile a script from the repository root with:

```cmd
.\micropython-esp32c3-tools\compile_esp32c3_mpy.cmd ".\micropython example\qmi8658a_usb_serial_demo.py"
```

This will generate:

```text
.\micropython example\qmi8658a_usb_serial_demo.mpy
```