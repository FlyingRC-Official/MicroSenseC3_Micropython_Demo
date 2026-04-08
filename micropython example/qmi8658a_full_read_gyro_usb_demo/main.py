from machine import I2C, Pin
import sys
import time

from qmi8658a import QMI8658A


I2C_BUS_ID = 0
I2C_SCL_PIN = 7
I2C_SDA_PIN = 6
I2C_FREQ_HZ = 400000
QMI8658A_ADDR = 0x6A
PRINT_INTERVAL_MS = 100


def flush_stdout():
    if hasattr(sys.stdout, "flush"):
        sys.stdout.flush()


def create_sensor():
    i2c = I2C(
        I2C_BUS_ID,
        scl=Pin(I2C_SCL_PIN),
        sda=Pin(I2C_SDA_PIN),
        freq=I2C_FREQ_HZ,
    )
    sensor = QMI8658A(i2c, address=QMI8658A_ADDR)
    sensor.init()
    return sensor


def print_header():
    print("QMI8658A gyro USB serial demo")
    print(
        "I2C: bus=%d, SDA=GPIO%d, SCL=GPIO%d, addr=0x%02X"
        % (I2C_BUS_ID, I2C_SDA_PIN, I2C_SCL_PIN, QMI8658A_ADDR)
    )
    print("Library reads temperature, accelerometer, and gyroscope data")
    print("USB serial output below is gyro only")
    print("Columns: ms,gx_dps,gy_dps,gz_dps")
    flush_stdout()


def main():
    print_header()
    print("Initializing sensor...")
    flush_stdout()

    sensor = create_sensor()
    print("Sensor ready")
    flush_stdout()

    start_ms = time.ticks_ms()

    while True:
        sample = sensor.read_scaled()
        if sample is not None:
            elapsed_ms = time.ticks_diff(time.ticks_ms(), start_ms)
            gx, gy, gz = sample["gyro_dps"]
            print("%d,%.2f,%.2f,%.2f" % (elapsed_ms, gx, gy, gz))
            flush_stdout()

        time.sleep_ms(PRINT_INTERVAL_MS)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Demo stopped:", exc)
        flush_stdout()
