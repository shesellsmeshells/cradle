import boto3
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import os
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

DAILY_ACRE_LIMIT = 4
DEFAULT_RATE = Decimal('145')  # Default rate per acre

def get_start_date_for_range(service_range):
    today = datetime.utcnow().date()
    if service_range == 'this_week':
        return today
    elif service_range == 'next_week':
        return today + timedelta(days=(7 - today.weekday()))
    elif service_range == 'in_2_weeks':
        return today + timedelta(days=(14 - today.weekday()))
    else:
        raise ValueError('Invalid serviceDateRange')

def find_schedule_dates(start_date, total_acres):
    schedule = []
    remaining_acres = float(total_acres)

    day_offset = 0
    while remaining_acres > 0:
        current_date = start_date + timedelta(days=day_offset)

        # Skip weekends
        if current_date.weekday() >= 5:
            day_offset += 1
            continue

        iso_date = current_date.isoformat()

        response = table.scan(
            FilterExpression="specificDate = :d",
            ExpressionAttributeValues={":d": iso_date}
        )
        existing_acres = sum(float(item['acres']) for item in response['Items'])

        available_capacity = DAILY_ACRE_LIMIT - existing_acres

        if available_capacity > 0:
            assigned_acres = min(available_capacity, remaining_acres)
            schedule.append((iso_date, Decimal(str(assigned_acres))))
            remaining_acres -= assigned_acres

        day_offset += 1

        if day_offset > 30:
            raise Exception("Could not find enough capacity within 30 days.")

    return schedule

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])

        total_acres = Decimal(str(body['acres']))
        rate = Decimal(str(body.get('rate', DEFAULT_RATE)))

        # Use specificDate only if it's provided and no serviceDateRange is selected
        if 'specificDate' in body and body['specificDate'] and not body.get('serviceDateRange'):
            task = {
                'ownerId': body['ownerId'],
                'taskId': str(uuid.uuid4()),
                'farmer': body['farmer'],
                'acres': total_acres,
                'rate': rate,
                'estimate': total_acres * rate,
                'serviceDateRange': None,
                'specificDate': body['specificDate'],
                'status': body.get('status', 'pending'),
                'cooperative': body['cooperative'],
                'sector': body['sector'],
                'notes': body.get('notes'),
                'dateCreated': datetime.utcnow().isoformat()
            }
            table.put_item(Item=task)

            return {
                'statusCode': 201,
                'body': json.dumps({
                    'message': 'Task created with specific date',
                    'taskId': task['taskId'],
                    'assignedDate': task['specificDate']
                })
            }

        # Otherwise, auto-assign based on serviceDateRange
        start_date = get_start_date_for_range(body['serviceDateRange'])
        scheduled_chunks = find_schedule_dates(start_date, total_acres)
        task_ids = []

        for date_str, chunk_acres in scheduled_chunks:
            task = {
                'ownerId': body['ownerId'],
                'taskId': str(uuid.uuid4()),
                'farmer': body['farmer'],
                'acres': chunk_acres,
                'rate': rate,
                'estimate': chunk_acres * rate,
                'serviceDateRange': body['serviceDateRange'],
                'specificDate': date_str,
                'status': body.get('status', 'pending'),
                'cooperative': body['cooperative'],
                'sector': body['sector'],
                'notes': body.get('notes'),
                'dateCreated': datetime.utcnow().isoformat()
            }
            table.put_item(Item=task)
            task_ids.append({
                'taskId': task['taskId'],
                'assignedDate': date_str,
                'acres': str(chunk_acres)
            })

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Task created in chunks',
                'tasks': task_ids
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
