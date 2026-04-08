# ESP32-C3 Station Wi-Fi GPIO8 LED And GPIO9 Button Web Demo

## Purpose

This MicroPython demo connects the ESP32-C3 board to a user-specified Wi-Fi access point in station mode and starts a tiny web server.

A phone on the same local network can then open the board IP address in a browser to:

- turn an external LED on `GPIO8` on and off
- view the current state of the boot button on `GPIO9`

## Target Board

- Custom ESP32-C3 development board in this repository

## Pin Assumptions

- LED output: `GPIO8`
- Button input: `GPIO9`
- `GPIO9` is the boot button and is wired active-low
- Pressed = `GPIO9` reads `0`
- Released = `GPIO9` reads `1`
- The demo defaults to active-low LED drive with `LED_ON_VALUE = 0`

## External LED Wiring

This demo is configured for an external LED wired active-low:

- `3V3` -> series resistor -> LED anode
- LED cathode -> `GPIO8`

With this wiring:

- LED on = `GPIO8` outputs `0`
- LED off = `GPIO8` outputs `1`

If your LED wiring is different, change `LED_ON_VALUE` in [main.py](D:\Projects\MicroSense\C3-Code_demos\micropython example\wifi_sta_gpio8_gpio9_web_demo\main.py).

## Wi-Fi Setup

The board joins your existing router instead of creating its own access point.

Set your Wi-Fi credentials in one of these ways:

1. Copy [wifi_config.example.py](D:\Projects\MicroSense\C3-Code_demos\micropython example\wifi_sta_gpio8_gpio9_web_demo\wifi_config.example.py) to `wifi_config.py` and edit the values.
2. Or edit `WIFI_SSID` and `WIFI_PASSWORD` directly in [main.py](D:\Projects\MicroSense\C3-Code_demos\micropython example\wifi_sta_gpio8_gpio9_web_demo\main.py).

Both the ESP32-C3 board and your phone must be connected to the same LAN.

## Files

- `main.py`: demo entry point
- `wifi_config.example.py`: optional Wi-Fi credentials template

## How To Run

1. Edit the Wi-Fi credentials.
2. Upload `main.py` to the board as `/main.py`.
3. If you use a separate config file, also upload `wifi_config.py` to the board root.
4. Reset the board.
5. Open the serial console and wait for the printed IP address.
6. Make sure your phone is connected to the same Wi-Fi router.
7. Browse to the printed URL from the phone.

Example upload commands:

```cmd
.\micropython-esp32c3-tools\mpremote_esp32c3.cmd connect COM4 fs cp ".\micropython example\wifi_sta_gpio8_gpio9_web_demo\main.py" :main.py
.\micropython-esp32c3-tools\mpremote_esp32c3.cmd connect COM4 fs cp ".\micropython example\wifi_sta_gpio8_gpio9_web_demo\wifi_config.py" :wifi_config.py
```

## Expected Serial Output

You should see lines similar to:

```text
Connecting to Wi-Fi SSID: YourRouter
ESP32-C3 STA Wi-Fi LED + button demo
Connected Wi-Fi SSID: YourRouter
Board IP address: 192.168.1.123
GPIO9 button is active-low
GPIO8 LED output defaults to OFF
Open this URL from a phone on the same LAN: http://192.168.1.123/
```

The serial console will also print button transitions and incoming web clients.

## Success Looks Like

- The ESP32-C3 connects to the target Wi-Fi network.
- The serial console prints a usable LAN IP address.
- A phone on the same router can load the webpage from that IP.
- The page updates between `Pressed` and `Released` when the GPIO9 button changes.
- The page can switch the external LED on `GPIO8` on and off.

## Notes And Limitations

- `GPIO9` is an ESP32-C3 strapping pin, so do not hold the button during reset or power-up unless you intentionally want bootloader-related behavior.
- This is a simple polling HTTP server for clarity and easy modification.
- The webpage polls `/status` every 500 ms, so button updates are near-real-time rather than interrupt-driven.
- If the board cannot join the Wi-Fi network, check the SSID, password, signal strength, and whether the router allows 2.4 GHz ESP32 clients.
