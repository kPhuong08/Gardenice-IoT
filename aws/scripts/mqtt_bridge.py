#!/usr/bin/env python3
"""
MQTT Bridge for Gardenice IoT
Subscribes to HiveMQ Cloud and forwards data to AWS Lambda
"""

import paho.mqtt.client as mqtt
import requests
import json
import time
from datetime import datetime

# HiveMQ Cloud Configuration
MQTT_BROKER = "3a28ae8aa3b449dba0a906bd966f1576.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "lethien"
MQTT_PASSWORD = "Thien@123"
MQTT_TOPIC = "esp32s3/soil"

# AWS Lambda Webhook Configuration
AWS_WEBHOOK_URL = "https://5gbq1zfci7.execute-api.us-east-1.amazonaws.com/prod/mqtt-ingest"
AWS_API_KEY = "81kxQXgMvtaXVFFqyT56f8jIcuTu7uPa3UnwEzks"

# Callback when connected to MQTT broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[{datetime.now()}] Connected to HiveMQ Cloud successfully")
        client.subscribe(MQTT_TOPIC)
        print(f"[{datetime.now()}] Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"[{datetime.now()}] Connection failed with code {rc}")

# Callback when message received
def on_message(client, userdata, msg):
    try:
        print(f"\n[{datetime.now()}] Message received on topic: {msg.topic}")
        
        # Parse payload
        payload = json.loads(msg.payload.decode())
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Prepare data for AWS Lambda
        webhook_data = {
            "topic": msg.topic,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "qos": msg.qos,
            "retain": msg.retain
        }
        
        # Send to AWS Lambda
        headers = {
            "x-api-key": AWS_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            AWS_WEBHOOK_URL,
            json=webhook_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[{datetime.now()}] ✓ Data forwarded to AWS successfully")
            print(f"Response: {response.json()}")
        else:
            print(f"[{datetime.now()}] ✗ AWS request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except json.JSONDecodeError as e:
        print(f"[{datetime.now()}] ✗ JSON decode error: {e}")
    except requests.RequestException as e:
        print(f"[{datetime.now()}] ✗ Request error: {e}")
    except Exception as e:
        print(f"[{datetime.now()}] ✗ Error: {e}")

# Callback when disconnected
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[{datetime.now()}] Unexpected disconnection. Reconnecting...")

# Main function
def main():
    print("=" * 60)
    print("Gardenice IoT - MQTT Bridge")
    print("=" * 60)
    print(f"MQTT Broker: {MQTT_BROKER}")
    print(f"MQTT Topic: {MQTT_TOPIC}")
    print(f"AWS Endpoint: {AWS_WEBHOOK_URL}")
    print("=" * 60)
    print()
    
    # Create MQTT client
    client = mqtt.Client(client_id="ec2-mqtt-bridge")
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set()  # Enable TLS for port 8883
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Connect to broker
    print(f"[{datetime.now()}] Connecting to HiveMQ Cloud...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start loop
        print(f"[{datetime.now()}] Starting MQTT loop...")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Shutting down...")
        client.disconnect()
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")

if __name__ == "__main__":
    main()
