# SHT4x AI Coding Notes

## What this device is
SHT4x is a digital humidity and temperature sensor family. It uses a simple I2C command interface rather than a large register map. The family includes variants such as SHT40, SHT41, SHT43, and SHT45, with different accuracy grades and address options.

## Core capabilities
- Relative humidity + temperature sensing
- I2C interface
- Supply: 1.08 V to 3.6 V
- Operating range: 0 to 100 %RH, -40 C to 125 C
- Typical humidity accuracy:
  - SHT40 / SHT41 / SHT43: ±1.8 %RH typical
  - SHT45: ±1.0 %RH typical
- SHT45 temperature accuracy: ±0.1 C
- Average current: about `0.4 uA`
- Idle current: about `80 nA`
- Integrated heater with selectable power and duration
- CRC on read data
- No clock stretching support

## Hardware integration notes
### Pins
- `1` `SDA` - serial data
- `2` `SCL` - serial clock
- `3` `VDD` - supply
- `4` `VSS` - ground

### I2C addressing
Family-dependent:
- Some SHT40 variants support `0x44`, `0x45`, `0x46`
- SHT41 / SHT45 common variants use `0x44`

Practical rule:
- Confirm the exact suffix of your part number before hardcoding the I2C address.

## Timing basics
- Power-up time: up to `1 ms`
- Soft reset time: up to `1 ms`
- Measurement time:
  - low repeatability: up to `1.6 ms`
  - medium repeatability: up to `4.5 ms`
  - high repeatability: up to `8.3 ms`

Practical rule:
- Wait 10 ms after a high-precision measurement command if you want a very safe one-shot implementation.

## Interface model
Unlike register-based sensors, SHT4x works like this:
1. Send a single command byte
2. Wait until the conversion is done
3. Read response bytes
4. Verify CRC for each 16-bit value
5. Convert raw values to temperature and RH

## Command overview
### Basic measurement commands
- `0xFD` -> measure T & RH, high precision
- `0xF6` -> measure T & RH, medium precision
- `0xE0` -> measure T & RH, low precision

Each returns 6 bytes:
- temp MSB
- temp LSB
- temp CRC
- RH MSB
- RH LSB
- RH CRC

### Other important commands
- `0x89` -> read serial number
- `0x94` -> soft reset

### Heater commands
- `0x39` -> 200 mW for 1 s + high-precision measurement
- `0x32` -> 200 mW for 0.1 s + high-precision measurement
- `0x2F` -> 110 mW for 1 s + high-precision measurement
- `0x24` -> 110 mW for 0.1 s + high-precision measurement
- `0x1E` -> 20 mW for 1 s + high-precision measurement
- `0x15` -> 20 mW for 0.1 s + high-precision measurement

## Data format
Readout always comes as two 16-bit values with CRC:
- temperature word + CRC
- humidity word + CRC

### Conversion formulas
```c
float t_degC = -45.0f + 175.0f * ((float)raw_t / 65535.0f);
float rh_pct = -6.0f + 125.0f * ((float)raw_rh / 65535.0f);
```

The datasheet notes humidity can mathematically land outside `0..100 %RH`; it is usually best to clamp it.

```c
if (rh_pct < 0.0f) rh_pct = 0.0f;
if (rh_pct > 100.0f) rh_pct = 100.0f;
```

## CRC details
Every 16-bit data word is followed by 1 CRC byte.

CRC properties:
- CRC-8
- polynomial: `0x31`
- init value: `0xFF`
- reflect in/out: false/false
- final XOR: `0x00`
- example from datasheet: `CRC(0xBEEF) = 0x92`

Reference implementation:
```c
uint8_t sht4x_crc8(const uint8_t *data, size_t len) {
    uint8_t crc = 0xFF;
    for (size_t i = 0; i < len; ++i) {
        crc ^= data[i];
        for (int b = 0; b < 8; ++b) {
            if (crc & 0x80) crc = (crc << 1) ^ 0x31;
            else            crc = (crc << 1);
        }
    }
    return crc;
}
```

## Minimal one-shot measurement flow
```c
bool sht4x_read(float *temp_c, float *rh_pct) {
    uint8_t cmd = 0xFD; // high precision
    i2c_write(SHT4X_ADDR, &cmd, 1);
    delay_ms(10);

    uint8_t rx[6];
    i2c_read(SHT4X_ADDR, rx, 6);

    if (sht4x_crc8(&rx[0], 2) != rx[2]) return false;
    if (sht4x_crc8(&rx[3], 2) != rx[5]) return false;

    uint16_t raw_t  = ((uint16_t)rx[0] << 8) | rx[1];
    uint16_t raw_rh = ((uint16_t)rx[3] << 8) | rx[4];

    *temp_c = -45.0f + 175.0f * ((float)raw_t / 65535.0f);
    *rh_pct = -6.0f + 125.0f * ((float)raw_rh / 65535.0f);

    if (*rh_pct < 0.0f) *rh_pct = 0.0f;
    if (*rh_pct > 100.0f) *rh_pct = 100.0f;
    return true;
}
```

## Serial number read
Command: `0x89`

Response: 6 bytes
- SN word 1 MSB
- SN word 1 LSB
- CRC
- SN word 2 MSB
- SN word 2 LSB
- CRC

Combine example:
```c
uint32_t serial = ((uint32_t)sn0 << 16) | sn1;
```

## Reset behavior
### Soft reset
- send `0x94`
- wait about `1 ms`

### Other reset methods
- I2C general-call reset: send `0x06` to address `0x00`
- power down, including pulling `SCL` and `SDA` low

Any running command can be aborted by soft reset or general-call reset.

## Heater behavior
### What the heater does
After a heater command:
1. Heater turns on
2. Timer runs for `0.1 s` or `1 s`
3. A high-repeatability measurement is triggered before heater turns off
4. Temperature/RH result becomes available

### Important cautions
- No dedicated heater-off command
- Maximum recommended duty cycle: `10%`
- During heater operation, normal sensor specs are not valid
- Highest heater setting can draw up to about `75 mA`
- Heater should only be used in ambient temperatures below `65 C`

### Good use cases
- Remove condensation
- Improve behavior in very humid environments

## Driver architecture recommendations
Since this is command-based, a clean driver should expose **operations**, not registers.

Implement these functions:
- `probe()`
- `soft_reset()`
- `read_serial()`
- `measure_low()`
- `measure_medium()`
- `measure_high()`
- `heater_measure(power, duration)`
- `crc_check()`

## Suggested enums
```c
typedef enum {
    SHT4X_REPEAT_LOW,
    SHT4X_REPEAT_MEDIUM,
    SHT4X_REPEAT_HIGH,
} sht4x_repeatability_t;

typedef enum {
    SHT4X_HEATER_20MW,
    SHT4X_HEATER_110MW,
    SHT4X_HEATER_200MW,
} sht4x_heater_power_t;

typedef enum {
    SHT4X_HEATER_100MS,
    SHT4X_HEATER_1S,
} sht4x_heater_duration_t;
```

## Best first driver target
Start with only:
- I2C probe
- command `0xFD`
- 6-byte read
- CRC check
- raw-to-physical conversion
- humidity clamping

That is enough for a solid production one-shot driver. Add heater support only if your application really needs it.
