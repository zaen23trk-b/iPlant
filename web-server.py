import network
import time
import socket
import json
import _thread
from umqtt.simple import MQTTClient

# ====================================
# WiFi
# ====================================
SSID = 'iPhone'
PASSWORD = 'zaenzidan'

def connect_wifi():
    station = network.WLAN(network.STA_IF)
    station.active(True)
    if not station.isconnected():
        print("Connecting to WiFi...")
        station.connect(SSID, PASSWORD)
        while not station.isconnected():
            print(".", end="")
            time.sleep(0.3)
    print("\nWiFi Connected! IP:", station.ifconfig()[0])
    return station

station = connect_wifi()

# ====================================
# MQTT
# ====================================
MQTT_BROKER = "160.187.144.142"
MQTT_CLIENT_ID = ""
MQTT_TOPIC = "pcr/23trkb/kelompok3/sensor"

# Variabel untuk menyimpan data sensor
last_temp = "-"
last_hum  = "-"
last_soil = "-"

# Lock untuk shared data (WAJIB di multithread)
data_lock = _thread.allocate_lock()

# ====================================
# MQTT Callback
# ====================================
def mqtt_callback(topic, msg):
    global last_temp, last_hum, last_soil
    try:
        data = json.loads(msg.decode())
        with data_lock:
            last_temp = str(data.get("temperature", "-"))
            last_hum  = str(data.get("humidity", "-"))

            soil_data = data.get("soil_pct", {})
            if isinstance(soil_data, dict):
                last_soil = str(soil_data.get("soil_pct", "-"))
            else:
                last_soil = str(soil_data)

        print("MQTT Received:", data)
    except Exception as e:
        print("Failed to parse MQTT message:", e)

def connect_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(MQTT_TOPIC)
    print("MQTT Connected & Subscribed to", MQTT_TOPIC)
    return client

client = connect_mqtt()

# ====================================
# MQTT THREAD
# ====================================
def mqtt_thread():
    global client
    while True:
        try:
            client.check_msg()
        except OSError:
            print("MQTT lost, reconnecting...")
            client = connect_mqtt()
        time.sleep(0.1)

# Jalankan thread MQTT
_thread.start_new_thread(mqtt_thread, ())

# ====================================
# Web Server
# ====================================
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(10)
print("Web Server running at http://", station.ifconfig()[0])

# HTML + CSS + JS
html = """
<!DOCTYPE html>
<html>
<head>
<title>iPlant Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: Arial, sans-serif; background: #1e1e2f; color: #fff; text-align: center; }
h1 { color: #ffcc00; margin-top: 20px; }
.card { background: #2c2c44; border-radius: 15px; padding: 20px; margin: 20px auto; width: 80%; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
.sensor-title { font-size: 1.2em; margin-bottom: 10px; }
.sensor-value { font-size: 2em; color: #00ff99; }
footer { margin-top: 30px; font-size: 0.8em; color: #aaa; }
</style>
<script>
function fetchData() {
    fetch('/data')
    .then(response => response.json())
    .then(data => {
        document.getElementById('temp').innerText = data.temp;
        document.getElementById('hum').innerText = data.hum;
        document.getElementById('soil').innerText = data.soil;
    })
    .catch(err => console.log(err));
}
setInterval(fetchData, 1000);
</script>
</head>
<body>
<h1>iPlant Dashboard</h1>

<div class="card">
    <div class="sensor-title">Temperature(°C)</div>
    <div id="temp" class="sensor-value">-</div>
</div>

<div class="card">
    <div class="sensor-title">Humidity (%)</div>
    <div id="hum" class="sensor-value">-</div>
</div>

<div class="card">
    <div class="sensor-title">Soil Moisture (%)</div>
    <div id="soil" class="sensor-value">-</div>
</div>

<footer>Copyright iPlant</footer>
</body>
</html>
"""

# ====================================
# Main Loop (WEB SERVER)
# ====================================
while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024)
        request = str(request)

        if "GET /data" in request:
            with data_lock:
                response = json.dumps({
                    "temp": last_temp,
                    "hum": last_hum,
                    "soil": last_soil
                })

            conn.send("HTTP/1.1 200 OK\n")
            conn.send("Content-Type: application/json\n")
            conn.send("Connection: close\n\n")
            conn.sendall(response)
        else:
            conn.send("HTTP/1.1 200 OK\n")
            conn.send("Content-Type: text/html\n")
            conn.send("Connection: close\n\n")
            conn.sendall(html)

        conn.close()

    except Exception as e:
        print("Web error:", e)

