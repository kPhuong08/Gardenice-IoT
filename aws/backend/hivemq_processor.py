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
    
    HiveMQ Webhook sends POST request with:
    {
        "topic": "gardenice/plant_001/sensors",
        "payload": {...sensor data...},
        "timestamp": "2024-11-22T10:30:00.123Z",
        "qos": 1,
        "retain": false
    }
    
    Returns:
        Success/Error response
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract MQTT data
        topic = body.get('topic')
        payload = body.get('payload')
        mqtt_timestamp = body.get('timestamp')
        qos = body.get('qos', 0)
        retain = body.get('retain', False)
        
        # Validate required fields
        if not topic or not payload:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required fields: topic and payload'
                })
            }
        
        print(f"Received MQTT message - Topic: {topic}, Payload size: {len(str(payload))} bytes")
        
        # Generate S3 key based on topic and timestamp
        s3_key = generate_s3_key(topic, mqtt_timestamp)
        
        # Prepare data to store
        data_to_store = {
            'topic': topic,
            'payload': payload,
            'mqtt_timestamp': mqtt_timestamp,
            'received_at': datetime.utcnow().isoformat() + 'Z',
            'qos': qos,
            'retain': retain
        }
        
        # Save to S3
        save_to_s3(s3_key, data_to_store)
        
        print(f"Successfully saved to S3: {s3_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data received and stored successfully',
                's3_key': s3_key,
                'timestamp': data_to_store['received_at']
            })
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Invalid JSON payload',
                'message': str(e)
            })
        }
    except Exception as e:
        print(f"Error processing MQTT message: {str(e)}")
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
        Topic: gardenice/plant_001/sensors
        Timestamp: 2024-11-22T10:30:00.123Z
        S3 Key: raw_data/gardenice/plant_001/sensors/2024-11-22_10-30-00.json
    
    Args:
        topic: MQTT topic string
        timestamp: ISO 8601 timestamp string
        
    Returns:
        S3 key string
    """
    # Sanitize topic (replace / with /)
    # Topic structure: gardenice/plant_001/sensors
    topic_parts = topic.split('/')
    topic_path = '/'.join(topic_parts)
    
    # Parse timestamp
    try:
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.utcnow()
    except:
        dt = datetime.utcnow()
    
    # Format: YYYY-MM-DD_HH-MM-SS
    timestamp_str = dt.strftime('%Y-%m-%d_%H-%M-%S')
    
    # Generate S3 key
    s3_key = f"raw_data/{topic_path}/{timestamp_str}.json"
    
    return s3_key


def save_to_s3(s3_key, data):
    """
    Save data to S3 bucket.
    
    Args:
        s3_key: S3 object key
        data: Dictionary to save as JSON
    """
    try:
        s3_client.put_object(
            Bucket=PLANT_DATA_BUCKET,
            Key=s3_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json',
            Metadata={
                'source': 'hivemq-webhook',
                'processed_at': datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        print(f"Error saving to S3: {str(e)}")
        raise


def get_latest_sensor_data(plant_id='plant_001'):
    """
    Get latest sensor data from S3 raw_data folder.
    This function can be called by get_plant_data Lambda.
    
    Args:
        plant_id: Plant identifier
        
    Returns:
        Dictionary with latest sensor readings or None
    """
    try:
        prefix = f"raw_data/gardenice/{plant_id}/sensors/"
        
        response = s3_client.list_objects_v2(
            Bucket=PLANT_DATA_BUCKET,
            Prefix=prefix,
            MaxKeys=10
        )
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            return None
        
        # Get latest file
        latest_file = sorted(
            response['Contents'],
            key=lambda x: x['LastModified'],
            reverse=True
        )[0]
        
        # Read file content
        obj = s3_client.get_object(
            Bucket=PLANT_DATA_BUCKET,
            Key=latest_file['Key']
        )
        
        data = json.loads(obj['Body'].read().decode('utf-8'))
        
        # Extract sensor values from payload
        payload = data.get('payload', {})
        
        return {
            'humidity': payload.get('humidity'),
            'temperature': payload.get('temperature'),
            'soil_moisture': payload.get('soil_moisture'),
            'light_level': payload.get('light_level'),
            'timestamp': data.get('mqtt_timestamp') or data.get('received_at'),
            'device_id': payload.get('device_id')
        }
        
    except Exception as e:
        print(f"Error reading sensor data from S3: {str(e)}")
        return None
