#!/usr/bin/env python3
"""
MQTT Bridge for Gardenice IoT - DIRECT S3 STORAGE
Subscribes to HiveMQ Cloud and saves data directly to AWS S3
"""

import paho.mqtt.client as mqtt
import boto3
import requests
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import os

# =======================
# SETUP LOGGING
# =======================
LOG_DIR = os.path.expanduser("~/mqtt-bridge/logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "mqtt-bridge.log")

handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)

logger = logging.getLogger('mqtt-bridge')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# =======================
# AWS S3 & LAMBDA CONFIGURATION
# =======================
S3_BUCKET = "iot-gardernice"  # ← THAY ĐỔI tên bucket của bạn
S3_REGION = "us-east-1"

# AWS Lambda Webhook Configuration (cũ)
AWS_WEBHOOK_URL = "https://5gbq1zfci7.execute-api.us-east-1.amazonaws.com/prod/mqtt-ingest"
AWS_API_KEY = "81kxQXgMvtaXVFFqyT56f8jIcuTu7uPa3UnwEzks"

s3_client = boto3.client('s3', region_name=S3_REGION)

# =======================
# HiveMQ Cloud Configuration
# =======================
MQTT_BROKER = "3a28ae8aa3b449dba0a906bd966f1576.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "lethien"
MQTT_PASSWORD = "Thien@123"
MQTT_TOPIC = "esp32s3/soil"

# =======================
# CALLBACKS
# =======================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("✓ Connected to HiveMQ Cloud successfully")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"✓ Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"✗ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"Message received on topic: {msg.topic}")
        logger.info(f"{'='*80}")
        
        # Parse payload
        payload = json.loads(msg.payload.decode())
        logger.info(f"RAW PAYLOAD FROM ESP32:")
        logger.info(json.dumps(payload, indent=2))
        logger.info(f"Payload keys: {list(payload.keys())}")
        
        # ============================================
        # CLEAN & VALIDATE DATA
        # ============================================
        cleaned_payload = {}
        
        # soil_moisture (float, 0-100)
        soil_moisture = payload.get('soil_moisture')
        if soil_moisture is not None:
            try:
                soil_moisture = float(soil_moisture)
                if 0 <= soil_moisture <= 100:
                    cleaned_payload['soil_moisture'] = soil_moisture
                else:
                    logger.warning(f"⚠️  soil_moisture out of range: {soil_moisture}")
            except (ValueError, TypeError):
                logger.warning(f"⚠️  Invalid soil_moisture: {soil_moisture}")
        
        # rain (convert string to int: "0" -> 0)
        rain = payload.get('rain')
        if rain is not None:
            try:
                # If string, convert to int
                rain = int(str(rain))
                cleaned_payload['rain'] = rain  # 0 = rain, 1 = dry
            except (ValueError, TypeError):
                logger.warning(f"⚠️  Invalid rain: {rain}")
        
        # temperature (float, typically -40 to 125)
        temperature = payload.get('temperature')
        if temperature is not None:
            try:
                temperature = float(temperature)
                if -40 <= temperature <= 125:
                    cleaned_payload['temperature'] = temperature
                else:
                    logger.warning(f"⚠️  temperature out of range: {temperature}")
            except (ValueError, TypeError):
                logger.warning(f"⚠️  Invalid temperature: {temperature}")
        
        # humidity (float, 0-100)
        humidity = payload.get('humidity')
        if humidity is not None:
            try:
                humidity = float(humidity)
                if 0 <= humidity <= 100:
                    cleaned_payload['humidity'] = humidity
                else:
                    logger.warning(f"⚠️  humidity out of range: {humidity}")
            except (ValueError, TypeError):
                logger.warning(f"⚠️  Invalid humidity: {humidity}")
        
        # light_level (float, >= 0)
        light_level = payload.get('light_level')
        if light_level is not None:
            try:
                light_level = float(light_level)
                if light_level >= 0:
                    cleaned_payload['light_level'] = light_level
                else:
                    logger.warning(f"⚠️  light_level negative: {light_level}, skipping")
            except (ValueError, TypeError):
                logger.warning(f"⚠️  Invalid light_level: {light_level}")
        
        logger.info(f"✓ CLEANED PAYLOAD:")
        logger.info(json.dumps(cleaned_payload, indent=2))
        
        if not cleaned_payload:
            logger.error("✗ No valid data to store!")
            return
        
        # ============================================
        # SAVE TO S3
        # ============================================
        now = datetime.utcnow()
        timestamp_str = now.strftime('%Y-%m-%d_%H-%M-%S')
        
        # S3 key: raw_data/esp32s3/soil/2024-11-25_13-36-42.json
        s3_key = f"raw_data/{msg.topic}/{timestamp_str}.json"
        
        # Data to store
        data_to_store = {
            'topic': msg.topic,
            'payload': cleaned_payload,
            'mqtt_timestamp': datetime.utcnow().isoformat() + 'Z',
            'qos': msg.qos,
            'retain': msg.retain,
            'device_id': 'esp32s3-cam'
        }
        
        logger.info(f"💾 DATA TO BE STORED IN S3:")
        logger.info(json.dumps(data_to_store, indent=2))
        
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(data_to_store, indent=2),
                ContentType='application/json',
                Metadata={
                    'source': 'mqtt-bridge-ec2',
                    'topic': msg.topic,
                    'processed_at': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"✓ Successfully saved to S3")
            logger.info(f"  S3 Bucket: {S3_BUCKET}")
            logger.info(f"  S3 Key: {s3_key}")
            logger.info(f"  Object size: {len(json.dumps(data_to_store))} bytes")
            
        except Exception as e:
            logger.error(f"✗ Error saving to S3: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        # ============================================
        # SEND TO LAMBDA WEBHOOK (CŨ)
        # ============================================
        try:
            webhook_data = {
                "topic": msg.topic,
                "payload": cleaned_payload,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "qos": msg.qos,
                "retain": msg.retain
            }
            
            headers = {
                "x-api-key": AWS_API_KEY,
                "Content-Type": "application/json"
            }
            
            logger.info(f"🌐 Sending to Lambda: {AWS_WEBHOOK_URL}")
            response = requests.post(
                AWS_WEBHOOK_URL,
                json=webhook_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✓ Data sent to Lambda successfully")
                logger.info(f"  Response: {response.json().get('s3_key')}")
            else:
                logger.error(f"✗ Lambda request failed: {response.status_code}")
                logger.error(f"  Response: {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"✗ Error sending to Lambda: {str(e)}")
        
        logger.info(f"{'='*80}\n")
            
    except json.JSONDecodeError as e:
        logger.error(f"✗ JSON decode error: {e}")
        logger.error(f"Raw payload: {msg.payload}")
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warning(f"✗ Unexpected disconnection. Reconnecting...")

# =======================
# MAIN
# =======================
def main():
    logger.info("=" * 80)
    logger.info("Gardenice IoT - MQTT Bridge (S3 STORAGE)")
    logger.info("=" * 80)
    logger.info(f"MQTT Broker: {MQTT_BROKER}")
    logger.info(f"MQTT Topic: {MQTT_TOPIC}")
    logger.info(f"S3 Bucket: {S3_BUCKET}")
    logger.info(f"S3 Region: {S3_REGION}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 80)
    logger.info("")
    
    # Create MQTT client
    client = mqtt.Client(client_id="ec2-mqtt-bridge")
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set()
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    logger.info("Connecting to HiveMQ Cloud...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info("Starting MQTT loop...\n")
        client.loop_forever()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        client.disconnect()
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()