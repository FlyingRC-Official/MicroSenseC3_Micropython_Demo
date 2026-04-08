# ESP32-C3 Wi-Fi Button And GPIO8 LED Demo

## Purpose

This MicroPython demo turns the ESP32-C3 board into a small Wi-Fi access point and serves a webpage that both:

- shows whether the on-board button connected to `GPIO9` is currently pressed
- lets the user turn an external LED on `GPIO8` on and off from the browser

The intended flow is:

1. Power the board.
2. Connect a phone or laptop to the ESP32-C3 Wi-Fi network.
3. Open the board IP in a browser.
4. Press and release the button and watch the page update live.
5. Tap the webpage buttons to control the external LED on `GPIO8`.

## Target Board

- Custom ESP32-C3 development board in this repository

## Pin Assumptions

- Button input: `GPIO9`
- LED output: `GPIO8`
- `GPIO9` is the boot button and is wired active-low
- Pressed = `GPIO9` reads `0`
- Released = `GPIO9` reads `1`
- The demo currently defaults to active-low LED drive with `LED_ON_VALUE = 0`

## External LED Wiring

This demo is currently configured for an external LED that is wired active-low:

- `3V3` -> series resistor -> LED anode
- LED cathode -> `GPIO8`

With that wiring:

- LED on = `GPIO8` outputs `0`
- LED off = `GPIO8` outputs `1`

If your LED wiring is inverted, change `LED_ON_VALUE` in `main.py`.
The code now derives both the ON level and the OFF level from that setting, including the startup default.

## Wi-Fi Behavior

The demo starts the ESP32-C3 in access point mode with:

- SSID: `MicroSense-C3-Button`
- Password: `microsense`
- TX power: `8 dBm`
- Default AP address: usually `192.168.4.1`

If your firmware or environment uses a different AP address, check the serial console output and open the printed URL instead.
If you need to reduce heat or range further, lower `AP_TXPOWER_DBM` in `main.py`.

## Files

- `main.py`: demo entry point

## How To Run

1. Copy [main.py](D:\Projects\MicroSense\C3-Code_demos\micropython example\wifi_gpio9_web_demo\main.py) to the board as `/main.py`, or run it manually from the REPL.
2. Reset the board.
3. Open the serial console to see the AP credentials and URL.
4. Connect your phone to `MicroSense-C3-Button`.
5. Browse to the printed URL, usually `http://192.168.4.1/`.

## Expected Serial Output

You should see lines similar to:

```text
ESP32-C3 Wi-Fi button + LED demo
Access point SSID: MicroSense-C3-Button
Access point password: microsense
Access point tx power: 8 dBm
GPIO9 button is active-low
GPIO8 LED output defaults to OFF
Connect your phone and open: http://192.168.4.1/
```

When you press or release the button, or when the webpage changes the LED state, the serial console should also print state changes.

## Success Looks Like

- The ESP32-C3 creates a Wi-Fi network.
- A phone can connect to that network.
- The browser page loads from the ESP32-C3.
- The page changes between `Pressed` and `Released` when the GPIO9 button is used.
- The page can switch the external GPIO8 LED on and off.

## Notes And Limitations

- `GPIO9` is a strapping pin on the ESP32-C3, so do not hold the button during reset or power-up unless you intentionally want bootloader-related behavior.
- This demo uses a simple polling HTTP server for clarity rather than a more advanced async framework.
- The webpage polls `/status` every 500 ms, so button updates are near-real-time but not instantaneous.
