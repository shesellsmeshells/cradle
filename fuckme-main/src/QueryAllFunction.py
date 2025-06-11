import json
import os
import logging
import boto3
from boto3.dynamodb.types import TypeDeserializer

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.client("dynamodb")
_deser = TypeDeserializer()


def _jsonify_items(raw_items):
    """Convert DynamoDB AttributeValue dicts → plain JSON serializable objects"""
    return [
        {k: _deser.deserialize(v) for k, v in item.items()} for item in raw_items or []
    ]


def lambda_handler(event, context):
    table_name = os.getenv("TABLE_NAME")
    if not table_name:
        logger.error("TABLE_NAME env var not set")
        return _response(500, {"message": "Server misconfiguration: TABLE_NAME missing"})

    try:
        items = []
        kwargs = {"TableName": table_name}
        # loop to handle pagination
        while True:
            resp = dynamodb.scan(**kwargs)
            items.extend(_jsonify_items(resp.get("Items")))
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
            # set ExclusiveStartKey for next page
            kwargs["ExclusiveStartKey"] = last_key

        return _response(200, items)

    except Exception as exc:
        logger.exception("DynamoDB scan failed: %s", exc)
        return _response(500, {"message": "Failed to scan DynamoDB", "error": str(exc)})


def _response(status_code, body):
    """Helper: format Lambda proxy integration response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }