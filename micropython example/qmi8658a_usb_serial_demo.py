from machine import I2C, Pin
import sys
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

    def __init__(self, i2c, address=0x6A, accel_range_g=4, gyro_range_dps=512):
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

    def scan_present(self):
        return self.address in self.i2c.scan()

    def chip_id(self):
        return self._read_reg(self.WHO_AM_I)

    def reset(self):
        self._write_reg(self.RESET, self.RESET_CMD)
        time.sleep_ms(20)

    def configure(self):
        accel_fs_bits = {
            2: 0x00,
            4: 0x01,
            8: 0x02,
            16: 0x03,
        }[self.accel_range_g]
        gyro_fs_bits = {
            16: 0x00,
            32: 0x01,
            64: 0x02,
            128: 0x03,
            256: 0x04,
            512: 0x05,
            1024: 0x06,
            2048: 0x07,
        }[self.gyro_range_dps]

        # Auto-increment register addresses so burst reads work.
        self._write_reg(self.CTRL1, 1 << 6)
        # Accel: +/-4 g at 250 Hz by default.
        self._write_reg(self.CTRL2, (accel_fs_bits << 4) | 0x05)
        # Gyro: +/-512 dps at 224.2 Hz by default.
        self._write_reg(self.CTRL3, (gyro_fs_bits << 4) | 0x05)
        # Enable LPF for both accel and gyro.
        self._write_reg(self.CTRL5, (1 << 4) | (1 << 0))
        # Turn on accel + gyro.
        self._write_reg(self.CTRL7, 0x03)
        time.sleep_ms(10)

    def init(self):
        if not self.scan_present():
            raise OSError("QMI8658A not found on I2C address 0x%02X" % self.address)

        time.sleep_ms(20)
        chip_id = self.chip_id()
        if chip_id != self.EXPECTED_CHIP_ID:
            raise OSError(
                "Unexpected QMI8658A chip id 0x%02X, expected 0x%02X"
                % (chip_id, self.EXPECTED_CHIP_ID)
            )

        self.reset()
        chip_id = self.chip_id()
        if chip_id != self.EXPECTED_CHIP_ID:
            raise OSError("QMI8658A did not respond correctly after reset")

        self.configure()

    def read_raw(self):
        status = self._read_reg(self.STATUS0)
        if (status & 0x03) == 0:
            return None

        data = self._read_regs(self.TEMP_L, 14)
        temp_c = data[1] + (data[0] / 256.0)

        ax = self._to_int16(data[2], data[3])
        ay = self._to_int16(data[4], data[5])
        az = self._to_int16(data[6], data[7])
        gx = self._to_int16(data[8], data[9])
        gy = self._to_int16(data[10], data[11])
        gz = self._to_int16(data[12], data[13])

        return temp_c, ax, ay, az, gx, gy, gz

    def read_scaled(self):
        raw = self.read_raw()
        if raw is None:
            return None

        temp_c, ax, ay, az, gx, gy, gz = raw
        accel_scale = self.ACCEL_LSB_PER_G[self.accel_range_g]
        gyro_scale = self.GYRO_LSB_PER_DPS[self.gyro_range_dps]

        return {
            "temp_c": temp_c,
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


def create_sensor():
    i2c = I2C(0, scl=Pin(7), sda=Pin(6), freq=400000)
    sensor = QMI8658A(i2c, address=0x6A)
    sensor.init()
    return sensor


def print_header():
    print("QMI8658A USB serial demo")
    print("I2C: SDA=GPIO6, SCL=GPIO7, addr=0x6A")
    print("Columns: ms,temp_c,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps")


def main():
    print_header()
    sensor = create_sensor()
    start_ms = time.ticks_ms()

    while True:
        sample = sensor.read_scaled()
        if sample is not None:
            elapsed_ms = time.ticks_diff(time.ticks_ms(), start_ms)
            ax, ay, az = sample["accel_g"]
            gx, gy, gz = sample["gyro_dps"]
            print(
                "%d,%.2f,%.4f,%.4f,%.4f,%.2f,%.2f,%.2f"
                % (elapsed_ms, sample["temp_c"], ax, ay, az, gx, gy, gz)
            )
            if hasattr(sys.stdout, "flush"):
                sys.stdout.flush()

        time.sleep_ms(100)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Demo stopped:", exc)
        if hasattr(sys.stdout, "flush"):
            sys.stdout.flush()
