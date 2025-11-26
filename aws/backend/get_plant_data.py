import json
import os
import boto3
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')

# Environment variables
PLANT_DATA_BUCKET = os.environ.get('PLANT_DATA_BUCKET')


def lambda_handler(event, context):
    """
    Lambda handler to fetch plant data from S3.
    """
    try:
        print("Event received:", json.dumps(event))  # Debug log

        # Extract plant_id from path parameters
        plant_id = event.get('pathParameters', {}).get('plant_id')
        
        if not plant_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'plant_id is required'})
            }
        
        # 1. Get AI evaluation from S3
        ai_evaluation = get_latest_result_from_s3()
        
        # 2. Get latest image from S3
        image_url = get_latest_image_url(plant_id)
        
        # 3. Get latest sensor data
        sensor_data = get_latest_sensor_data()

        # Combine data
        response_data = {
            'plant_id': plant_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metrics': {
                'ai_evaluation': ai_evaluation,
                'soil_moisture': sensor_data.get('soil_moisture') if sensor_data else None,
                'rain': sensor_data.get('rain') if sensor_data else None,
                'temperature': sensor_data.get('temperature') if sensor_data else None,
                'humidity': sensor_data.get('humidity') if sensor_data else None,
                # 'light': sensor_data.get('light_level') if sensor_data else None
            },
            'image_url': image_url
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }


def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Cache-Control,Pragma,Expires',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
        'Pragma': 'no-cache'
    }


def get_latest_result_from_s3():
    try:
        data_prefix = os.environ.get('DATA_PATH_PREFIX', '')
        prefix = f"{data_prefix}results/" if data_prefix else "results/"
        
        response = s3_client.list_objects_v2(Bucket=PLANT_DATA_BUCKET, Prefix=prefix, MaxKeys=1000)
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            return 'Unknown'
        
        latest_file = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]
        
        obj = s3_client.get_object(Bucket=PLANT_DATA_BUCKET, Key=latest_file['Key'])
        result_text = obj['Body'].read().decode('utf-8').strip().lower()
        
        if 'bacterial' in result_text:
            return 'Plant is bacterial'
        elif 'fungal' in result_text:
            return 'Plant is fungal'
        elif 'healthy' in result_text:
            return 'Plant is healthy'
        else:
            return result_text.capitalize()
    except:
        return 'Unknown'


def get_latest_image_url(plant_id):
    try:
        data_prefix = os.environ.get('DATA_PATH_PREFIX', '')
        prefix = f"{data_prefix}images/" if data_prefix else "images/"
        
        response = s3_client.list_objects_v2(Bucket=PLANT_DATA_BUCKET, Prefix=prefix, MaxKeys=1000)
        
        if 'Contents' not in response:
            return None
        
        valid_images = [obj for obj in response['Contents'] if obj['Key'].lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not valid_images:
            return None

        latest_file = sorted(valid_images, key=lambda x: x['LastModified'], reverse=True)[0]
        
        return s3_client.generate_presigned_url('get_object', Params={'Bucket': PLANT_DATA_BUCKET, 'Key': latest_file['Key']}, ExpiresIn=3600)
    except:
        return None


def get_latest_sensor_data():
    """
    ĐÃ IMPORT từ file thứ nhất – giữ nguyên format raw_data/esp32s3/soil/yyyy...
    """
    try:
        mqtt_topic = os.environ.get('MQTT_TOPIC', 'esp32s3/sensors')
        prefix = f"raw_data/{mqtt_topic}/"

        response = s3_client.list_objects_v2(Bucket=PLANT_DATA_BUCKET, Prefix=prefix, MaxKeys=1000)

        if 'Contents' not in response:
            return None
        
        latest_file = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]
        
        obj = s3_client.get_object(Bucket=PLANT_DATA_BUCKET, Key=latest_file['Key'])
        data = json.loads(obj['Body'].read().decode('utf-8'))
        payload = data.get('payload', {})

        return {
            'humidity': payload.get('humidity'),
            'temperature': payload.get('temperature'),
            'soil_moisture': payload.get('soil_moisture'),
            'rain': payload.get('rain'),
            'timestamp': data.get('mqtt_timestamp') or data.get('received_at'),
            'device_id': payload.get('device_id')
        }
    except:
        return None
