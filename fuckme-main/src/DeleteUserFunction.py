import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')
USER_POOL_ID = os.environ['USER_POOL_ID']  # e.g. "us-east-1_XXXXXXXXX"

# Single place for your CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST',
    'Access-Control-Allow-Headers': 'Content-Type'
}

def lambda_handler(event, context):
    logger.info("Received event: %s", event)

    # 1) Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }

    # 2) Parse body (proxy vs non‐proxy)
    payload = event.get('body') or event
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return _error(400, 'InvalidJSON', 'Request body is not valid JSON')

    phone = payload.get('phone_number')
    if not phone:
        return _error(400, 'MissingParameter', 'Require phone_number')

    try:
        # Delete the user
        cognito.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=phone
        )
        logger.info("Deleted user %s", phone)

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'message': f'User with phone {phone} successfully deleted.'
            })
        }

    except cognito.exceptions.UserNotFoundException:
        return _error(404, 'UserNotFound', f'No user found with phone {phone}.')
    except Exception as e:
        logger.error("Error deleting user: %s", e, exc_info=True)
        return _error(500, e.__class__.__name__, str(e))


def _error(status, code, message):
    return {
        'statusCode': status,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'error': code,
            'message': message
        })
    }
