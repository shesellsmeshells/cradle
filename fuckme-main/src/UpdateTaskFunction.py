import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST',
    'Access-Control-Allow-Headers': 'Content-Type'
}

def lambda_handler(event, context):
    # 1) Preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    # 2) Parse & validate
    try:
        payload = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'InvalidJSON'})
        }
    owner_id  = payload.get('ownerId')
    task_id   = payload.get('taskId')
    new_status = payload.get('status')

    if not task_id or not new_status or not owner_id:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Missing taskId or status or ownerId'})
        }

    # 3) Perform update
    try:
        resp = table.update_item(
        Key={
            'ownerId': owner_id,
            'taskId':  task_id
        },
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': new_status},
        ReturnValues='UPDATED_NEW'
        )
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'message': 'Status updated successfully',
                'updated': resp.get('Attributes')
            })
        }

    except Exception as e:
        logger.error("Update failed for task %s: %s", task_id, e, exc_info=True)
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'InternalServerError', 'message': str(e)})
        }
