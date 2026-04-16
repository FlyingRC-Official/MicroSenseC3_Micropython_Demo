from micropython import const
import bluetooth
import struct
import time


_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

_ADV_INTERVAL_US = const(500000)
_APPEARANCE_KEYBOARD = const(961)
_REPORT_ID = const(1)
_REPORT_TYPE_INPUT = const(1)

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x03)
_ADV_TYPE_APPEARANCE = const(0x19)

_ADV_FLAGS = const(0x06)

_SERVICE_UUID_HID = bluetooth.UUID(0x1812)
_CHAR_UUID_HID_INFORMATION = bluetooth.UUID(0x2A4A)
_CHAR_UUID_REPORT_MAP = bluetooth.UUID(0x2A4B)
_CHAR_UUID_HID_CONTROL_POINT = bluetooth.UUID(0x2A4C)
_CHAR_UUID_REPORT = bluetooth.UUID(0x2A4D)
_CHAR_UUID_PROTOCOL_MODE = bluetooth.UUID(0x2A4E)
_DESC_UUID_REPORT_REFERENCE = bluetooth.UUID(0x2908)

_REPORT_MAP = bytes(
    (
        0x05,
        0x01,
        0x09,
        0x06,
        0xA1,
        0x01,
        0x85,
        _REPORT_ID,
        0x05,
        0x07,
        0x19,
        0xE0,
        0x29,
        0xE7,
        0x15,
        0x00,
        0x25,
        0x01,
        0x75,
        0x01,
        0x95,
        0x08,
        0x81,
        0x02,
        0x95,
        0x01,
        0x75,
        0x08,
        0x81,
        0x01,
        0x95,
        0x06,
        0x75,
        0x08,
        0x15,
        0x00,
        0x25,
        0x65,
        0x05,
        0x07,
        0x19,
        0x00,
        0x29,
        0x65,
        0x81,
        0x00,
        0xC0,
    )
)

_HID_INFORMATION = struct.pack("<HBB", 0x0111, 0x00, 0x03)
_PROTOCOL_MODE_REPORT = b"\x01"
_CONTROL_POINT_SUSPEND_OFF = b"\x00"
_REPORT_REFERENCE_INPUT = struct.pack("<BB", _REPORT_ID, _REPORT_TYPE_INPUT)
_KEY_RELEASE_DELAY_MS = const(20)

_CHAR_REPORT = (
    _CHAR_UUID_REPORT,
    bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,
    ((_DESC_UUID_REPORT_REFERENCE, bluetooth.FLAG_READ),),
)
_SERVICE_HID = (
    _SERVICE_UUID_HID,
    (
        (_CHAR_UUID_HID_INFORMATION, bluetooth.FLAG_READ),
        (_CHAR_UUID_REPORT_MAP, bluetooth.FLAG_READ),
        (_CHAR_UUID_HID_CONTROL_POINT, bluetooth.FLAG_WRITE_NO_RESPONSE),
        (_CHAR_UUID_PROTOCOL_MODE, bluetooth.FLAG_READ | bluetooth.FLAG_WRITE_NO_RESPONSE),
        _CHAR_REPORT,
    ),
)


def _append_advertising_field(payload, adv_type, value):
    payload.extend(struct.pack("BB", len(value) + 1, adv_type))
    payload.extend(value)


def _build_advertising_payload(
    name=None,
    include_name=True,
    include_flags=True,
    include_service=True,
    include_appearance=True,
):
    payload = bytearray()
    if include_flags:
        _append_advertising_field(payload, _ADV_TYPE_FLAGS, bytes((_ADV_FLAGS,)))
    if include_name and name is not None:
        _append_advertising_field(payload, _ADV_TYPE_NAME, name.encode("utf-8"))
    if include_service:
        _append_advertising_field(
            payload, _ADV_TYPE_UUID16_COMPLETE, struct.pack("<H", 0x1812)
        )
    if include_appearance:
        _append_advertising_field(
            payload, _ADV_TYPE_APPEARANCE, struct.pack("<H", _APPEARANCE_KEYBOARD)
        )
    return payload


def _format_addr(addr):
    return ":".join("%02X" % value for value in bytes(addr))


class BleHidKeyboard:
    def __init__(self, device_name, status_callback=None):
        self._device_name = device_name
        self._status_callback = status_callback
        self._ble = bluetooth.BLE()
        self._ble.irq(self._irq)
        self._conn_handle = None
        self._advertising = False
        self._started = False
        self._advertising_payload = _build_advertising_payload(include_name=False)
        self._scan_response_payload = _build_advertising_payload(
            device_name,
            include_name=True,
            include_flags=False,
            include_service=False,
            include_appearance=False,
        )
        self._report = bytearray((0, 0, 0, 0, 0, 0, 0, 0))

        self._hid_info_handle = None
        self._report_map_handle = None
        self._control_point_handle = None
        self._protocol_mode_handle = None
        self._report_handle = None
        self._report_reference_handle = None

    def _log(self, message):
        if self._status_callback is not None:
            self._status_callback(message)

    def _register_services(self):
        (
            (
                self._hid_info_handle,
                self._report_map_handle,
                self._control_point_handle,
                self._protocol_mode_handle,
                self._report_handle,
                self._report_reference_handle,
            ),
        ) = self._ble.gatts_register_services((_SERVICE_HID,))

        self._ble.gatts_write(self._hid_info_handle, _HID_INFORMATION)
        self._ble.gatts_write(self._report_map_handle, _REPORT_MAP)
        self._ble.gatts_write(self._control_point_handle, _CONTROL_POINT_SUSPEND_OFF)
        self._ble.gatts_write(self._protocol_mode_handle, _PROTOCOL_MODE_REPORT)
        self._ble.gatts_write(self._report_handle, self._report)
        self._ble.gatts_write(self._report_reference_handle, _REPORT_REFERENCE_INPUT)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._conn_handle = conn_handle
            self._advertising = False
            self._log(
                "BLE central connected: addr_type=%d addr=%s"
                % (addr_type, _format_addr(addr))
            )
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            if conn_handle == self._conn_handle:
                self._conn_handle = None
            self._advertising = False
            self._log(
                "BLE central disconnected: addr_type=%d addr=%s"
                % (addr_type, _format_addr(addr))
            )

    def _advertise(self):
        self._ble.gap_advertise(
            _ADV_INTERVAL_US,
            adv_data=self._advertising_payload,
            resp_data=self._scan_response_payload,
        )
        self._advertising = True
        self._log(
            "BLE advertising started: name=%s appearance=keyboard"
            % self._device_name
        )

    def start(self):
        if self._started:
            self.tick()
            return

        self._ble.active(True)
        self._ble.config(gap_name=self._device_name)
        self._ble.config(bond=True)
        self._ble.config(le_secure=True)
        self._register_services()
        self._advertise()
        self._started = True

    def is_connected(self):
        return self._conn_handle is not None

    def send_key(self, keycode):
        if self._conn_handle is None:
            return False

        self._report[0] = 0
        self._report[1] = 0
        self._report[2] = keycode
        self._report[3] = 0
        self._report[4] = 0
        self._report[5] = 0
        self._report[6] = 0
        self._report[7] = 0
        self._ble.gatts_write(self._report_handle, self._report)
        self._ble.gatts_notify(self._conn_handle, self._report_handle, self._report)

        time.sleep_ms(_KEY_RELEASE_DELAY_MS)

        self._report[0] = 0
        self._report[1] = 0
        self._report[2] = 0
        self._report[3] = 0
        self._report[4] = 0
        self._report[5] = 0
        self._report[6] = 0
        self._report[7] = 0
        self._ble.gatts_write(self._report_handle, self._report)
        self._ble.gatts_notify(self._conn_handle, self._report_handle, self._report)
        return True

    def tick(self):
        if self._conn_handle is None and not self._advertising:
            self._advertise()
