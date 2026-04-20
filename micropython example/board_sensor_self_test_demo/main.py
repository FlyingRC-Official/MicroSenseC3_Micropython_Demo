from machine import I2C, Pin
import sys
import time

from board_sensors import FAIL, PASS, WARN
from board_sensors import test_ltr381, test_qmc6309, test_qmi8658a, test_sht40, test_spa06


I2C_BUS_ID = 0
I2C_SCL_PIN = 7
I2C_SDA_PIN = 6
I2C_FREQ_HZ = 400000
LIVE_INTERVAL_MS = 2000

SENSOR_TESTS = (
    ("QMI8658A", 0x6A, test_qmi8658a),
    ("QMC6309", 0x7C, test_qmc6309),
    ("SPA06-003", 0x77, test_spa06),
    ("SHT40", 0x44, test_sht40),
    ("LTR-381RGB-01", 0x53, test_ltr381),
)


def flush_stdout():
    if hasattr(sys.stdout, "flush"):
        sys.stdout.flush()


def format_address(address):
    return "0x%02X" % address


def format_triplet(values, decimals):
    if decimals <= 0:
        return "(%d,%d,%d)" % values
    fmt = "(%." + str(decimals) + "f,%." + str(decimals) + "f,%." + str(decimals) + "f)"
    return fmt % values


def create_i2c():
    return I2C(
        I2C_BUS_ID,
        scl=Pin(I2C_SCL_PIN),
        sda=Pin(I2C_SDA_PIN),
        freq=I2C_FREQ_HZ,
    )


def print_banner():
    print("MicroSense board sensor self-test demo")
    print(
        "I2C: bus=%d, SDA=GPIO%d, SCL=GPIO%d, freq=%dHz"
        % (I2C_BUS_ID, I2C_SDA_PIN, I2C_SCL_PIN, I2C_FREQ_HZ)
    )
    print("Expected onboard sensors:")
    for name, address, _tester in SENSOR_TESTS:
        print("  %-15s %s" % (name, format_address(address)))
    flush_stdout()


def print_scan_results(i2c):
    try:
        detected = sorted(i2c.scan())
    except OSError as exc:
        print("I2C scan failed:", exc)
        flush_stdout()
        return []

    if detected:
        detected_text = ", ".join([format_address(address) for address in detected])
    else:
        detected_text = "none"
    print("Detected I2C addresses:", detected_text)
    flush_stdout()
    return detected


def run_sensor_tests(i2c):
    results = []
    print("Running startup checks...")
    flush_stdout()

    for _name, _address, tester in SENSOR_TESTS:
        result = tester(i2c)
        results.append(result)
        print(
            "%s %s %s %s"
            % (
                result["status"],
                result["name"],
                format_address(result["address"]),
                result["details"],
            )
        )
        flush_stdout()
    return results


def overall_status(results):
    seen_warn = False
    for result in results:
        if result["status"] == FAIL:
            return FAIL
        if result["status"] == WARN:
            seen_warn = True
    if seen_warn:
        return WARN
    return PASS


def format_live_sample(result, sample):
    name = result["name"]
    if name == "QMI8658A":
        return "%s temp=%.1fC accel=%s gyro=%s" % (
            name,
            sample["temp_c"],
            format_triplet(sample["accel_g"], 2),
            format_triplet(sample["gyro_dps"], 1),
        )
    if name == "QMC6309":
        return "%s mag=%sG" % (name, format_triplet(sample["mag_gauss"], 3))
    if name == "SPA06-003":
        return "%s temp=%.1fC pressure=%.2fhPa" % (
            name,
            sample["temp_c"],
            sample["pressure_hpa"],
        )
    if name == "SHT40":
        return "%s temp=%.1fC humidity=%.1f%%RH" % (
            name,
            sample["temp_c"],
            sample["humidity_rh"],
        )
    if name == "LTR-381RGB-01":
        return "%s ir=%d rgb=(%d,%d,%d)" % (
            name,
            sample["ir"],
            sample["red"],
            sample["green"],
            sample["blue"],
        )
    return "%s sample=%s" % (name, sample)


def live_monitor(results):
    active_results = []
    for result in results:
        if result["status"] != FAIL and callable(result.get("reader")):
            active_results.append(result)

    if not active_results:
        print("No readable sensors available for live monitoring.")
        flush_stdout()
        while True:
            time.sleep_ms(LIVE_INTERVAL_MS)

    print("Live monitor: %d sensor(s), update every %d ms" % (len(active_results), LIVE_INTERVAL_MS))
    flush_stdout()

    start_ms = time.ticks_ms()
    while True:
        parts = []
        elapsed_ms = time.ticks_diff(time.ticks_ms(), start_ms)

        for result in active_results:
            try:
                sample = result["reader"]()
                if sample is None:
                    parts.append("%s timeout" % result["name"])
                else:
                    parts.append(format_live_sample(result, sample))
            except Exception as exc:
                parts.append("%s error=%s" % (result["name"], exc))

        print("%dms %s" % (elapsed_ms, " | ".join(parts)))
        flush_stdout()
        time.sleep_ms(LIVE_INTERVAL_MS)


def main():
    print_banner()
    i2c = create_i2c()
    print_scan_results(i2c)
    results = run_sensor_tests(i2c)

    summary = overall_status(results)
    print("OVERALL:", summary)
    if summary == PASS:
        print("Board looks healthy. Starting live monitor.")
    elif summary == WARN:
        print("Board is readable, but at least one sensor reported a soft warning.")
    else:
        print("At least one sensor failed startup. Live monitor will continue for readable sensors.")
    flush_stdout()

    live_monitor(results)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Demo stopped:", exc)
        flush_stdout()
