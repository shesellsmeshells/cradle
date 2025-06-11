# list_users_lambda.py
import os
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')
USER_POOL_ID = os.environ['USER_POOL_ID']

def lambda_handler(event, context):
    try:
        users = []
        response = cognito.list_users(UserPoolId=USER_POOL_ID)
        for user in response['Users']:
            user_data = {
                'username': user['Username'],
                'attributes': {attr['Name']: attr['Value'] for attr in user.get('Attributes', [])}
            }
            # Fetch groups for each user
            groups_resp = cognito.admin_list_groups_for_user(
                UserPoolId=USER_POOL_ID,
                Username=user['Username']
            )
            user_data['groups'] = [g['GroupName'] for g in groups_resp.get('Groups', [])]
            users.append(user_data)

        return {
            'statusCode': 200,
            'body': json.dumps(users)
        }
    except Exception as e:
        logger.error("Error listing users: %s", e, exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
