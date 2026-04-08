from machine import Pin
import network
import socket
import sys
import time


DEFAULT_WIFI_SSID = "YOUR_WIFI_SSID"
DEFAULT_WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
WIFI_CONNECT_TIMEOUT_MS = 15000
HOSTNAME = "microsense-c3-web-io"
BUTTON_PIN = 9
LED_PIN = 8
BUTTON_PRESSED_VALUE = 0
LED_ON_VALUE = 0
LED_OFF_VALUE = 0 if LED_ON_VALUE else 1
POLL_INTERVAL_MS = 50
HTTP_SOCKET_TIMEOUT_S = 1


try:
    import wifi_config

    WIFI_SSID = wifi_config.WIFI_SSID
    WIFI_PASSWORD = wifi_config.WIFI_PASSWORD
except ImportError:
    WIFI_SSID = DEFAULT_WIFI_SSID
    WIFI_PASSWORD = DEFAULT_WIFI_PASSWORD


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ESP32-C3 LAN LED And Button Demo</title>
  <style>
    :root {
      color-scheme: light;
      --bg-top: #f7fbff;
      --bg-bottom: #dfefff;
      --panel: #ffffff;
      --ink: #14324c;
      --muted: #5a7389;
      --accent: #0b84f3;
      --accent-strong: #0863b6;
      --pressed: #de4c3c;
      --released: #1d9b5d;
      --led-on: #ffb622;
      --led-off: #8c9eb0;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.95) 0%%, rgba(255, 255, 255, 0) 42%%),
        linear-gradient(180deg, var(--bg-top), var(--bg-bottom));
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .panel {
      width: min(460px, 100%%);
      background: var(--panel);
      border-radius: 22px;
      padding: 28px;
      box-shadow: 0 20px 44px rgba(20, 50, 76, 0.18);
    }

    h1 {
      margin: 0 0 12px;
      font-size: 1.9rem;
      line-height: 1.1;
    }

    p {
      margin: 0 0 14px;
      color: var(--muted);
      line-height: 1.5;
    }

    .meta {
      font-size: 0.96rem;
    }

    .status {
      margin: 12px 0 18px;
      padding: 14px 16px;
      border-radius: 16px;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: bold;
      font-size: 1.05rem;
    }

    .status::before {
      content: "";
      width: 12px;
      height: 12px;
      border-radius: 50%%;
      background: rgba(255, 255, 255, 0.88);
      flex: 0 0 auto;
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
      margin: 16px 0 18px;
    }

    button {
      flex: 1;
      border: none;
      border-radius: 14px;
      padding: 14px 16px;
      font-size: 1rem;
      font-weight: bold;
      color: #ffffff;
      background: var(--accent);
      cursor: pointer;
    }

    button.secondary {
      background: #6b7d90;
    }

    button:disabled {
      opacity: 0.6;
      cursor: default;
    }

    code {
      color: var(--accent-strong);
      font-weight: bold;
    }
  </style>
</head>
<body>
  <main class="panel">
    <h1>ESP32-C3 Web GPIO Demo</h1>
    <p>After the board joins your Wi-Fi router, open this page from your phone on the same LAN to read the GPIO9 button and control an external LED on GPIO8.</p>
    <p class="meta">Wi-Fi SSID: <code>%s</code></p>
    <p class="meta">Board IP: <code>%s</code></p>
    <p class="meta">GPIO9 button state</p>
    <div id="button-status" class="status released">Released</div>
    <p class="meta">GPIO8 LED output</p>
    <div id="led-status" class="status led-off">LED Off</div>
    <div class="actions">
      <button id="led-on">Turn LED On</button>
      <button id="led-off" class="secondary">Turn LED Off</button>
    </div>
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
        buttonStatusEl.className = "status pressed";
      } else {
        buttonStatusEl.textContent = "Released";
        buttonStatusEl.className = "status released";
      }

      if (data.led_on) {
        ledStatusEl.textContent = "LED On";
        ledStatusEl.className = "status led-on";
        ledOnButton.disabled = true;
        ledOffButton.disabled = false;
      } else {
        ledStatusEl.textContent = "LED Off";
        ledStatusEl.className = "status led-off";
        ledOnButton.disabled = false;
        ledOffButton.disabled = true;
      }

      updatedEl.textContent = new Date().toLocaleTimeString();
    }

    async function fetchJson(path) {
      const response = await fetch(path, { cache: "no-store" });
      return response.json();
    }

    async function setLed(state) {
      try {
        const route = state ? "/led/on" : "/led/off";
        const data = await fetchJson(route);
        updateView(data);
      } catch (error) {
        updatedEl.textContent = "LED command failed";
      }
    }

    async function poll() {
      try {
        const data = await fetchJson("/status?ts=" + Date.now());
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


def wifi_credentials_are_configured():
    return (
        WIFI_SSID
        and WIFI_PASSWORD is not None
        and WIFI_SSID != DEFAULT_WIFI_SSID
        and WIFI_PASSWORD != DEFAULT_WIFI_PASSWORD
    )


def button_pressed():
    return button.value() == BUTTON_PRESSED_VALUE


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


def connect_to_wifi():
    if not wifi_credentials_are_configured():
        raise RuntimeError(
            "Configure WIFI_SSID and WIFI_PASSWORD in wifi_config.py or main.py first."
        )

    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    if hasattr(sta, "config"):
        try:
            sta.config(dhcp_hostname=HOSTNAME)
        except Exception:
            pass

    if sta.isconnected():
        sta.disconnect()
        time.sleep_ms(300)

    print("Connecting to Wi-Fi SSID:", WIFI_SSID)
    sta.connect(WIFI_SSID, WIFI_PASSWORD)

    deadline = time.ticks_add(time.ticks_ms(), WIFI_CONNECT_TIMEOUT_MS)
    while not sta.isconnected():
        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            status = sta.status() if hasattr(sta, "status") else "unknown"
            raise RuntimeError("Wi-Fi connect timeout, status=%s" % status)
        time.sleep_ms(250)

    return sta


def open_server():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    server.listen(2)
    server.settimeout(HTTP_SOCKET_TIMEOUT_S)
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

    body = HTML_PAGE % (WIFI_SSID, ip_addr)
    client.sendall(http_response("200 OK", "text/html; charset=utf-8", body))


def print_startup(sta):
    ip_addr = sta.ifconfig()[0]
    print("ESP32-C3 STA Wi-Fi LED + button demo")
    print("Connected Wi-Fi SSID:", WIFI_SSID)
    print("Board IP address:", ip_addr)
    print("GPIO9 button is active-low")
    print("GPIO8 LED output defaults to OFF")
    print("Open this URL from a phone on the same LAN: http://%s/" % ip_addr)
    if hasattr(sys.stdout, "flush"):
        sys.stdout.flush()


def main():
    sta = connect_to_wifi()
    server = open_server()
    ip_addr = sta.ifconfig()[0]
    print_startup(sta)

    last_button_state = None
    last_poll_ms = time.ticks_ms()

    while True:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_poll_ms) >= POLL_INTERVAL_MS:
            pressed = button_pressed()
            if pressed != last_button_state:
                print("GPIO9 button:", "Pressed" if pressed else "Released")
                if hasattr(sys.stdout, "flush"):
                    sys.stdout.flush()
                last_button_state = pressed
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
