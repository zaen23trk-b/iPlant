import network
import socket
import time
from machine import Pin
import dht

# Pastikan WiFi sudah tersambung
wifi = network.WLAN(network.STA_IF)
while not wifi.isconnected():
    print("Menunggu WiFi...")
    time.sleep(1)

print("ESP32 IP:", wifi.ifconfig()[0])

sensor = dht.DHT11(Pin(32))


def read_sensor():
    try:
        sensor.measure()
        time.sleep_ms(500)
        temp = sensor.temperature()
        hum = sensor.humidity()

        if isinstance(temp, (int, float)) and isinstance(hum, (int, float)):
            return temp, hum
        else:
            return None, None
    except OSError:
        return None, None


def web_page():
    temp, hum = read_sensor()

    html = """<!DOCTYPE HTML>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet"
      href="https://use.fontawesome.com/releases/v5.7.2/css/all.css"
      crossorigin="anonymous">
    <style>
        html {
            font-family: Arial;
            display: inline-block;
            margin: 0 auto;
            text-align: center;
        }
        h2 { font-size: 2.4rem; margin-top: 20px; }
        p { font-size: 2.2rem; }
        .units { font-size: 1.2rem; }
        .dht-labels {
            font-size: 1.4rem;
            vertical-align: middle;
            padding-bottom: 10px;
        }
    </style>
</head>
<body>
    <h2>ESP DHT Web Server</h2>

    <p>
        <i class="fas fa-thermometer-half" style="color:#059e8a;"></i>
        <span class="dht-labels">Temperature</span>
        <span>""" + str(temp) + """</span>
        <sup class="units">&deg;C</sup>
    </p>

    <p>
        <i class="fas fa-tint" style="color:#00add6;"></i>
        <span class="dht-labels">Humidity</span>
        <span>""" + str(hum) + """</span>
        <sup class="units">%</sup>
    </p>

</body>
</html>"""

    return html


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

while True:
  conn, addr = s.accept()
  print('Got a connection from %s' % str(addr))
  request = conn.recv(1024)
  print('Content = %s' % str(request))
  sensor_readings = read_sensor()
  print(sensor_readings)
  response = web_page()
  conn.send('HTTP/1.1 200 OK\n')
  conn.send('Content-Type: text/html\n')
  conn.send('Connection: close\n\n')
  conn.sendall(response)
  conn.close()
