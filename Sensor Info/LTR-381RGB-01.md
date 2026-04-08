# LTR-381RGB-01 AI Coding Notes

## What this device is
LTR-381RGB-01 is a low-voltage I2C optical sensor that combines:
- Ambient Light Sensing (ALS)
- RGB color sensing
- IR channel measurement

It is intended for display brightness and color control in mobile, computing, and consumer devices.

## Core capabilities
- I2C interface: standard mode 100 kHz, fast mode 400 kHz
- Supply voltage: 1.7 V to 3.6 V
- Operating temperature: -40 C to +85 C
- Resolution: programmable from 16 to 20 bits
- Gain: programmable 1x, 3x, 6x, 9x, 18x
- Measurement/integration timing: 25 ms to 400 ms conversion window depending on resolution
- Automatic 50/60 Hz flicker rejection
- Very low standby current
- Interrupt output available

## Hardware integration notes
### Pins
1. `VDD` - supply
2. `NC` - do not connect
3. `GND`
4. `SCL` - open-drain I2C clock input
5. `INT` - open-drain interrupt output
6. `SDA` - open-drain I2C data

### Recommended external parts
- Pull-ups on SDA, SCL, and INT: `1k` to `10k`
- `C1 = 0.1uF`
- `C2 = 1uF`
- In noisy environments, optional `10pF` from signal to GND for noise filtering

## I2C basics
- 7-bit slave address: `0x53`
- Write address byte: `0xA6`
- Read address byte: `0xA7`
- Bus speed up to `400 kHz`

## Important registers
### Control and status
- `0x00` `MAIN_CTRL`
- `0x04` `ALS_CS_MEAS_RATE`
- `0x05` `ALS_CS_GAIN`
- `0x06` `PART_ID`
- `0x07` `MAIN_STATUS`

### Measurement data
- IR: `0x0A` `0x0B` `0x0C`
- Green / ALS: `0x0D` `0x0E` `0x0F`
- Red: `0x10` `0x11` `0x12`
- Blue: `0x13` `0x14` `0x15`

### Interrupt control
- `0x19` `INT_CFG`
- `0x1A` `INT_PST`
- Upper threshold: `0x21` `0x22` `0x23`
- Lower threshold: `0x24` `0x25` `0x26`

## Register details for coding
### `0x00 MAIN_CTRL`
Bits:
- Bit 4: software reset
- Bit 2: mode select
  - `0`: ALS mode
  - `1`: color-sensor mode
- Bit 1: enable
  - `0`: standby
  - `1`: active

Safe patterns:
- ALS mode active: `0x02`
- CS mode active: `0x06`
- Standby default: `0x00`

Important behavior:
- Writing this register stops ongoing measurement and starts a new one.

### `0x04 ALS_CS_MEAS_RATE`
Bits 6:4 = resolution:
- `000` => 20-bit, 400 ms
- `001` => 19-bit, 200 ms
- `010` => 18-bit, 100 ms
- `011` => 17-bit, 50 ms
- `100` => 16-bit, 25 ms

Bits 2:0 = measurement repeat rate:
- `000` => 25 ms
- `001` => 50 ms
- `010` => 100 ms
- `011` => 200 ms
- `100` => 500 ms
- `101` => 1000 ms
- `110/111` => 2000 ms

Note:
If repeat rate is set faster than the conversion can finish, the device slows to the maximum achievable speed.

### `0x05 ALS_CS_GAIN`
Bits 2:0:
- `000` => 1x
- `001` => 3x default
- `010` => 6x
- `011` => 9x
- `100` => 18x

### `0x06 PART_ID`
- Reset/default value: `0xC2`
- Part number ID is upper nibble
- Revision ID is lower nibble

Use this register during probe to confirm the device is present.

### `0x07 MAIN_STATUS`
Important bits:
- Bit 5: power-on flag
- Bit 4: interrupt status
- Bit 3: new-data flag

Behavior:
- Power-on flag clears after being read
- Interrupt flag clears after being read
- Data-new flag clears after being read

Practical polling rule:
- Read `MAIN_STATUS`
- If bit 3 is set, read the measurement registers

## Data format
Each channel is stored in 3 registers and represented as a 16- to 20-bit unsigned value.

Example for green:
- low byte at `0x0D`
- middle byte at `0x0E`
- high nibble at low nibble of `0x0F`

Recommended combine logic:
```c
uint32_t value = ((uint32_t)(data2 & 0x0F) << 16) |
                 ((uint32_t)data1 << 8) |
                 data0;
```

Apply the same pattern to IR, red, and blue.

### Read-group locking behavior
When reading addresses in `0x07` to `0x18`, the sensor locks the corresponding data registers until the I2C read operation finishes or leaves that range. This helps keep multi-byte channel data coherent.

Coding implication:
- Read each 3-byte channel as a contiguous group
- Better: read all status/data registers in one burst transaction if your driver supports it

## Interrupt behavior
- INT pin is active low
- Interrupt source is selectable through `INT_CFG`
- Source can be IR, green/ALS, blue, or red
- Threshold crossing must persist for N consecutive measurements based on `INT_PST`
- Interrupt status is mirrored into `MAIN_STATUS` bit 4
- Reading `MAIN_STATUS` clears the interrupt flag and also clears the INT pin condition

### `0x19 INT_CFG`
- Bits 5:4 select interrupt source
  - `00` IR
  - `01` Green / ALS default
  - `10` Blue
  - `11` Red
- Bit 2 enables interrupt pin

### `0x1A INT_PST`
Bits 7:4 define persistence count:
- `0000` => every out-of-range event triggers
- `0001` => 2 consecutive out-of-range measurements
- ...
- `1111` => 16 consecutive out-of-range measurements

## Device-operation notes
- After enabling measurement, internal support blocks power up first
- Settling time is typically about `5 ms`
- After that, scheduled conversions start
- Returning enable bit to `0` lets the current conversion finish, then powers down the measurement blocks

## Accuracy and performance notes
- Lux accuracy: about `+/-10%`
- Color temperature accuracy: about `+/-5%`
- Flicker noise error: about `+/-5%`
- Temperature dependency around `+/-0.25%/C` at 100 lux
- Voltage dependency around `+/-5%` at 100 lux

## Driver design recommendations
### Recommended init sequence
1. Power up sensor
2. Wait a few ms
3. Read `PART_ID` and verify `0xC2`
4. Write `ALS_CS_MEAS_RATE`
5. Write `ALS_CS_GAIN`
6. Write `MAIN_CTRL` to select mode and active state
7. Wait for first conversion or poll `MAIN_STATUS`
8. Read channel data

### Recommended software architecture
Implement these functions:
- `init()`
- `probe()`
- `set_mode_als()`
- `set_mode_color()`
- `set_gain(gain)`
- `set_resolution(bits)`
- `set_measurement_rate(ms)`
- `read_status()`
- `read_ir()`
- `read_green()`
- `read_red()`
- `read_blue()`
- `read_all_channels()`
- `configure_interrupt(source, persist, low, high)`
- `soft_reset()`
- `sleep()`
- `wake()`

### Defensive coding rules
- Always preserve reserved bits as required by the datasheet
- Only write documented encodings
- Read multi-byte channel registers in order from low to high
- Treat `MAIN_STATUS` as read-to-clear
- Expect stale data until new-data flag is set
- Clamp unsupported gain/resolution options in software
- Separate ALS mode and CS mode logic clearly

## Suggested register helpers
```c
#define LTR381_I2C_ADDR            0x53

#define LTR381_REG_MAIN_CTRL       0x00
#define LTR381_REG_MEAS_RATE       0x04
#define LTR381_REG_GAIN            0x05
#define LTR381_REG_PART_ID         0x06
#define LTR381_REG_MAIN_STATUS     0x07

#define LTR381_REG_IR_0            0x0A
#define LTR381_REG_IR_1            0x0B
#define LTR381_REG_IR_2            0x0C
#define LTR381_REG_GREEN_0         0x0D
#define LTR381_REG_GREEN_1         0x0E
#define LTR381_REG_GREEN_2         0x0F
#define LTR381_REG_RED_0           0x10
#define LTR381_REG_RED_1           0x11
#define LTR381_REG_RED_2           0x12
#define LTR381_REG_BLUE_0          0x13
#define LTR381_REG_BLUE_1          0x14
#define LTR381_REG_BLUE_2          0x15

#define LTR381_REG_INT_CFG         0x19
#define LTR381_REG_INT_PST         0x1A
#define LTR381_REG_THRES_UP_0      0x21
#define LTR381_REG_THRES_UP_1      0x22
#define LTR381_REG_THRES_UP_2      0x23
#define LTR381_REG_THRES_LOW_0     0x24
#define LTR381_REG_THRES_LOW_1     0x25
#define LTR381_REG_THRES_LOW_2     0x26
```

## Suggested status helpers
```c
#define LTR381_STATUS_POWER_ON     0x20
#define LTR381_STATUS_INT          0x10
#define LTR381_STATUS_NEW_DATA     0x08
```

## Suggested sample code skeleton
```c
bool ltr381_probe(i2c_bus_t *bus) {
    uint8_t id = 0;
    if (!i2c_read_reg(bus, LTR381_I2C_ADDR, LTR381_REG_PART_ID, &id, 1)) {
        return false;
    }
    return id == 0xC2;
}

bool ltr381_set_active_als(i2c_bus_t *bus) {
    uint8_t cmd = 0x02;
    return i2c_write_reg(bus, LTR381_I2C_ADDR, LTR381_REG_MAIN_CTRL, &cmd, 1);
}

bool ltr381_set_active_color(i2c_bus_t *bus) {
    uint8_t cmd = 0x06;
    return i2c_write_reg(bus, LTR381_I2C_ADDR, LTR381_REG_MAIN_CTRL, &cmd, 1);
}

bool ltr381_read_status(i2c_bus_t *bus, uint8_t *status) {
    return i2c_read_reg(bus, LTR381_I2C_ADDR, LTR381_REG_MAIN_STATUS, status, 1);
}

static uint32_t ltr381_unpack20(uint8_t low, uint8_t mid, uint8_t high) {
    return ((uint32_t)(high & 0x0F) << 16) | ((uint32_t)mid << 8) | low;
}

bool ltr381_read_green(i2c_bus_t *bus, uint32_t *out) {
    uint8_t d[3];
    if (!i2c_read_reg(bus, LTR381_I2C_ADDR, LTR381_REG_GREEN_0, d, 3)) {
        return false;
    }
    *out = ltr381_unpack20(d[0], d[1], d[2]);
    return true;
}
```

## Things not fully specified in the extracted notes
These should be confirmed directly in the full datasheet before final production driver work:
- Exact lux conversion formula to engineering lux units
- Exact color-temperature or XYZ conversion workflow
- Any recommended calibration strategy behind cover glass or window materials
- Full pseudo-code examples for all channels and interrupt threshold programming

## Practical summary for an AI coding assistant
When generating driver code for this part:
- Use I2C address `0x53`
- Probe `PART_ID == 0xC2`
- Configure `0x04` and `0x05`
- Enable ALS or color mode through `0x00`
- Poll `0x07` bit 3 for new data
- Read channel data as 3 bytes per channel and combine into a 20-bit unsigned integer
- Treat status bits as read-to-clear
- Use interrupt registers only if threshold-based wakeup is needed
- Never write to reserved registers or reserved bit patterns
