# ESP32-C3 BLE GPIO9 Slideshow Remote Demo

## Purpose

This MicroPython demo turns the ESP32-C3 board into a Bluetooth Low Energy HID keyboard remote for laptop presentations.

It uses the on-board button on `GPIO9` like this:

- one short press goes to the next slide
- one double press goes to the previous slide

The demo is designed for presentation software that accepts standard keyboard arrow keys, including PowerPoint, Google Slides, Keynote, and many PDF viewers.

## Target Board

- Custom ESP32-C3 development board in this repository

## Pin Assumptions

- Button input: `GPIO9`
- `GPIO9` is the boot button and is wired active-low
- Pressed = `GPIO9` reads `0`
- Released = `GPIO9` reads `1`

## Bluetooth Behavior

- BLE device name: `MicroSense-C3-Slides`
- BLE role: peripheral
- BLE profile style: HID keyboard
- Appearance: keyboard
- Default next-slide key: Right Arrow (`0x4F`)
- Default previous-slide key: Left Arrow (`0x50`)

The single-press action is intentionally delayed by the double-press window so the demo can decide whether to send next or previous without accidentally sending both.

## Files

- `main.py`: slideshow button logic and demo entry point
- `ble_hid_keyboard.py`: minimal local BLE HID keyboard helper

## Firmware Prerequisite

This demo assumes the ESP32-C3 firmware includes MicroPython's built-in `bluetooth` module with BLE support.

The repository currently includes:

- [ESP32_GENERIC_C3-20251209-v1.27.0.bin](D:\Projects\MicroSense\C3-Code_demos\firmware\micropython-esp32c3\ESP32_GENERIC_C3-20251209-v1.27.0.bin)

If the board prints a message about missing Bluetooth support, flash a BLE-capable ESP32-C3 MicroPython firmware build before retrying this demo.

## How To Run

1. Upload `main.py` and `ble_hid_keyboard.py` to the board filesystem.
2. Place `main.py` at the board root as `/main.py`.
3. Reset the board.
4. Open the serial console and wait for the BLE startup messages.
5. On your laptop, open the Bluetooth settings screen and pair with `MicroSense-C3-Slides`.
6. Open your slideshow or PDF presentation.
7. Press `GPIO9` once for next slide, or double press for previous slide.

Example upload commands:

```cmd
.\micropython-esp32c3-tools\mpremote_esp32c3.cmd connect COM4 fs cp ".\micropython example\bluetooth_gpio9_slideshow_remote_demo\ble_hid_keyboard.py" :ble_hid_keyboard.py
.\micropython-esp32c3-tools\mpremote_esp32c3.cmd connect COM4 fs cp ".\micropython example\bluetooth_gpio9_slideshow_remote_demo\main.py" :main.py
```

If you want compiled bytecode files instead, upload the matching `.mpy` files after compiling them with the local tooling.

## Expected Serial Output

You should see lines similar to:

```text
BLE advertising started: name=MicroSense-C3-Slides appearance=keyboard
ESP32-C3 BLE slideshow remote demo
BLE device name: MicroSense-C3-Slides
GPIO9 button is active-low
Single press sends next slide after 300 ms
Double press sends previous slide
Pair your laptop with MicroSense-C3-Slides over Bluetooth, then use the GPIO9 button.
BLE central connected: addr_type=0 addr=AA:BB:CC:DD:EE:FF
BLE host is now connected
GPIO9 single press candidate detected
Slide action sent: next slide
Slide action sent: previous slide
```

## Success Looks Like

- The ESP32-C3 starts BLE advertising after reset.
- A laptop can discover and pair with `MicroSense-C3-Slides`.
- A short single press on `GPIO9` advances the presentation by one slide.
- A quick double press on `GPIO9` moves back by one slide.
- Holding the button does not auto-repeat slide actions.
- Disconnecting and reconnecting the laptop resumes control without reflashing.

## Notes And Limitations

- `GPIO9` is an ESP32-C3 strapping pin, so do not hold the button during reset or power-up unless you intentionally want bootloader-related behavior.
- The default single-press action waits for the double-press window to expire before sending next slide.
- Different host operating systems may display the device as a keyboard or generic input accessory during pairing.
- Presentation apps with custom key bindings may need different HID keycodes. Edit `NEXT_SLIDE_KEYCODE` and `PREVIOUS_SLIDE_KEYCODE` in [main.py](D:\Projects\MicroSense\C3-Code_demos\micropython example\bluetooth_gpio9_slideshow_remote_demo\main.py) if needed.
