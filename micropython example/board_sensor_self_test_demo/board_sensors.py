from machine import I2C
import time


PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
QMC6309_FALLBACK_ADDRESS = 0x7C
QMC6309_EXPECTED_CHIP_ID = 0x90


def _make_result(name, address, status, details, sample=None, reader=None):
    result = {
        "name": name,
        "address": address,
        "status": status,
        "details": details,
        "sample": sample,
    }
    if reader is not None:
        result["reader"] = reader
    return result


def custom_i2c_scan(i2c):
    found = set()

    # Scan the normal 7-bit range first, then apply a board-specific
    # fallback for the known high reserved-address QMC6309 device.
    for address in range(0x08, 0x78):
        try:
            i2c.writeto(address, b"")
            found.add(address)
        except OSError:
            pass

    # QMC6309 on this board responds at 0x7C even though built-in scan omits it.
    try:
        chip_id = i2c.readfrom_mem(QMC6309_FALLBACK_ADDRESS, 0x00, 1)[0]
        if chip_id == QMC6309_EXPECTED_CHIP_ID:
            found.add(QMC6309_FALLBACK_ADDRESS)
    except OSError:
        pass

    return sorted(found)


def _address_present(i2c, address):
    try:
        return address in custom_i2c_scan(i2c)
    except OSError:
        return False


def _status_from_warnings(warnings):
    if warnings:
        return WARN
    return PASS


def _sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    mask = (1 << bits) - 1
    value &= mask
    if value & sign_bit:
        value -= 1 << bits
    return value


def _to_int16(lo, hi):
    return _sign_extend(lo | (hi << 8), 16)


def _read_signed24(msb, mid, lsb):
    return _sign_extend((msb << 16) | (mid << 8) | lsb, 24)


def _format_triplet(values, decimals):
    if decimals <= 0:
        return "(%d,%d,%d)" % values
    fmt = "(%." + str(decimals) + "f,%." + str(decimals) + "f,%." + str(decimals) + "f)"
    return fmt % values


class QMI8658A:
    WHO_AM_I = 0x00
    CTRL1 = 0x02
    CTRL2 = 0x03
    CTRL3 = 0x04
    CTRL5 = 0x06
    CTRL7 = 0x08
    STATUS0 = 0x2E
    TEMP_L = 0x33
    RESET = 0x60

    EXPECTED_CHIP_ID = 0x05
    RESET_CMD = 0xB0

    def __init__(self, i2c, address=0x6A):
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be an initialized machine.I2C instance")
        self.i2c = i2c
        self.address = address

    def _write_reg(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytes((value,)))

    def _read_reg(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    def _read_regs(self, register, length):
        return self.i2c.readfrom_mem(self.address, register, length)

    @staticmethod
    def _temp_to_celsius(temp_l, temp_h):
        return temp_h + (temp_l / 256.0)

    def chip_id(self):
        return self._read_reg(self.WHO_AM_I)

    def reset(self):
        self._write_reg(self.RESET, self.RESET_CMD)
        time.sleep_ms(20)

    def configure(self):
        self._write_reg(self.CTRL1, 1 << 6)
        self._write_reg(self.CTRL2, (0x01 << 4) | 0x05)
        self._write_reg(self.CTRL3, (0x05 << 4) | 0x05)
        self._write_reg(self.CTRL5, (1 << 4) | (1 << 0))
        self._write_reg(self.CTRL7, 0x03)
        time.sleep_ms(10)

    def init(self):
        time.sleep_ms(20)
        chip_id = self.chip_id()
        if chip_id != self.EXPECTED_CHIP_ID:
            raise OSError("Unexpected QMI8658A chip id 0x%02X" % chip_id)
        self.reset()
        chip_id = self.chip_id()
        if chip_id != self.EXPECTED_CHIP_ID:
            raise OSError("Unexpected QMI8658A chip id 0x%02X after reset" % chip_id)
        self.configure()

    def read_scaled(self):
        status = self._read_reg(self.STATUS0)
        if (status & 0x03) == 0:
            return None

        data = self._read_regs(self.TEMP_L, 14)
        temp_c = self._temp_to_celsius(data[0], data[1])
        ax = _to_int16(data[2], data[3]) / 8192.0
        ay = _to_int16(data[4], data[5]) / 8192.0
        az = _to_int16(data[6], data[7]) / 8192.0
        gx = _to_int16(data[8], data[9]) / 64.0
        gy = _to_int16(data[10], data[11]) / 64.0
        gz = _to_int16(data[12], data[13]) / 64.0
        return {
            "temp_c": temp_c,
            "accel_g": (ax, ay, az),
            "gyro_dps": (gx, gy, gz),
        }

    def read_scaled_timeout(self, timeout_ms=250):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) >= 0:
            sample = self.read_scaled()
            if sample is not None:
                return sample
            time.sleep_ms(10)
        return None


class QMC6309:
    CHIP_ID = 0x00
    STATUS = 0x09
    CTRL1 = 0x0A
    CTRL2 = 0x0B

    EXPECTED_CHIP_ID = QMC6309_EXPECTED_CHIP_ID

    def __init__(self, i2c, address=0x7C):
        self.i2c = i2c
        self.address = address

    def _write_reg(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytes((value,)))

    def _read_reg(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    def chip_id(self):
        return self._read_reg(self.CHIP_ID)

    def init(self):
        time.sleep_ms(5)
        chip_id = self.chip_id()
        if chip_id != self.EXPECTED_CHIP_ID:
            raise OSError("Unexpected QMC6309 chip id 0x%02X" % chip_id)
        self._write_reg(self.CTRL2, 0x40)
        self._write_reg(self.CTRL1, 0x61)
        time.sleep_ms(20)

    def read_xyz_gauss(self, timeout_ms=250):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) >= 0:
            status = self._read_reg(self.STATUS)
            if status & 0x01:
                data = self.i2c.readfrom_mem(self.address, 0x01, 6)
                sample = {
                    "mag_gauss": (
                        _to_int16(data[0], data[1]) / 1000.0,
                        _to_int16(data[2], data[3]) / 1000.0,
                        _to_int16(data[4], data[5]) / 1000.0,
                    ),
                    "overflow": bool(status & 0x02),
                }
                return sample
            time.sleep_ms(10)
        return None


class SPA06:
    ID = 0x0D
    PRS_CFG = 0x06
    TMP_CFG = 0x07
    MEAS_CFG = 0x08
    CFG_REG = 0x09
    COEF_START = 0x10

    SCALE_FACTORS = {
        1: 524288.0,
        2: 1572864.0,
        4: 3670016.0,
        8: 7864320.0,
        16: 253952.0,
        32: 516096.0,
        64: 1040384.0,
        128: 2088960.0,
    }

    def __init__(self, i2c, address=0x77):
        self.i2c = i2c
        self.address = address
        self.pressure_osr = 16
        self.temperature_osr = 2
        self.coefficients = None

    def _write_reg(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytes((value,)))

    def _read_reg(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    def _read_regs(self, register, length):
        return self.i2c.readfrom_mem(self.address, register, length)

    def _wait_for_startup(self, timeout_ms=500):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) >= 0:
            value = self._read_reg(self.MEAS_CFG)
            if (value & 0xC0) == 0xC0:
                return value
            time.sleep_ms(10)
        raise OSError("SPA06 startup timeout")

    def _wait_for_sample(self, timeout_ms=500):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) >= 0:
            value = self._read_reg(self.MEAS_CFG)
            if (value & 0x30) == 0x30:
                return
            time.sleep_ms(20)
        raise OSError("SPA06 data timeout")

    def _read_coefficients(self):
        coef = self._read_regs(self.COEF_START, 21)

        # Coefficients are bit-packed across byte boundaries.
        self.coefficients = {
            "c0": _sign_extend((coef[0] << 4) | (coef[1] >> 4), 12),
            "c1": _sign_extend(((coef[1] & 0x0F) << 8) | coef[2], 12),
            "c00": _sign_extend((coef[3] << 12) | (coef[4] << 4) | (coef[5] >> 4), 20),
            "c10": _sign_extend(((coef[5] & 0x0F) << 16) | (coef[6] << 8) | coef[7], 20),
            "c01": _sign_extend((coef[8] << 8) | coef[9], 16),
            "c11": _sign_extend((coef[10] << 8) | coef[11], 16),
            "c20": _sign_extend((coef[12] << 8) | coef[13], 16),
            "c21": _sign_extend((coef[14] << 8) | coef[15], 16),
            "c30": _sign_extend((coef[16] << 8) | coef[17], 16),
            "c31": _sign_extend((coef[18] << 4) | (coef[19] >> 4), 12),
            "c40": _sign_extend(((coef[19] & 0x0F) << 8) | coef[20], 12),
        }

    def _compensate(self, raw_pressure, raw_temperature):
        coeff = self.coefficients
        p_scale = self.SCALE_FACTORS[self.pressure_osr]
        t_scale = self.SCALE_FACTORS[self.temperature_osr]
        p_raw_sc = raw_pressure / p_scale
        t_raw_sc = raw_temperature / t_scale

        temperature_c = coeff["c0"] * 0.5 + coeff["c1"] * t_raw_sc
        pressure_pa = (
            coeff["c00"]
            + p_raw_sc
            * (
                coeff["c10"]
                + p_raw_sc
                * (
                    coeff["c20"]
                    + p_raw_sc * (coeff["c30"] + p_raw_sc * coeff["c40"])
                )
            )
            + t_raw_sc
            * (
                coeff["c01"]
                + p_raw_sc
                * (
                    coeff["c11"]
                    + p_raw_sc * (coeff["c21"] + p_raw_sc * coeff["c31"])
                )
            )
        )
        return {
            "temp_c": temperature_c,
            "pressure_pa": pressure_pa,
            "pressure_hpa": pressure_pa / 100.0,
        }

    def init(self):
        self._wait_for_startup()
        sensor_id = self._read_reg(self.ID)
        if (sensor_id & 0x0F) != 0x01:
            raise OSError("Unexpected SPA06 id 0x%02X" % sensor_id)
        self._read_coefficients()
        self._write_reg(self.PRS_CFG, 0x14)
        self._write_reg(self.TMP_CFG, 0x11)
        self._write_reg(self.CFG_REG, 0x04)
        self._write_reg(self.MEAS_CFG, 0x07)
        time.sleep_ms(50)
        return sensor_id

    def read_compensated(self, timeout_ms=500):
        self._wait_for_sample(timeout_ms)
        data = self._read_regs(0x00, 6)
        raw_pressure = _read_signed24(data[0], data[1], data[2])
        raw_temperature = _read_signed24(data[3], data[4], data[5])
        sample = self._compensate(raw_pressure, raw_temperature)
        sample["raw_pressure"] = raw_pressure
        sample["raw_temperature"] = raw_temperature
        return sample


class SHT40:
    HIGH_PRECISION_MEASURE = 0xFD
    SOFT_RESET = 0x94

    def __init__(self, i2c, address=0x44):
        self.i2c = i2c
        self.address = address

    def _crc8(self, data):
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    def soft_reset(self):
        self.i2c.writeto(self.address, bytes((self.SOFT_RESET,)))
        time.sleep_ms(2)

    def measure_high(self):
        self.i2c.writeto(self.address, bytes((self.HIGH_PRECISION_MEASURE,)))
        time.sleep_ms(10)
        data = self.i2c.readfrom(self.address, 6)

        if self._crc8(data[0:2]) != data[2]:
            raise OSError("SHT40 temperature CRC mismatch")
        if self._crc8(data[3:5]) != data[5]:
            raise OSError("SHT40 humidity CRC mismatch")

        raw_temp = (data[0] << 8) | data[1]
        raw_humidity = (data[3] << 8) | data[4]
        humidity_rh = -6.0 + 125.0 * (raw_humidity / 65535.0)
        clamped = False
        if humidity_rh < 0.0:
            humidity_rh = 0.0
            clamped = True
        if humidity_rh > 100.0:
            humidity_rh = 100.0
            clamped = True
        return {
            "temp_c": -45.0 + 175.0 * (raw_temp / 65535.0),
            "humidity_rh": humidity_rh,
            "humidity_clamped": clamped,
        }


class LTR381:
    MAIN_CTRL = 0x00
    MEAS_RATE = 0x04
    GAIN = 0x05
    PART_ID = 0x06
    MAIN_STATUS = 0x07

    EXPECTED_PART_ID = 0xC2

    def __init__(self, i2c, address=0x53):
        self.i2c = i2c
        self.address = address

    def _write_reg(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytes((value,)))

    def _read_reg(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    @staticmethod
    def _unpack20(low, mid, high):
        return ((high & 0x0F) << 16) | (mid << 8) | low

    def init(self):
        part_id = self._read_reg(self.PART_ID)
        if part_id != self.EXPECTED_PART_ID:
            raise OSError("Unexpected LTR-381 part id 0x%02X" % part_id)
        self._write_reg(self.MEAS_RATE, 0x22)
        self._write_reg(self.GAIN, 0x01)
        self._write_reg(self.MAIN_CTRL, 0x06)
        time.sleep_ms(5)
        return part_id

    def read_channels(self, timeout_ms=700):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) >= 0:
            status = self._read_reg(self.MAIN_STATUS)
            if status & 0x08:
                data = self.i2c.readfrom_mem(self.address, 0x0A, 12)
                return {
                    "ir": self._unpack20(data[0], data[1], data[2]),
                    "green": self._unpack20(data[3], data[4], data[5]),
                    "red": self._unpack20(data[6], data[7], data[8]),
                    "blue": self._unpack20(data[9], data[10], data[11]),
                }
            time.sleep_ms(25)
        return None


def test_qmi8658a(i2c):
    name = "QMI8658A"
    address = 0x6A
    if not _address_present(i2c, address):
        return _make_result(name, address, FAIL, "missing from I2C scan")

    try:
        sensor = QMI8658A(i2c, address=address)
        sensor.init()
        sample = sensor.read_scaled_timeout()
        if sample is None:
            return _make_result(name, address, FAIL, "no accel/gyro sample ready")

        warnings = []
        if sample["temp_c"] < -40.0 or sample["temp_c"] > 85.0:
            warnings.append("temperature outside -40..85C")

        details = "id=0x%02X temp=%.1fC accel=%s gyro=%s" % (
            sensor.EXPECTED_CHIP_ID,
            sample["temp_c"],
            _format_triplet(sample["accel_g"], 2),
            _format_triplet(sample["gyro_dps"], 1),
        )
        if warnings:
            details = details + " ; " + "; ".join(warnings)
        return _make_result(
            name,
            address,
            _status_from_warnings(warnings),
            details,
            sample=sample,
            reader=sensor.read_scaled_timeout,
        )
    except Exception as exc:
        return _make_result(name, address, FAIL, str(exc))


def test_qmc6309(i2c):
    name = "QMC6309"
    address = 0x7C
    if not _address_present(i2c, address):
        return _make_result(name, address, FAIL, "missing from I2C scan")

    try:
        sensor = QMC6309(i2c, address=address)
        sensor.init()
        sample = sensor.read_xyz_gauss()
        if sample is None:
            return _make_result(name, address, FAIL, "no magnetometer sample ready")

        warnings = []
        if sample["overflow"]:
            warnings.append("overflow flag set")

        details = "id=0x%02X mag=%sG" % (
            sensor.EXPECTED_CHIP_ID,
            _format_triplet(sample["mag_gauss"], 3),
        )
        if warnings:
            details = details + " ; " + "; ".join(warnings)
        return _make_result(
            name,
            address,
            _status_from_warnings(warnings),
            details,
            sample=sample,
            reader=sensor.read_xyz_gauss,
        )
    except Exception as exc:
        return _make_result(name, address, FAIL, str(exc))


def test_spa06(i2c):
    name = "SPA06-003"
    address = 0x77
    if not _address_present(i2c, address):
        return _make_result(name, address, FAIL, "missing from I2C scan")

    try:
        sensor = SPA06(i2c, address=address)
        sensor_id = sensor.init()
        sample = sensor.read_compensated()

        warnings = []
        if sample["pressure_hpa"] < 300.0 or sample["pressure_hpa"] > 1100.0:
            warnings.append("pressure outside 300..1100hPa")
        if sample["temp_c"] < -40.0 or sample["temp_c"] > 85.0:
            warnings.append("temperature outside -40..85C")

        details = "id=0x%02X temp=%.1fC pressure=%.2fhPa" % (
            sensor_id,
            sample["temp_c"],
            sample["pressure_hpa"],
        )
        if warnings:
            details = details + " ; " + "; ".join(warnings)
        return _make_result(
            name,
            address,
            _status_from_warnings(warnings),
            details,
            sample=sample,
            reader=sensor.read_compensated,
        )
    except Exception as exc:
        return _make_result(name, address, FAIL, str(exc))


def test_sht40(i2c):
    name = "SHT40"
    address = 0x44
    if not _address_present(i2c, address):
        return _make_result(name, address, FAIL, "missing from I2C scan")

    try:
        sensor = SHT40(i2c, address=address)
        sensor.soft_reset()
        sample = sensor.measure_high()

        warnings = []
        if sample["humidity_clamped"]:
            warnings.append("humidity result was clamped")
        if sample["temp_c"] < -40.0 or sample["temp_c"] > 125.0:
            warnings.append("temperature outside -40..125C")

        details = "temp=%.1fC humidity=%.1f%%RH" % (
            sample["temp_c"],
            sample["humidity_rh"],
        )
        if warnings:
            details = details + " ; " + "; ".join(warnings)
        return _make_result(
            name,
            address,
            _status_from_warnings(warnings),
            details,
            sample=sample,
            reader=sensor.measure_high,
        )
    except Exception as exc:
        return _make_result(name, address, FAIL, str(exc))


def test_ltr381(i2c):
    name = "LTR-381RGB-01"
    address = 0x53
    if not _address_present(i2c, address):
        return _make_result(name, address, FAIL, "missing from I2C scan")

    try:
        sensor = LTR381(i2c, address=address)
        part_id = sensor.init()
        sample = sensor.read_channels()
        if sample is None:
            return _make_result(name, address, FAIL, "no light/color sample ready")

        warnings = []
        if (
            sample["ir"] == 0
            and sample["green"] == 0
            and sample["red"] == 0
            and sample["blue"] == 0
        ):
            warnings.append("sample read but all channels are zero")

        details = "id=0x%02X ir=%d rgb=(%d,%d,%d)" % (
            part_id,
            sample["ir"],
            sample["red"],
            sample["green"],
            sample["blue"],
        )
        if warnings:
            details = details + " ; " + "; ".join(warnings)
        return _make_result(
            name,
            address,
            _status_from_warnings(warnings),
            details,
            sample=sample,
            reader=sensor.read_channels,
        )
    except Exception as exc:
        return _make_result(name, address, FAIL, str(exc))
