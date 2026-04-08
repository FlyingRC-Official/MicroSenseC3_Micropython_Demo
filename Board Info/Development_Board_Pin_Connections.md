# Development Board Pin Connections

Source schematic: `Schematic_ESP32C3-Mini-DevBRD-V1_2026-03-22.pdf`

## 1. Breakout headers

### H1 (`HX PZ1.27-1X10P ZZ`)

| Pin | Net | Notes |
|---|---|---|
| 1 | EN | Reset enable line, also tied to reset button |
| 2 | GPIO0 | Broken out only |
| 3 | GPIO1 | Broken out only |
| 4 | GPIO2 | QMI8658 `INT1` |
| 5 | GPIO3 | QMI8658 `INT2` |
| 6 | GPIO4 | LTR-381 `INT` |
| 7 | GPIO5 | SPA06 `SDO` / address-related pin |
| 8 | GPIO6 | Main sensor `SDA` bus |
| 9 | 5V | From USB VBUS through Schottky diode |
| 10 | GND | Ground |

### H2 (`HX PZ1.27-1X10P ZZ`)

| Pin | Net | Notes |
|---|---|---|
| 1 | TXD | ESP32-C3 `U0TXD` |
| 2 | RXD | ESP32-C3 `U0RXD` |
| 3 | GPIO19 | USB `D+` through 22 ohm resistor |
| 4 | GPIO18 | USB `D-` through 22 ohm resistor |
| 5 | GPIO10 | Broken out only |
| 6 | GPIO9 | Boot button / strapping pin |
| 7 | GPIO8 | Broken out only |
| 8 | GPIO7 | Main sensor `SCL` bus |
| 9 | 3V3 | Main 3.3 V rail |
| 10 | GND | Ground |

## 2. ESP32-C3 signal usage

| MCU net | Connected to |
|---|---|
| EN | Reset button, H1-1, 10 k pull-up to `3V3` |
| GPIO0 | H1-2 |
| GPIO1 | H1-3 |
| GPIO2 | H1-4, QMI8658 `INT1` |
| GPIO3 | H1-5, QMI8658 `INT2` |
| GPIO4 | H1-6, LTR-381 `INT` |
| GPIO5 | H1-7, SPA06 `SDO` |
| GPIO6 | H1-8, shared sensor `SDA` bus, 4.7 k pull-up to `3V3` |
| GPIO7 | H2-8, shared sensor `SCL` bus, 4.7 k pull-up to `3V3` |
| GPIO8 | H2-7 |
| GPIO9 | H2-6, boot button to GND, 10 k pull-up to `3V3` |
| GPIO10 | H2-5 |
| GPIO18 | H2-4, USB `D-` via 22 ohm series resistor |
| GPIO19 | H2-3, USB `D+` via 22 ohm series resistor |
| U0RXD / RXD | H2-2 |
| U0TXD / TXD | H2-1 |

## 3. On-board sensors

### Shared I2C-style bus

- `GPIO6` is the shared data line.
- `GPIO7` is the shared clock line.
- `R1` and `R8` are 4.7 k pull-ups from `GPIO6` and `GPIO7` to `3V3`.
- Most sensors are powered from `3V3_S`, which is derived from `3V3` through ferrite bead `L2`.

### QMI8658A IMU (`U4`)

| Sensor pin | MCU / rail |
|---|---|
| SDA | GPIO6 |
| SCL | GPIO7 |
| INT1 | GPIO2 |
| INT2 | GPIO3 |
| SDO/SA0 | `3V3_S` |
| CS | `3V3_S` |
| VDDIO, VDD | `3V3_S` |
| GND pins | GND |

Schematic note: address marked as `0x6A`.

### QMC6309 magnetometer (`U5`)

| Sensor pin | MCU / rail |
|---|---|
| SDA | GPIO6 |
| SCL | GPIO7 |
| VDD | `3V3_S` |
| VSS | GND |

Schematic note: address marked as `0x7C`.

### SPA06-003 pressure sensor (`U6`)

| Sensor pin | MCU / rail |
|---|---|
| SDA | GPIO6 |
| SCK / SCL | GPIO7 |
| SDO | GPIO5 |
| VDDIO, VDD | `3V3_S` |
| GND pins | GND |

Schematic note: address marked as `0x77`.

### SHT40 temperature / humidity sensor (`U8`)

| Sensor pin | MCU / rail |
|---|---|
| SDA | GPIO6 |
| SCL | GPIO7 |
| VDD | `3V3_S` |
| VSS | GND |

Schematic note: address marked as `0x44`.

### LTR-381RGB-01 light / color sensor (`U7`)

| Sensor pin | MCU / rail |
|---|---|
| SDA | GPIO6 |
| SCL | GPIO7 |
| INT | GPIO4 |
| VDD | `3V3_S` |
| GND | GND |

Schematic note: address marked as `0x53`.

## 4. USB, power, and buttons

### USB Type-C

- USB connector `USB1` routes `DP` to `GPIO19` through `R4` (22 ohm).
- USB connector `USB1` routes `DN` to `GPIO18` through `R5` (22 ohm).
- `CC1` and `CC2` each have a 5.1 k pull-down to GND (`R6`, `R7`).
- `VBUS` feeds the board `5V` net.

### Power tree

- `VBUS` passes through Schottky diode `D2` to create the `5V` rail.
- `U10` (`TLV76733DRVR`) regulates `5V` down to `3V3`.
- Ferrite bead `L2` filters `3V3` into `3V3_S` for the sensors.

### Buttons

- Boot button `U3` shorts `GPIO9` to GND when pressed.
- Reset button `U9` shorts `EN` to GND when pressed.
- `R2` is a 10 k pull-up on `EN`.
- `R3` is a 10 k pull-up on `GPIO9`.

## 5. Quick software-facing summary

- I2C bus: `SDA = GPIO6`, `SCL = GPIO7`
- USB: `D+ = GPIO19`, `D- = GPIO18`
- UART0: `TX = GPIO21 / U0TXD` exposed as `TXD`, `RX = GPIO20 / U0RXD` exposed as `RXD`
- IMU interrupts: `GPIO2`, `GPIO3`
- Light sensor interrupt: `GPIO4`
- Pressure sensor extra pin: `GPIO5`
