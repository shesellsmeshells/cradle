import json
import os
import logging
import boto3
from boto3.dynamodb.types import TypeDeserializer

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.client("dynamodb")  # one client reused per container
_deser = TypeDeserializer()


def _jsonify_items(raw_items):
    """Convert DynamoDB AttributeValue dicts → plain JSON serializable objects"""
    return [
        {k: _deser.deserialize(v) for k, v in item.items()} for item in raw_items or []
    ]


def lambda_handler(event, context):
    table_name = os.getenv("TABLE_NAME")
    partition_key = os.getenv("PARTITION_KEY", "pk")

    if not table_name:
        logger.error("TABLE_NAME env var not set")
        return _response(500, {"message": "Server misconfiguration: TABLE_NAME missing"})

    # 1. path param → /items/{value}
    pk_value = (
        event.get("pathParameters", {}).get(partition_key)
        or event.get("queryStringParameters", {}).get(partition_key)
    )

    # 2. JSON body
    if pk_value is None and event.get("body"):
        try:
            body = json.loads(event["body"])
            pk_value = body.get(partition_key)
        except (TypeError, ValueError):
            pass

    if pk_value is None:
        return _response(400, {"message": f"Missing required partition key '{partition_key}'"})

    try:
        resp = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression="#pk = :pkval",
            ExpressionAttributeNames={"#pk": partition_key},
            ExpressionAttributeValues={":pkval": {"S": str(pk_value)}},
        )
        items = _jsonify_items(resp.get("Items"))
        return _response(200, items)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("DynamoDB query failed: %s", exc)
        return _response(500, {"message": "Failed to query DynamoDB", "error": str(exc)})


def _response(status_code, body):
    """Helper: format Lambda proxy integration response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }