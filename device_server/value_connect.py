import paho.mqtt.client as mqtt
import json

# =======================
# Cấu hình MQTT (trùng với ESP32)
# =======================
MQTT_BROKER = "3a28ae8aa3b449dba0a906bd966f1576.s1.eu.hivemq.cloud"
MQTT_PORT = 8883        # Port SSL/TLS
MQTT_USER = "lethien"
MQTT_PASSWORD = "Thien@123"
MQTT_TOPIC = "esp32s3/soil"  # Topic ESP32 publish

# =======================
# Callback khi kết nối broker
# =======================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker!")
        client.subscribe(MQTT_TOPIC)
    else:
        print("Failed to connect, return code:", rc)

# =======================
# Callback khi nhận message
# =======================
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        soil = data.get("soil_moisture", None)
        if soil is not None:
            print(f"Soil Moisture: {soil:.2f} %")
        else:
            print("Invalid data:", payload)
    except Exception as e:
        print("Error parsing message:", e)

# =======================
# Setup MQTT client
# =======================
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set()  # Dùng TLS
client.on_connect = on_connect
client.on_message = on_message

# =======================
# Kết nối và vòng lặp
# =======================
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
