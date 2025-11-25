import json
import os
import boto3
# import urllib3  # Commented out - not needed when EC2 service is disabled
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')
# http = urllib3.PoolManager()  # Commented out - not needed when EC2 service is disabled

# Environment variables
PLANT_DATA_BUCKET = os.environ.get('PLANT_DATA_BUCKET')
# EC2_SERVICE_URL = os.environ.get('EC2_SERVICE_URL')  # Commented out - not needed yet


def lambda_handler(event, context):
    """
    Lambda handler to fetch plant data from S3.
    Currently returns: AI evaluation + image URL
    
    Returns:
        JSON with AI evaluation and pre-signed image URL from S3
    """
    try:
        # Extract plant_id from path parameters
        plant_id = event.get('pathParameters', {}).get('plant_id')
        
        if not plant_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'plant_id is required'})
            }
        
        # Get AI evaluation from S3
        ai_evaluation = get_latest_result_from_s3()
        
        # Get latest image from S3 and generate pre-signed URL
        image_url = get_latest_image_url(plant_id)
        
        # Get latest sensor data from MQTT/S3
        sensor_data = get_latest_sensor_data(plant_id)
        
        # Combine data
        response_data = {
            'plant_id': plant_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metrics': {
                'ai_evaluation': ai_evaluation,
                'soil_moisture': sensor_data.get('soil_moisture') if sensor_data else None,
                'rain': sensor_data.get('rain') if sensor_data else None,
                'light': sensor_data.get('light_level') if sensor_data else None
            },
            'image_url': image_url
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }


def get_latest_result_from_s3():
    """
    Get latest AI result from S3 results folder.
    Cấu trúc: s3://iot-gardernice/results/*.txt
    
    Returns:
        String: 'Plant is healthy' hoặc 'Plant is unhealthy' hoặc 'Unknown'
    """
    try:
        data_prefix = os.environ.get('DATA_PATH_PREFIX', '')
        prefix = f"{data_prefix}results/" if data_prefix else "results/"
        
        response = s3_client.list_objects_v2(
            Bucket=PLANT_DATA_BUCKET,
            Prefix=prefix,
            MaxKeys=100
        )
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            return 'Unknown'
        
        # Get latest result file
        results = sorted(
            response['Contents'],
            key=lambda x: x['LastModified'],
            reverse=True
        )
        latest_result_key = results[0]['Key']
        
        # Read result file
        obj = s3_client.get_object(Bucket=PLANT_DATA_BUCKET, Key=latest_result_key)
        result_text = obj['Body'].read().decode('utf-8').strip().lower()
        
        # Parse result
        if 'healthy' in result_text and 'unhealthy' not in result_text:
            return 'Plant is healthy'
        elif 'unhealthy' in result_text:
            return 'Plant is unhealthy'
        else:
            return result_text.capitalize()
            
    except Exception as e:
        print(f"Error reading result from S3: {str(e)}")
        return 'Unknown'


def get_latest_image_url(plant_id):
    """
    Get the latest plant image from S3 and generate a pre-signed URL.
    
    Args:
        plant_id: Unique identifier for the plant
        
    Returns:
        Pre-signed URL for the latest image (valid for 1 hour)
    """
    try:
        # Get data path prefix from environment
        data_prefix = os.environ.get('DATA_PATH_PREFIX', '')
        
        # List objects in the plant's image folder
        prefix = f"{data_prefix}images/" if data_prefix else "images/"
        response = s3_client.list_objects_v2(
            Bucket=PLANT_DATA_BUCKET,
            Prefix=prefix,
            MaxKeys=100
        )
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            return None
        
        # Sort by last modified and get the latest image
        images = sorted(
            response['Contents'],
            key=lambda x: x['LastModified'],
            reverse=True
        )
        latest_image_key = images[0]['Key']
        
        # Generate pre-signed URL (valid for 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': PLANT_DATA_BUCKET,
                'Key': latest_image_key
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return presigned_url
        
    except Exception as e:
        print(f"Error generating image URL: {str(e)}")
        return None


def get_cors_headers():
    """Return CORS headers for API responses."""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }


# TODO: Uncomment when EC2 service with sensors is ready
# def fetch_ec2_metrics(plant_id):
#     """Fetch real-time sensor data from EC2 service"""
#     try:
#         url = f"{EC2_SERVICE_URL}/api/plants/{plant_id}/metrics"
#         response = http.request('GET', url, timeout=5.0)
#         
#         if response.status == 200:
#             data = json.loads(response.data.decode('utf-8'))
#             return {
#                 'humidity': data.get('humidity'),
#                 'temperature': data.get('temperature'),
#                 'soil_moisture': data.get('soil_moisture'),
#                 'light_level': data.get('light_level'),
#                 'health_score': data.get('health_score'),
#                 'ai_evaluation': data.get('ai_evaluation', 'Unknown')
#             }
#     except Exception as e:
#         print(f"Error fetching EC2 metrics: {str(e)}")
#         return None


def get_latest_sensor_data(plant_id='plant_001'):
    """
    Get latest sensor data from S3 raw_data folder (from MQTT/HiveMQ).
    
    Args:
        plant_id: Plant identifier
        
    Returns:
        Dictionary with latest sensor readings or None
    """
    try:
        # Look for sensor data in raw_data folder
        # Path: raw_data/{MQTT_TOPIC}/YYYY-MM-DD_HH-MM-SS.json
        # Default topic: esp32s3/soil
        mqtt_topic = os.environ.get('MQTT_TOPIC', 'esp32s3/soil')
        prefix = f"raw_data/{mqtt_topic}/"
        
        response = s3_client.list_objects_v2(
            Bucket=PLANT_DATA_BUCKET,
            Prefix=prefix,
            MaxKeys=10
        )
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            print(f"No sensor data found in S3 at {prefix}")
            return None
        
        # Get latest file
        latest_file = sorted(
            response['Contents'],
            key=lambda x: x['LastModified'],
            reverse=True
        )[0]
        
        print(f"Reading sensor data from: {latest_file['Key']}")
        
        # Read file content
        obj = s3_client.get_object(
            Bucket=PLANT_DATA_BUCKET,
            Key=latest_file['Key']
        )
        
        data = json.loads(obj['Body'].read().decode('utf-8'))
        
        # Extract sensor values from payload
        payload = data.get('payload', {})
        
        sensor_data = {
            'soil_moisture': payload.get('soil_moisture'),
            'rain': payload.get('rain'),  # Boolean: True if raining, False if dry
            'light_level': payload.get('light_level'),
            'timestamp': data.get('mqtt_timestamp') or data.get('received_at'),
            'device_id': payload.get('device_id')
        }
        
        print(f"Sensor data retrieved: {sensor_data}")
        return sensor_data
        
    except Exception as e:
        print(f"Error reading sensor data from S3: {str(e)}")
        return None
