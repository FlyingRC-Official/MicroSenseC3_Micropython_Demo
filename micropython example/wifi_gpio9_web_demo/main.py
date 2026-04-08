from machine import Pin
import network
import socket
import sys
import time


AP_SSID = "MicroSense-C3-Button"
AP_PASSWORD = "microsense"
AP_CHANNEL = 6
AP_AUTHMODE = getattr(network, "AUTH_WPA_WPA2_PSK", 3)
AP_TXPOWER_DBM = 8
BUTTON_PIN = 9
LED_PIN = 8
LED_ON_VALUE = 0
LED_OFF_VALUE = 0 if LED_ON_VALUE else 1
POLL_INTERVAL_MS = 50
SOCKET_TIMEOUT_S = 1


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ESP32-C3 Button And LED Control</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef4ff;
      --panel: #ffffff;
      --text: #12304a;
      --muted: #5f7388;
      --pressed: #d83f31;
      --released: #1f8f51;
      --accent: #1f5fbf;
      --led-on: #ffb11f;
      --led-off: #8193a7;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Arial, sans-serif;
      background: radial-gradient(circle at top, #ffffff 0%%, var(--bg) 65%%);
      color: var(--text);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      box-sizing: border-box;
    }

    .card {
      width: min(420px, 100%%);
      background: var(--panel);
      border-radius: 20px;
      box-shadow: 0 18px 45px rgba(18, 48, 74, 0.18);
      padding: 28px;
    }

    h1 {
      margin: 0 0 10px;
      font-size: 1.8rem;
    }

    p {
      margin: 0 0 14px;
      line-height: 1.5;
      color: var(--muted);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      border-radius: 999px;
      color: #ffffff;
      font-weight: bold;
      font-size: 1.1rem;
      margin: 12px 0 18px;
    }

    .badge::before {
      content: "";
      width: 12px;
      height: 12px;
      border-radius: 50%%;
      background: rgba(255, 255, 255, 0.85);
    }

    .pressed {
      background: var(--pressed);
    }

    .released {
      background: var(--released);
    }

    .led-on {
      background: var(--led-on);
    }

    .led-off {
      background: var(--led-off);
    }

    .actions {
      display: flex;
      gap: 12px;
      margin: 12px 0 18px;
    }

    .actions button {
      flex: 1;
      border: none;
      border-radius: 14px;
      padding: 14px 16px;
      font-size: 1rem;
      font-weight: bold;
      cursor: pointer;
      color: #ffffff;
      background: var(--accent);
    }

    .actions button.secondary {
      background: #5f7388;
    }

    .actions button:disabled {
      opacity: 0.55;
      cursor: default;
    }

    .meta {
      font-size: 0.95rem;
      color: var(--muted);
    }

    code {
      color: var(--accent);
      font-weight: bold;
    }
  </style>
</head>
<body>
  <main class="card">
    <h1>ESP32-C3 Wi-Fi Control Demo</h1>
    <p>Connect your phone to <code>%s</code> to watch the GPIO9 boot button and control an external LED wired to GPIO8.</p>
    <p class="meta">GPIO9 button</p>
    <div id="button-status" class="badge released">Released</div>
    <p class="meta">GPIO8 LED output</p>
    <div id="led-status" class="badge led-off">LED Off</div>
    <div class="actions">
      <button id="led-on">Turn LED On</button>
      <button id="led-off" class="secondary">Turn LED Off</button>
    </div>
    <p class="meta">Button pin: GPIO9</p>
    <p class="meta">LED pin: GPIO8</p>
    <p class="meta">Board IP: <code>%s</code></p>
    <p class="meta">Last update: <span id="updated">waiting...</span></p>
  </main>

  <script>
    const buttonStatusEl = document.getElementById("button-status");
    const ledStatusEl = document.getElementById("led-status");
    const ledOnButton = document.getElementById("led-on");
    const ledOffButton = document.getElementById("led-off");
    const updatedEl = document.getElementById("updated");

    function updateView(data) {
      if (data.button_pressed) {
        buttonStatusEl.textContent = "Pressed";
        buttonStatusEl.className = "badge pressed";
      } else {
        buttonStatusEl.textContent = "Released";
        buttonStatusEl.className = "badge released";
      }

      if (data.led_on) {
        ledStatusEl.textContent = "LED On";
        ledStatusEl.className = "badge led-on";
        ledOnButton.disabled = true;
        ledOffButton.disabled = false;
      } else {
        ledStatusEl.textContent = "LED Off";
        ledStatusEl.className = "badge led-off";
        ledOnButton.disabled = false;
        ledOffButton.disabled = true;
      }

      updatedEl.textContent = new Date().toLocaleTimeString();
    }

    async function setLed(state) {
      const route = state ? "/led/on" : "/led/off";

      try {
        const response = await fetch(route, { cache: "no-store" });
        const data = await response.json();
        updateView(data);
      } catch (error) {
        updatedEl.textContent = "LED command failed";
      }
    }

    async function poll() {
      try {
        const response = await fetch("/status?ts=" + Date.now(), { cache: "no-store" });
        const data = await response.json();
        updateView(data);
      } catch (error) {
        updatedEl.textContent = "connection lost";
      }
    }

    ledOnButton.addEventListener("click", function () {
      setLed(true);
    });

    ledOffButton.addEventListener("click", function () {
      setLed(false);
    });

    poll();
    setInterval(poll, 500);
  </script>
</body>
</html>
"""


button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN, Pin.OUT)
led.value(LED_OFF_VALUE)


def button_pressed():
    return button.value() == 0


def led_is_on():
    return led.value() == LED_ON_VALUE


def set_led(on):
    led.value(LED_ON_VALUE if on else LED_OFF_VALUE)


def build_status_json():
    return (
        '{"button_pressed":%s,"button_gpio":9,"led_on":%s,"led_gpio":8}'
        % (
            "true" if button_pressed() else "false",
            "true" if led_is_on() else "false",
        )
    )


def http_response(status_code, content_type, body):
    if isinstance(body, str):
        body = body.encode("utf-8")

    headers = [
        "HTTP/1.1 %s" % status_code,
        "Content-Type: %s" % content_type,
        "Content-Length: %d" % len(body),
        "Connection: close",
        "Cache-Control: no-store",
        "",
        "",
    ]
    return "\r\n".join(headers).encode("utf-8") + body


def start_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASSWORD, authmode=AP_AUTHMODE)
    ap.config(channel=AP_CHANNEL)
    ap.config(txpower=AP_TXPOWER_DBM)

    while not ap.active():
        time.sleep_ms(100)

    return ap


def open_server():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    server.listen(2)
    server.settimeout(SOCKET_TIMEOUT_S)
    return server


def read_request_path(client):
    request = client.recv(1024)
    if not request:
        return "/"

    try:
        request_line = request.decode("utf-8").split("\r\n", 1)[0]
    except UnicodeError:
        return "/"

    parts = request_line.split(" ")
    if len(parts) < 2:
        return "/"

    return parts[1]


def serve_client(client, ip_addr):
    path = read_request_path(client)
    route = path.split("?", 1)[0]

    if route == "/status":
        client.sendall(http_response("200 OK", "application/json", build_status_json()))
        return

    if route == "/led/on":
        set_led(True)
        print("GPIO8 LED: On")
        client.sendall(http_response("200 OK", "application/json", build_status_json()))
        return

    if route == "/led/off":
        set_led(False)
        print("GPIO8 LED: Off")
        client.sendall(http_response("200 OK", "application/json", build_status_json()))
        return

    if route == "/favicon.ico":
        client.sendall(http_response("204 No Content", "text/plain", b""))
        return

    body = HTML_PAGE % (AP_SSID, ip_addr)
    client.sendall(http_response("200 OK", "text/html; charset=utf-8", body))


def print_startup(ap):
    ip_addr = ap.ifconfig()[0]
    print("ESP32-C3 Wi-Fi button + LED demo")
    print("Access point SSID:", AP_SSID)
    print("Access point password:", AP_PASSWORD)
    print("Access point tx power:", AP_TXPOWER_DBM, "dBm")
    print("GPIO9 button is active-low")
    print("GPIO8 LED output defaults to OFF")
    print("Connect your phone and open: http://%s/" % ip_addr)
    if hasattr(sys.stdout, "flush"):
        sys.stdout.flush()


def main():
    ap = start_access_point()
    server = open_server()
    ip_addr = ap.ifconfig()[0]
    print_startup(ap)

    last_state = None
    last_poll_ms = time.ticks_ms()

    while True:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_poll_ms) >= POLL_INTERVAL_MS:
            pressed = button_pressed()
            if pressed != last_state:
                print("GPIO9 button:", "Pressed" if pressed else "Released")
                if hasattr(sys.stdout, "flush"):
                    sys.stdout.flush()
                last_state = pressed
            last_poll_ms = now

        client = None
        try:
            client, client_addr = server.accept()
            print("HTTP client:", client_addr[0])
            serve_client(client, ip_addr)
        except OSError:
            pass
        finally:
            if client is not None:
                client.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Demo stopped:", exc)
        if hasattr(sys.stdout, "flush"):
            sys.stdout.flush()
