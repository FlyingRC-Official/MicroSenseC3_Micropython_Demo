from machine import I2C
import time


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

    ACCEL_FS_BITS = {
        2: 0x00,
        4: 0x01,
        8: 0x02,
        16: 0x03,
    }

    GYRO_FS_BITS = {
        16: 0x00,
        32: 0x01,
        64: 0x02,
        128: 0x03,
        256: 0x04,
        512: 0x05,
        1024: 0x06,
        2048: 0x07,
    }

    ACCEL_LSB_PER_G = {
        2: 16384,
        4: 8192,
        8: 4096,
        16: 2048,
    }

    GYRO_LSB_PER_DPS = {
        16: 2048,
        32: 1024,
        64: 512,
        128: 256,
        256: 128,
        512: 64,
        1024: 32,
        2048: 16,
    }

    ACCEL_ODR_250HZ = 0x05
    GYRO_ODR_224HZ = 0x05

    def __init__(self, i2c, address=0x6A, accel_range_g=4, gyro_range_dps=512):
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be an initialized machine.I2C instance")

        if accel_range_g not in self.ACCEL_FS_BITS:
            raise ValueError("unsupported accel_range_g: %r" % (accel_range_g,))

        if gyro_range_dps not in self.GYRO_FS_BITS:
            raise ValueError("unsupported gyro_range_dps: %r" % (gyro_range_dps,))

        self.i2c = i2c
        self.address = address
        self.accel_range_g = accel_range_g
        self.gyro_range_dps = gyro_range_dps

    def _write_reg(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytes((value,)))

    def _read_reg(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    def _read_regs(self, register, length):
        return self.i2c.readfrom_mem(self.address, register, length)

    @staticmethod
    def _to_int16(lo, hi):
        value = lo | (hi << 8)
        if value & 0x8000:
            value -= 0x10000
        return value

    @staticmethod
    def _temp_to_celsius(temp_l, temp_h):
        return temp_h + (temp_l / 256.0)

    def probe(self):
        try:
            if self.address not in self.i2c.scan():
                return False
            return self.chip_id() == self.EXPECTED_CHIP_ID
        except OSError:
            return False

    def chip_id(self):
        return self._read_reg(self.WHO_AM_I)

    def reset(self):
        self._write_reg(self.RESET, self.RESET_CMD)
        time.sleep_ms(20)

    def configure(self):
        accel_ctrl = (self.ACCEL_FS_BITS[self.accel_range_g] << 4) | self.ACCEL_ODR_250HZ
        gyro_ctrl = (self.GYRO_FS_BITS[self.gyro_range_dps] << 4) | self.GYRO_ODR_224HZ

        # Enable address auto-increment so one read returns temp + accel + gyro.
        self._write_reg(self.CTRL1, 1 << 6)
        self._write_reg(self.CTRL2, accel_ctrl)
        self._write_reg(self.CTRL3, gyro_ctrl)
        self._write_reg(self.CTRL5, (1 << 4) | (1 << 0))
        self._write_reg(self.CTRL7, 0x03)
        time.sleep_ms(10)

    def init(self):
        time.sleep_ms(20)

        if not self.probe():
            raise OSError("QMI8658A not found at I2C address 0x%02X" % self.address)

        self.reset()

        chip_id = self.chip_id()
        if chip_id != self.EXPECTED_CHIP_ID:
            raise OSError(
                "Unexpected QMI8658A chip id 0x%02X after reset" % chip_id
            )

        self.configure()

    def read_raw(self):
        status = self._read_reg(self.STATUS0)
        if (status & 0x03) == 0:
            return None

        data = self._read_regs(self.TEMP_L, 14)
        return {
            "temp": (data[0], data[1]),
            "accel": (
                self._to_int16(data[2], data[3]),
                self._to_int16(data[4], data[5]),
                self._to_int16(data[6], data[7]),
            ),
            "gyro": (
                self._to_int16(data[8], data[9]),
                self._to_int16(data[10], data[11]),
                self._to_int16(data[12], data[13]),
            ),
        }

    def read_scaled(self):
        sample = self.read_raw()
        if sample is None:
            return None

        temp_l, temp_h = sample["temp"]
        ax, ay, az = sample["accel"]
        gx, gy, gz = sample["gyro"]

        accel_scale = self.ACCEL_LSB_PER_G[self.accel_range_g]
        gyro_scale = self.GYRO_LSB_PER_DPS[self.gyro_range_dps]

        return {
            "temp_c": self._temp_to_celsius(temp_l, temp_h),
            "accel_g": (
                ax / accel_scale,
                ay / accel_scale,
                az / accel_scale,
            ),
            "gyro_dps": (
                gx / gyro_scale,
                gy / gyro_scale,
                gz / gyro_scale,
            ),
        }

    def read_accel_raw(self):
        sample = self.read_raw()
        if sample is None:
            return None
        return sample["accel"]

    def read_accel_g(self):
        sample = self.read_scaled()
        if sample is None:
            return None
        return sample["accel_g"]

    def read_gyro_raw(self):
        sample = self.read_raw()
        if sample is None:
            return None
        return sample["gyro"]

    def read_gyro_dps(self):
        sample = self.read_scaled()
        if sample is None:
            return None
        return sample["gyro_dps"]

    def read_temperature_c(self):
        sample = self.read_scaled()
        if sample is None:
            return None
        return sample["temp_c"]
