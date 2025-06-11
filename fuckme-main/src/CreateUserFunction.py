import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')
USER_POOL_ID = os.environ['USER_POOL_ID']           # e.g. "us-east-1_XXXXXXXXX"

def lambda_handler(event, context):
    logger.info("Raw event: %s", event)

    # parse proxy vs non-proxy
    payload = event.get('body') or event
    if isinstance(payload, str):
        payload = json.loads(payload)

    phone      = payload.get('phone_number')
    password   = payload.get('password')
    first_name = payload.get('first_name')
    last_name  = payload.get('last_name')

    if not all([phone, password, first_name, last_name]):
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'MissingParameter',
                'message': 'Require phone_number, password, first_name, last_name'
            })
        }

    try:
        # 1) Create & auto-confirm the user
        create_resp = cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=phone,
            UserAttributes=[
                {'Name': 'phone_number',          'Value': phone},
                {'Name': 'phone_number_verified', 'Value': 'true'},
                {'Name': 'given_name',            'Value': first_name},
                {'Name': 'family_name',           'Value': last_name},
            ],
            MessageAction='SUPPRESS'   # no welcome SMS/email
        )
        logger.info("admin_create_user response: %s", create_resp)

        # 2) Set the provided password as a *temporary* password
        #    so that the user must change it on first sign-in.
        pwd_resp = cognito.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=phone,
            Password=password,
            Permanent=False       # NOT permanent → forces CHANGE_PASSWORD challenge
        )
        logger.info("admin_set_user_password response: %s", pwd_resp)

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'User created and must reset password on first login.',
                'username': phone
            })
        }

    except cognito.exceptions.UsernameExistsException:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'UserAlreadyExists',
                'message': f'A user with phone {phone} already exists.'
            })
        }

    except Exception as e:
        logger.error("Error in creating user: %s", e, exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': e.__class__.__name__,
                'message': str(e)
            })
        }
