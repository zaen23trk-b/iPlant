"""
MicroPython IoT Weather Station Example (DHT11 Version)
"""

import network
import time
from machine import Pin
import dht
import ujson
from umqtt.simple import MQTTClient

# MQTT Server Parameters
MQTT_CLIENT_ID = "mqtt_weather"
MQTT_BROKER    = "160.187.144.142"
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC     = "iPlant/sensors/dht11"

# --- Inisialisasi DHT11 di pin 32 ---
sensor = dht.DHT11(Pin(32))

print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Hmz', '123qweasdzxc')

while not sta_if.isconnected():
    print(".", end="")
    time.sleep(0.2)

print(" Connected!")

print("Connecting to MQTT server... ", end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, user=MQTT_USER, password=MQTT_PASSWORD)
client.connect()
print("Connected!")

while True:
    try:
        print("Measuring DHT11 sensor...")
        sensor.measure()
        temp = sensor.temperature()   # °C
        hum  = sensor.humidity()      # %

        print("Temperature:", temp, "°C")
        print("Humidity:", hum, "%")

        message = ujson.dumps({
            "temperature": temp,
            "humidity": hum
        })

        client.publish(MQTT_TOPIC, message)
        print("Published:", message)

    except OSError:
        print("Failed to read DHT11 sensor!")

    time.sleep(2)
