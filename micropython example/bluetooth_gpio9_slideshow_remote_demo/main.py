from machine import Pin
import sys
import time


BUTTON_PIN = 9
BUTTON_PRESSED_VALUE = 0
POLL_INTERVAL_MS = 10
DEBOUNCE_MS = 30
DOUBLE_PRESS_WINDOW_MS = 300
STARTUP_IGNORE_MS = 800
BLE_DEVICE_NAME = "MicroSense-C3-Slides"

# HID keyboard usage IDs for the arrow keys.
NEXT_SLIDE_KEYCODE = 0x4F
PREVIOUS_SLIDE_KEYCODE = 0x50


try:
    from ble_hid_keyboard import BleHidKeyboard
except Exception as exc:
    BleHidKeyboard = None
    BLE_IMPORT_ERROR = exc
else:
    BLE_IMPORT_ERROR = None


button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)


def log_message(message):
    print(message)
    if hasattr(sys.stdout, "flush"):
        sys.stdout.flush()


def button_pressed():
    return button.value() == BUTTON_PRESSED_VALUE


def print_startup():
    log_message("ESP32-C3 BLE slideshow remote demo")
    log_message("BLE device name: %s" % BLE_DEVICE_NAME)
    log_message("GPIO9 button is active-low")
    log_message(
        "Single press sends next slide after %d ms"
        % DOUBLE_PRESS_WINDOW_MS
    )
    log_message("Double press sends previous slide")
    log_message("Next slide keycode: 0x%02X" % NEXT_SLIDE_KEYCODE)
    log_message("Previous slide keycode: 0x%02X" % PREVIOUS_SLIDE_KEYCODE)
    log_message(
        "Startup button ignore window: %d ms on GPIO9" % STARTUP_IGNORE_MS
    )
    log_message(
        "Pair your laptop with %s over Bluetooth, then use the GPIO9 button."
        % BLE_DEVICE_NAME
    )


def send_slide_action(remote, keycode, action_name):
    if remote.send_key(keycode):
        log_message("Slide action sent: %s" % action_name)
        return

    log_message("Slide action skipped: %s (BLE host not connected)" % action_name)


def completed_press_event(pressed, state):
    now = time.ticks_ms()

    if pressed != state["raw_pressed"]:
        state["raw_pressed"] = pressed
        state["raw_changed_at"] = now

    if time.ticks_diff(now, state["raw_changed_at"]) < DEBOUNCE_MS:
        return False

    if pressed == state["stable_pressed"]:
        return False

    state["stable_pressed"] = pressed
    return not pressed


def main():
    if BleHidKeyboard is None:
        raise RuntimeError(
            "Bluetooth HID helper unavailable: %s" % BLE_IMPORT_ERROR
        )

    remote = BleHidKeyboard(BLE_DEVICE_NAME, status_callback=log_message)
    remote.start()
    print_startup()

    state = {
        "raw_pressed": button_pressed(),
        "stable_pressed": button_pressed(),
        "raw_changed_at": time.ticks_ms(),
    }
    startup_deadline = time.ticks_add(time.ticks_ms(), STARTUP_IGNORE_MS)
    pending_single_press = False
    pending_single_deadline = 0
    last_connection_state = remote.is_connected()

    if state["stable_pressed"]:
        log_message("GPIO9 button is already pressed at startup")

    while True:
        remote.tick()

        connected = remote.is_connected()
        if connected != last_connection_state:
            log_message(
                "BLE host is now %s"
                % ("connected" if connected else "disconnected")
            )
            last_connection_state = connected

        now = time.ticks_ms()
        pressed = button_pressed()

        if completed_press_event(pressed, state):
            if time.ticks_diff(now, startup_deadline) < 0:
                log_message("GPIO9 release ignored during startup grace period")
            elif pending_single_press and time.ticks_diff(
                now, pending_single_deadline
            ) <= 0:
                pending_single_press = False
                send_slide_action(remote, PREVIOUS_SLIDE_KEYCODE, "previous slide")
            else:
                pending_single_press = True
                pending_single_deadline = time.ticks_add(
                    now, DOUBLE_PRESS_WINDOW_MS
                )
                log_message("GPIO9 single press candidate detected")

        if pending_single_press and time.ticks_diff(now, pending_single_deadline) >= 0:
            pending_single_press = False
            send_slide_action(remote, NEXT_SLIDE_KEYCODE, "next slide")

        time.sleep_ms(POLL_INTERVAL_MS)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log_message("Demo stopped: %s" % exc)
        log_message(
            "If Bluetooth support is missing, flash a BLE-capable ESP32-C3 "
            "MicroPython firmware build and try again."
        )
