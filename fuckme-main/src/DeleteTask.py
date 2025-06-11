import boto3
import os
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,DELETE',
    'Access-Control-Allow-Headers': 'Content-Type'
}

def lambda_handler(event, context):
    # Preflight
    if event.get('httpMethod') == 'OPTIONS':
        return { 'statusCode': 200, 'headers': CORS_HEADERS, 'body': '' }

    # Parse body for both keys
    try:
        payload = json.loads(event.get('body') or '{}')
        owner_id = payload['ownerId']
        task_id  = payload['taskId']
    except (KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Missing userId or taskId'})
        }

    # Build key map matching your schema
    key = {
        'ownerId': owner_id,
        'taskId': task_id
    }

    try:
        table.delete_item(Key=key)
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'message': 'Task deleted successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': str(e)})
        }