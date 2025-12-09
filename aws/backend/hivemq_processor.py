import json
import os
import boto3
from datetime import datetime
import re

# Initialize AWS clients
s3_client = boto3.client('s3')

# Environment variables
PLANT_DATA_BUCKET = os.environ.get('PLANT_DATA_BUCKET')


def lambda_handler(event, context):
    """
    Lambda handler to process HiveMQ webhook and persist to S3.
    DEBUG VERSION - Log mọi thứ để track dữ liệu
    """
    try:
        print("=" * 80)
        print(f"[Lambda Start] Timestamp: {datetime.utcnow().isoformat()}")
        print("=" * 80)
        
        # Log raw event
        print("\n RAW EVENT RECEIVED:")
        print(json.dumps(event, indent=2, default=str))
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        print("\n PARSED BODY:")
        print(json.dumps(body, indent=2))
        
        # Extract MQTT data
        topic = body.get('topic')
        payload = body.get('payload')
        mqtt_timestamp = body.get('timestamp')
        qos = body.get('qos', 0)
        retain = body.get('retain', False)
        
        print(f"\n EXTRACTED FIELDS:")
        print(f"  - topic: {topic}")
        print(f"  - payload: {json.dumps(payload, indent=2)}")
        print(f"  - mqtt_timestamp: {mqtt_timestamp}")
        print(f"  - qos: {qos}")
        print(f"  - retain: {retain}")
        
        # Validate required fields
        if not topic or not payload:
            print(f"\n VALIDATION ERROR: Missing topic or payload")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required fields: topic and payload'
                })
            }
        
        print(f"\n✓ Validation passed")
        print(f"  - Topic: {topic}")
        print(f"  - Payload keys: {list(payload.keys())}")
        print(f"  - Payload size: {len(str(payload))} bytes")
        
        # Generate S3 key based on topic and timestamp
        s3_key = generate_s3_key(topic, mqtt_timestamp)
        print(f"  - Generated S3 key: {s3_key}")
        
        # Prepare data to store
        data_to_store = {
            'topic': topic,
            'payload': payload,
            'mqtt_timestamp': mqtt_timestamp,
            'received_at': datetime.utcnow().isoformat() + 'Z',
            'qos': qos,
            'retain': retain
        }
        
        print(f"\nDATA TO BE STORED IN S3:")
        print(json.dumps(data_to_store, indent=2))
        
        # Save to S3
        save_to_s3(s3_key, data_to_store)
        
        print(f"\n✓ Successfully saved to S3: {s3_key}")
        print(f"  - S3 Bucket: {PLANT_DATA_BUCKET}")
        print(f"  - Object size: {len(json.dumps(data_to_store))} bytes")
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data received and stored successfully',
                's3_key': s3_key,
                'timestamp': data_to_store['received_at'],
                'payload_keys': list(payload.keys())
            })
        }
        
        print(f"\nRESPONSE TO CLIENT:")
        print(json.dumps(response, indent=2))
        print("=" * 80 + "\n")
        
        return response
        
    except json.JSONDecodeError as e:
        print(f"\nJSON decode error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Invalid JSON payload',
                'message': str(e)
            })
        }
    except Exception as e:
        print(f"\nError processing MQTT message: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def generate_s3_key(topic, timestamp):
    """
    Generate S3 key from MQTT topic and timestamp.
    
    Example:
        Topic: esp32s3/sensors
        Timestamp: 2024-11-22T10:30:00.123Z
        S3 Key: raw_data/esp32s3/sensors/2024-11-22_10-30-00.json
    """
    topic_path = topic.replace('/', '/')
    
    try:
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.utcnow()
    except:
        dt = datetime.utcnow()
    
    timestamp_str = dt.strftime('%Y-%m-%d_%H-%M-%S')
    s3_key = f"raw_data/{topic_path}/{timestamp_str}.json"
    
    return s3_key


def save_to_s3(s3_key, data):
    """
    Save data to S3 bucket.
    """
    try:
        print(f"\n[S3 Save] Saving to: s3://{PLANT_DATA_BUCKET}/{s3_key}")
        
        body_json = json.dumps(data, indent=2)
        print(f"[S3 Save] Body size: {len(body_json)} bytes")
        
        s3_client.put_object(
            Bucket=PLANT_DATA_BUCKET,
            Key=s3_key,
            Body=body_json,
            ContentType='application/json',
            Metadata={
                'source': 'hivemq-webhook',
                'processed_at': datetime.utcnow().isoformat()
            }
        )
        
        print(f"[S3 Save] Object created successfully")
        
    except Exception as e:
        print(f"[S3 Save] Error saving to S3: {str(e)}")
        raise